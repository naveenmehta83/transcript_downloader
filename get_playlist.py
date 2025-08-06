# YouTube Playlist URL Extractor with External Configuration
import requests
import json
import os

# Configuration management functions
def load_config_from_file(config_file='config.txt'):
    """
    Load playlist URL and API key from external config file
    
    Config file format:
    PLAYLIST_URL=https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID
    API_KEY=your_api_key_here
    """
    config = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '=' in line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
        return config
    except FileNotFoundError:
        print(f"Config file '{config_file}' not found!")
        return {}
    except Exception as e:
        print(f"Error reading config file: {e}")
        return {}

def create_sample_config(config_file='config.txt'):
    """Create a sample configuration file"""
    sample_config = """# YouTube Playlist Extractor Configuration
# Replace the values below with your actual playlist URL and API key

PLAYLIST_URL=https://www.youtube.com/playlist?list=YOUR_PLAYLIST_ID_HERE
API_KEY=your_youtube_data_api_key_here

# Optional settings
OUTPUT_FILE=urls.txt
"""
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(sample_config)
        print(f"Sample config file created: {config_file}")
        print("Please edit the file with your actual values before running the script.")
    except Exception as e:
        print(f"Error creating config file: {e}")

def load_config_from_env():
    """Load configuration from environment variables"""
    return {
        'PLAYLIST_URL': os.getenv('YOUTUBE_PLAYLIST_URL', ''),
        'API_KEY': os.getenv('YOUTUBE_API_KEY', ''),
        'OUTPUT_FILE': os.getenv('OUTPUT_FILE', 'urls.txt')
    }

# Core extraction functions
def extract_urls_with_api(playlist_id, api_key):
    """
    Extract YouTube URLs from playlist using YouTube Data API v3
    
    Args:
        playlist_id (str): YouTube playlist ID
        api_key (str): YouTube Data API key
    
    Returns:
        list: List of video URLs
    """
    base_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    video_urls = []
    next_page_token = None
    
    while True:
        # API parameters
        params = {
            'part': 'snippet',
            'playlistId': playlist_id,
            'key': api_key,
            'maxResults': 50  # Maximum allowed per request
        }
        
        if next_page_token:
            params['pageToken'] = next_page_token
        
        try:
            # Make API request
            response = requests.get(base_url, params=params)
            
            # Better error handling with detailed response
            if response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_message = error_data.get('error', {}).get('message', 'Unknown error')
                error_code = error_data.get('error', {}).get('code', response.status_code)
                
                print(f"API Error {error_code}: {error_message}")
                
                # Common error solutions
                if error_code == 400:
                    print("\nPossible solutions:")
                    print("1. Check if your API key is valid and properly set")
                    print("2. Ensure the playlist ID is correct")
                    print("3. Make sure YouTube Data API v3 is enabled in Google Cloud Console")
                elif error_code == 403:
                    print("\nPossible solutions:")
                    print("1. Check if you've exceeded your API quota")
                    print("2. Verify the API key has proper permissions")
                    print("3. Make sure the playlist is public or you have access")
                elif error_code == 404:
                    print("\nPlaylist not found. Check if:")
                    print("1. The playlist ID is correct")
                    print("2. The playlist is public or you have access")
                
                break
            
            data = response.json()
            
            # Extract video IDs and create URLs
            for item in data.get('items', []):
                try:
                    video_id = item['snippet']['resourceId']['videoId']
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    video_urls.append(video_url)
                except KeyError:
                    # Skip items that don't have video IDs (e.g., private videos)
                    continue
            
            # Check if there are more pages
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Network error: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"Error parsing API response: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    return video_urls

def extract_urls_with_ytdlp(playlist_url):
    """
    Extract URLs using yt-dlp library
    Note: Requires 'pip install yt-dlp'
    """
    try:
        import yt_dlp
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,  # Don't download, just extract info
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)
            
            urls = []
            for entry in playlist_info.get('entries', []):
                if entry:
                    video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                    urls.append(video_url)
            
            return urls
            
    except ImportError:
        print("yt-dlp not installed. Install with: pip install yt-dlp")
        return []
    except Exception as e:
        print(f"Error with yt-dlp: {e}")
        return []

def get_playlist_id_from_url(playlist_url):
    """
    Extract playlist ID from YouTube playlist URL
    
    Args:
        playlist_url (str): Full YouTube playlist URL
        
    Returns:
        str: Playlist ID
    """
    if 'list=' in playlist_url:
        return playlist_url.split('list=')[1].split('&')[0]
    return playlist_url

def validate_api_key(api_key):
    """
    Validate the YouTube Data API key by making a simple test request
    """
    test_url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        'part': 'snippet',
        'q': 'test',
        'key': api_key,
        'maxResults': 1
    }
    
    try:
        response = requests.get(test_url, params=params)
        if response.status_code == 200:
            return True, "API key is valid"
        else:
            error_data = response.json() if response.content else {}
            error_message = error_data.get('error', {}).get('message', 'Invalid API key')
            return False, f"API key validation failed: {error_message}"
    except Exception as e:
        return False, f"Error validating API key: {e}"

def validate_playlist_url(playlist_url):
    """
    Validate and extract playlist ID from URL
    """
    if not playlist_url:
        return False, "No playlist URL provided"
    
    if 'youtube.com' not in playlist_url and 'youtu.be' not in playlist_url:
        return False, "Invalid YouTube URL"
    
    if 'list=' not in playlist_url:
        return False, "No playlist ID found in URL"
    
    playlist_id = get_playlist_id_from_url(playlist_url)
    if len(playlist_id) < 10:  # Basic length check
        return False, "Playlist ID seems too short"
    
    return True, f"Valid playlist ID: {playlist_id}"
    """
    Extract playlist ID from YouTube playlist URL
    
    Args:
        playlist_url (str): Full YouTube playlist URL
        
    Returns:
        str: Playlist ID
    """
    if 'list=' in playlist_url:
        return playlist_url.split('list=')[1].split('&')[0]
    return playlist_url

def save_urls_to_file(urls, filename='urls.txt'):
    """
    Save URLs to a text file
    
    Args:
        urls (list): List of URLs
        filename (str): Output filename
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(url + '\n')
        print(f"Successfully saved {len(urls)} URLs to {filename}")
    except IOError as e:
        print(f"Error saving to file: {e}")

# Main execution functions
def main_with_config():
    """Main function using external configuration"""
    print("YouTube Playlist URL Extractor (Config Version)")
    print("=" * 50)
    
    # Try to load from config file first
    config = load_config_from_file()
    
    # If config file doesn't exist or is incomplete, try environment variables
    if not config.get('PLAYLIST_URL') or not config.get('API_KEY'):
        env_config = load_config_from_env()
        config.update({k: v for k, v in env_config.items() if v})
    
    # If still no config, offer to create sample config or use interactive mode
    if not config.get('PLAYLIST_URL'):
        print("\nNo configuration found!")
        print("1. Create sample config file")
        print("2. Use interactive mode")
        print("3. Exit")
        
        choice = input("Choose option (1-3): ").strip()
        
        if choice == '1':
            create_sample_config()
            return
        elif choice == '2':
            main()  # Fall back to original interactive mode
            return
        else:
            return
    
    playlist_url = config.get('PLAYLIST_URL')
    api_key = config.get('API_KEY')
    output_file = config.get('OUTPUT_FILE', 'urls.txt')
    
    print(f"Using playlist: {playlist_url}")
    print(f"Output file: {output_file}")
    
    # Validate inputs
    print("\nValidating configuration...")
    
    # Validate playlist URL
    url_valid, url_message = validate_playlist_url(playlist_url)
    print(f"Playlist URL: {url_message}")
    if not url_valid:
        return
    
    # Validate API key
    print("Validating API key...")
    key_valid, key_message = validate_api_key(api_key)
    print(f"API Key: {key_message}")
    if not key_valid:
        return
    
    # Extract playlist ID and get URLs
    playlist_id = get_playlist_id_from_url(playlist_url)
    print(f"\nExtracting URLs from playlist ID: {playlist_id}")
    
    urls = extract_urls_with_api(playlist_id, api_key)
    
    if urls:
        print(f"\nFound {len(urls)} videos in the playlist")
        save_urls_to_file(urls, output_file)
        
        # Show first few URLs as preview
        print(f"\nFirst 5 URLs preview:")
        for i, url in enumerate(urls[:5], 1):
            print(f"{i}. {url}")
            
        if len(urls) > 5:
            print(f"... and {len(urls) - 5} more URLs")
    else:
        print("No URLs extracted. Please check your configuration and try again.")

def main():
    """Interactive main function (original version)"""
    print("YouTube Playlist URL Extractor")
    print("=" * 40)
    
    # Get playlist URL from user
    playlist_url = input("Enter YouTube playlist URL: ").strip()
    
    if not playlist_url:
        print("No URL provided!")
        return
    
    # Method selection
    print("\nChoose extraction method:")
    print("1. YouTube Data API (requires API key)")
    print("2. yt-dlp library (requires installation)")
    
    choice = input("Enter choice (1 or 2): ").strip()
    
    urls = []
    
    if choice == '1':
        # API method
        api_key = input("Enter your YouTube Data API key: ").strip()
        if not api_key:
            print("API key required for this method!")
            return
            
        playlist_id = get_playlist_id_from_url(playlist_url)
        print(f"Extracting URLs from playlist ID: {playlist_id}")
        
        urls = extract_urls_with_api(playlist_id, api_key)
        
    elif choice == '2':
        # yt-dlp method
        print("Extracting URLs using yt-dlp...")
        urls = extract_urls_with_ytdlp(playlist_url)
        
    else:
        print("Invalid choice!")
        return
    
    if urls:
        print(f"\nFound {len(urls)} videos in the playlist")
        
        # Save to file
        filename = input("Enter filename (press Enter for 'urls.txt'): ").strip()
        if not filename:
            filename = 'urls.txt'
            
        save_urls_to_file(urls, filename)
        
        # Show first few URLs as preview
        print(f"\nFirst 5 URLs preview:")
        for i, url in enumerate(urls[:5], 1):
            print(f"{i}. {url}")
            
        if len(urls) > 5:
            print(f"... and {len(urls) - 5} more URLs")
            
    else:
        print("No URLs extracted. Please check your playlist URL and try again.")

# Quick usage functions
def run_with_config_file():
    """Run extraction using config.txt file"""
    config = load_config_from_file('config.txt')
    if config.get('PLAYLIST_URL') and config.get('API_KEY'):
        playlist_id = get_playlist_id_from_url(config['PLAYLIST_URL'])
        urls = extract_urls_with_api(playlist_id, config['API_KEY'])
        output_file = config.get('OUTPUT_FILE', 'urls.txt')
        save_urls_to_file(urls, output_file)
        return urls
    else:
        print("Please check your config.txt file")
        return []

def run_with_env_vars():
    """Run extraction using environment variables"""
    config = load_config_from_env()
    if config.get('PLAYLIST_URL') and config.get('API_KEY'):
        playlist_id = get_playlist_id_from_url(config['PLAYLIST_URL'])
        urls = extract_urls_with_api(playlist_id, config['API_KEY'])
        output_file = config.get('OUTPUT_FILE', 'urls.txt')
        save_urls_to_file(urls, output_file)
        return urls
    else:
        print("Please set YOUTUBE_PLAYLIST_URL and YOUTUBE_API_KEY environment variables")
        return []

def quick_extract_api(playlist_url, api_key):
    """Quick extraction using API method"""
    playlist_id = get_playlist_id_from_url(playlist_url)
    urls = extract_urls_with_api(playlist_id, api_key)
    save_urls_to_file(urls)
    return urls

def quick_extract_ytdlp(playlist_url):
    """Quick extraction using yt-dlp method"""
    urls = extract_urls_with_ytdlp(playlist_url)
    save_urls_to_file(urls)
    return urls

# Main execution
if __name__ == "__main__":
    # You can choose which version to run:
    
    # Option 1: Use config file approach (recommended)
    main_with_config()
    
    # Option 2: Use interactive mode (uncomment line below and comment line above)
    # main()
    
    # Option 3: Quick run with config file (uncomment line below and comment line above)
    # run_with_config_file()
    
    # Option 4: Quick run with environment variables (uncomment line below and comment line above)
    # run_with_env_vars()