import logging
import re
import os
import requests
from typing import Optional, Tuple
from youtube_transcript_api import YouTubeTranscriptApi

# Configure logging
def setup_logging():
    """Set up logging configuration"""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create formatters
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create and configure file handler
    file_handler = logging.FileHandler('logs/transcript_extracter.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    
    # Create and configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    
    # Get the logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

class TranscriptExtractor:

    def sanitize_filename(self, title: str) -> str:
        """Remove invalid characters from filename"""
        # Remove invalid chars
        title = re.sub(r'[<>:"/\\|?*]', '', title)
        # Replace problematic characters
        title = title.replace('\n', ' ').replace('\r', ' ')
        # Trim spaces and dots at the end
        title = title.strip('. ')
        return title if title else 'untitled'

    def extract_transcript(self, video_url: str, output_file: Optional[str] = None) -> Tuple[str, str]:
        """Extract transcript from a YouTube video."""
        try:
            # Extract video ID from either youtube.com or youtu.be URLs
            logger.info(f"Processing URL: {video_url}")
            
            # Get video ID
            if 'youtu.be/' in video_url:
                logger.info("Detected youtu.be URL")
                parts = video_url.split('youtu.be/')
                if len(parts) < 2:
                    raise ValueError("Invalid youtu.be URL format")
                video_id = parts[1].split('?')[0]
            else:
                logger.info("Detected youtube.com URL")
                match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", video_url)
                if not match:
                    raise ValueError("Invalid YouTube URL")
                video_id = match.group(1)
            
            logger.info(f"Extracted video ID: {video_id}")
            if not video_id or len(video_id) != 11:
                raise ValueError(f"Invalid video ID length: {len(video_id) if video_id else 'None'}")
            
            # Get video title
            logger.info("Fetching video title...")
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept-Language': 'en-US,en;q=0.9'
                }
                response = requests.get(video_url, headers=headers)
                response.raise_for_status()
                
                # Extract title using regex
                title_match = re.search(r'<title>(.+?)</title>', response.text)
                if title_match:
                    title = title_match.group(1).replace('- YouTube', '').strip()
                    title = self.sanitize_filename(title)
                else:
                    raise ValueError("Could not find video title")
                    
            except Exception as e:
                logger.warning(f"Could not fetch title: {str(e)}")
                title = video_id  # Use video ID as fallback
            logger.info(f"Video title: {title}")
            
            # Get transcript
            logger.info(f"Fetching transcript for video: {video_id}")
            ytt_api = YouTubeTranscriptApi()
            transcript = ytt_api.fetch(video_id)
            
            # Combine transcript text
            text = "\n".join(entry.text for entry in transcript)
            
            # Save to file if specified
            if output_file:
                # Replace the filename with the title
                output_dir = os.path.dirname(output_file)
                output_file = os.path.join(output_dir, f"{title}.txt")
                os.makedirs(os.path.dirname(output_file) or ".", exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(text)
                logger.info(f"Saved transcript to: {output_file}")
            
            return text, output_file
            
        except Exception as e:
            logger.error(f"Failed to extract transcript: {str(e)}")
            raise

def main():
    extractor = TranscriptExtractor()
    
    try:
        # Create transcripts directory
        os.makedirs("transcripts", exist_ok=True)
        
        # Process each video
        with open("urls.txt", "r") as f:
            urls = [line.strip() for line in f if line.strip()]
        
        print(f"\nProcessing {len(urls)} videos...")
        for i, url in enumerate(urls, 1):
            try:
                if 'youtu.be/' in url:
                    video_id = url.split('youtu.be/')[1].split('?')[0]
                else:
                    video_id = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url).group(1)
                output_file = os.path.join("transcripts", f"{video_id}.txt")
                
                print(f"[{i}/{len(urls)}] Processing: {url}")
                _, saved_file = extractor.extract_transcript(url, output_file)
                print(f" Saved transcript to: {saved_file}")
                
            except Exception as e:
                print(f" Error processing {url}: {str(e)}")
                continue
        
        print("\nProcessing completed!")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
