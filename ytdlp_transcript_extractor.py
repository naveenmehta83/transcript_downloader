#!/usr/bin/env python3
"""
YouTube Transcript Extractor using yt-dlp
More reliable than youtube-transcript-api for avoiding blocks
"""

import yt_dlp
import os
import json
from pathlib import Path

def extract_transcript_ytdlp(url: str, output_dir: str = "transcripts"):
    """Extract transcripts using yt-dlp"""
    
    # Configure yt-dlp options
    ydl_opts = {
        'writeautomaticsub': True,      # Download auto-generated subtitles
        'writesubtitles': True,         # Download manual subtitles if available  
        'subtitlesformat': 'json3',     # JSON format for easy parsing
        'skip_download': True,          # Only get subtitles, not video
        'subtitleslangs': ['en'],       # English subtitles only
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
    }
    
    os.makedirs(output_dir, exist_ok=True)
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            # Extract video info
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'Unknown')
            
            # Download subtitles
            ydl.download([url])
            
            # Find and process subtitle files
            subtitle_files = list(Path(output_dir).glob(f"*{title}*.json3"))
            
            if subtitle_files:
                subtitle_file = subtitle_files[0]
                
                # Convert JSON3 subtitles to plain text
                with open(subtitle_file, 'r', encoding='utf-8') as f:
                    subtitle_data = json.load(f)
                
                # Extract text from subtitle events
                transcript_text = []
                for event in subtitle_data.get('events', []):
                    if 'segs' in event:
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                transcript_text.append(seg['utf8'])
                
                # Save as plain text
                text_file = subtitle_file.with_suffix('.txt')
                with open(text_file, 'w', encoding='utf-8') as f:
                    f.write(' '.join(transcript_text))
                
                # Clean up JSON file
                subtitle_file.unlink()
                
                print(f"✓ Transcript saved: {text_file}")
                return str(text_file)
            else:
                print(f"✗ No subtitles found for: {title}")
                return None
                
        except Exception as e:
            print(f"✗ Error processing {url}: {e}")
            return None

def main():
    """Process URLs from urls.txt"""
    try:
        with open("urls.txt", "r") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: urls.txt not found")
        return
    
    print(f"Processing {len(urls)} URLs with yt-dlp...")
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{len(urls)}] Processing: {url}")
        extract_transcript_ytdlp(url)

if __name__ == "__main__":
    main()
