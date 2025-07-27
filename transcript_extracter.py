#!/usr/bin/env python3
"""
YouTube Transcript Extractor - No Proxy Version
Removes Tor dependency and focuses on robust retry mechanisms
"""

import logging
import os
import random
import re
import sys
import time
from typing import List, Tuple

import requests
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    IpBlocked,
    RequestBlocked,
    NoTranscriptFound,
    TranscriptsDisabled,
)

# Setup logging
def setup_logging():
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("TranscriptExtractor")
    logger.setLevel(logging.DEBUG)
    
    # File and console handlers
    fh = logging.FileHandler("logs/transcript_extractor.log", encoding="utf-8")
    ch = logging.StreamHandler()
    
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logging()

class TranscriptExtractor:
    def __init__(self):
        self.api = YouTubeTranscriptApi()
        self.min_delay = 5  # Increased delay to avoid blocks
        self.max_delay = 15
        self.max_retries = 3
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def _rand_delay(self):
        return random.uniform(self.min_delay, self.max_delay)
    
    def _extract_video_id(self, url: str) -> str:
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
        if not match:
            raise ValueError(f"Cannot parse video ID from URL: {url}")
        return match.group(1)
    
    def _sanitize_filename(self, name: str) -> str:
        name = re.sub(r'[<>:"/\\|?*\n\r]+', "", name).strip()
        return re.sub(r"\s+", " ", name)[:250]
    
    def _fetch_title(self, url: str) -> str:
        """Fetch title with extended retry logic"""
        for attempt in range(self.max_retries):
            try:
                time.sleep(self._rand_delay())
                response = requests.get(url, headers=self.headers, timeout=30)
                response.raise_for_status()
                
                match = re.search(r"<title>(.+?)</title>", response.text)
                if match:
                    title = match.group(1).replace("- YouTube", "").strip()
                    return self._sanitize_filename(title)
            except Exception as e:
                logger.warning(f"Title fetch attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self._rand_delay() * (attempt + 1))
        
        # Fallback to video ID
        return self._extract_video_id(url)
    
    def _fetch_transcript_direct(self, video_id: str) -> List[dict]:
        """Direct transcript fetch without proxy"""
        for attempt in range(self.max_retries):
            try:
                # Extended delay to avoid rate limiting
                time.sleep(self._rand_delay())
                
                transcript_list = self.api.list(video_id)
                
                # Try manual English first, then auto-generated
                try:
                    transcript = transcript_list.find_transcript(['en'])
                except NoTranscriptFound:
                    logger.info("Manual English not found, trying auto-generated")
                    transcript = transcript_list.find_generated_transcript(['en'])
                
                return transcript.fetch().to_raw_data()
                
            except (IpBlocked, RequestBlocked) as e:
                logger.error(f"IP blocked on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    # Exponential backoff for IP blocks
                    wait_time = self._rand_delay() * (2 ** attempt)
                    logger.info(f"Waiting {wait_time:.1f}s before retry...")
                    time.sleep(wait_time)
                else:
                    raise RuntimeError("All attempts failed due to IP blocking")
                    
            except (TranscriptsDisabled, NoTranscriptFound) as e:
                raise RuntimeError(f"Transcript not available: {e}")
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self._rand_delay())
        
        raise RuntimeError(f"Failed after {self.max_retries} attempts")
    
    def extract_transcript(self, url: str, output_dir: str = "transcripts") -> Tuple[str, str]:
        """Extract transcript without proxy dependency"""
        try:
            video_id = self._extract_video_id(url)
            logger.info(f"Processing video ID: {video_id}")
            
            # Get title and transcript
            title = self._fetch_title(url)
            logger.info(f"Video title: {title}")
            
            transcript_data = self._fetch_transcript_direct(video_id)
            
            # Save transcript
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{title}.txt")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                for entry in transcript_data:
                    f.write(entry['text'] + '\n')
            
            logger.info(f"Transcript saved: {output_path}")
            return title, output_path
            
        except Exception as e:
            logger.error(f"Failed to extract transcript: {e}")
            raise

def main():
    extractor = TranscriptExtractor()
    
    # Read URLs
    try:
        with open("urls.txt", "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        logger.error("urls.txt not found. Create it with one YouTube URL per line.")
        return
    
    logger.info(f"Processing {len(urls)} URLs...")
    success = fail = 0
    
    for i, url in enumerate(urls, 1):
        logger.info(f"[{i}/{len(urls)}] Processing: {url}")
        try:
            title, path = extractor.extract_transcript(url)
            logger.info(f"✓ Success: {title}")
            success += 1
        except Exception as e:
            logger.error(f"✗ Failed: {e}")
            fail += 1
    
    logger.info(f"Completed: {success} successful, {fail} failed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(1)
