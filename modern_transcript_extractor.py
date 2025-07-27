#!/usr/bin/env python3
"""
Updated YouTube Transcript Extractor (2025)
Addresses SOCKS library concerns and YouTube IP blocking issues

Key Updates:
- Uses modern proxy approaches without relying on potentially archived libraries
- Leverages youtube-transcript-api's native WebshareProxyConfig support
- Provides multiple fallback strategies including requests[socks] and python-socks
- Handles YouTube IP blocking with residential proxies
"""

import logging
import os
import random
import re
import sys
import time
from typing import List, Optional, Tuple
import requests

# Modern approach: Use requests[socks] or youtube-transcript-api native proxy support
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.proxies import WebshareProxyConfig
    from youtube_transcript_api import (
        IpBlocked, RequestBlocked, NoTranscriptFound, 
        TranscriptsDisabled, VideoUnavailable
    )
    NATIVE_PROXY_SUPPORT = True
except ImportError:
    print("Install with: pip install youtube-transcript-api>=1.0.0")
    sys.exit(1)

# Optional: Modern SOCKS alternatives (choose one)
try:
    # Option 1: python-socks (modern, actively maintained)
    from python_socks.sync import Proxy as PythonSocksProxy
    PYTHON_SOCKS_AVAILABLE = True
except ImportError:
    PYTHON_SOCKS_AVAILABLE = False

try:
    # Option 2: requests[socks] (uses PySocks under the hood but handles installation)
    import socks  # This comes with requests[socks]
    REQUESTS_SOCKS_AVAILABLE = True
except ImportError:
    REQUESTS_SOCKS_AVAILABLE = False

# --------------------------------------------------------------------------- #
# Logging setup
# --------------------------------------------------------------------------- #
def setup_logging() -> logging.Logger:
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("TranscriptExtractor")
    logger.setLevel(logging.DEBUG)

    # File handler
    fh = logging.FileHandler("logs/transcript_extractor.log", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

logger = setup_logging()

# --------------------------------------------------------------------------- #
# Modern Transcript Extractor with Multiple Proxy Strategies
# --------------------------------------------------------------------------- #
class ModernTranscriptExtractor:
    def __init__(self, min_delay: float = 2.0, max_delay: float = 5.0, max_retries: int = 3):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

    def _rand_delay(self) -> float:
        return random.uniform(self.min_delay, self.max_delay)

    @staticmethod
    def _sanitize_filename(name: str, max_len: int = 250) -> str:
        name = re.sub(r'[<>:"/\\|?*\n\r]+', "", name).strip()
        name = re.sub(r"\s+", " ", name)
        return name[:max_len] if len(name) > max_len else name

    @staticmethod
    def _extract_video_id(url: str) -> str:
        if "youtu.be/" in url:
            return url.split("youtu.be/")[1].split("?")[0]
        match = re.search(r"[?&]v=([a-zA-Z0-9_-]{11})", url)
        if not match:
            raise ValueError(f"Cannot parse video ID from URL: {url}")
        return match.group(1)

    def _fetch_title(self, url: str) -> str:
        for attempt in range(1, self.max_retries + 1):
            try:
                time.sleep(self._rand_delay())
                r = requests.get(url, headers=self.headers, timeout=15)
                r.raise_for_status()
                m = re.search(r"<title>(.+?)</title>", r.text)
                if m:
                    title = m.group(1).replace("- YouTube", "").strip()
                    return self._sanitize_filename(title)
            except Exception as exc:
                logger.warning("Title fetch attempt %d/%d failed: %s", 
                              attempt, self.max_retries, exc)
        return self._extract_video_id(url)

    # Strategy 1: Native WebshareProxyConfig (Recommended for 2025)
    def _create_webshare_api(self, username: str, password: str) -> YouTubeTranscriptApi:
        """Use youtube-transcript-api's native Webshare integration (v1.0.0+)"""
        if not NATIVE_PROXY_SUPPORT:
            raise RuntimeError("Native proxy support not available")

        proxy_config = WebshareProxyConfig(
            proxy_username=username,
            proxy_password=password,
            retries_when_blocked=0,  # We handle retries manually
        )
        return YouTubeTranscriptApi(proxy_config=proxy_config)

    # Strategy 2: requests[socks] approach
    def _create_requests_socks_session(self, proxy_url: str) -> requests.Session:
        """Create a requests session with SOCKS proxy using requests[socks]"""
        if not REQUESTS_SOCKS_AVAILABLE:
            raise RuntimeError("Install with: pip install 'requests[socks]'")

        session = requests.Session()
        session.proxies = {
            'http': proxy_url,
            'https': proxy_url
        }
        return session

    # Strategy 3: python-socks approach (most modern)
    def _create_python_socks_session(self, proxy_url: str) -> requests.Session:
        """Create a session using modern python-socks library"""
        if not PYTHON_SOCKS_AVAILABLE:
            raise RuntimeError("Install with: pip install python-socks[asyncio]")

        # Parse proxy URL
        from urllib.parse import urlparse
        parsed = urlparse(proxy_url)

        proxy = PythonSocksProxy.from_url(proxy_url)
        # Note: This would require custom adapter integration
        # For simplicity, fall back to requests[socks] approach
        return self._create_requests_socks_session(proxy_url)

    # Main extraction methods
    def extract_with_webshare(self, video_id: str, username: str, password: str) -> List[dict]:
        """Extract transcript using Webshare residential proxies (Recommended)"""
        for attempt in range(self.max_retries):
            try:
                time.sleep(self._rand_delay())
                api = self._create_webshare_api(username, password)
                transcript_list = api.list(video_id)

                try:
                    transcript = transcript_list.find_transcript(["en"])
                except NoTranscriptFound:
                    logger.info("Manual EN not found; using auto-generated")
                    transcript = transcript_list.find_generated_transcript(["en"])

                return transcript.fetch().to_raw_data()

            except (IpBlocked, RequestBlocked) as exc:
                wait_time = self._rand_delay() * (attempt + 2)
                logger.warning("Proxy blocked (attempt %d/%d); waiting %.1fs", 
                              attempt + 1, self.max_retries, wait_time)
                time.sleep(wait_time)
            except Exception as exc:
                logger.warning("Webshare attempt %d/%d failed: %s", 
                              attempt + 1, self.max_retries, exc)

        raise RuntimeError(f"Webshare extraction failed after {self.max_retries} attempts")

    def extract_with_tor(self, video_id: str, tor_proxy: str = "socks5h://127.0.0.1:9050") -> List[dict]:
        """Extract transcript using Tor SOCKS proxy"""
        if not REQUESTS_SOCKS_AVAILABLE:
            raise RuntimeError("Tor method requires: pip install 'requests[socks]'")

        for attempt in range(self.max_retries):
            try:
                time.sleep(self._rand_delay())

                # Create API instance with Tor proxy
                session = self._create_requests_socks_session(tor_proxy)
                api = YouTubeTranscriptApi(http_client=session)

                transcript_list = api.list(video_id)
                try:
                    transcript = transcript_list.find_transcript(["en"])
                except NoTranscriptFound:
                    transcript = transcript_list.find_generated_transcript(["en"])

                return transcript.fetch().to_raw_data()

            except Exception as exc:
                logger.warning("Tor attempt %d/%d failed: %s", 
                              attempt + 1, self.max_retries, exc)
                time.sleep(self._rand_delay() * (attempt + 1))

        raise RuntimeError(f"Tor extraction failed after {self.max_retries} attempts")

    def extract_with_custom_proxy(self, video_id: str, proxy_url: str) -> List[dict]:
        """Extract transcript using any SOCKS/HTTP proxy"""
        for attempt in range(self.max_retries):
            try:
                time.sleep(self._rand_delay())

                if proxy_url.startswith("socks"):
                    if not REQUESTS_SOCKS_AVAILABLE:
                        raise RuntimeError("SOCKS support requires: pip install 'requests[socks]'")
                    session = self._create_requests_socks_session(proxy_url)
                else:
                    # HTTP proxy
                    session = requests.Session()
                    session.proxies = {'http': proxy_url, 'https': proxy_url}

                api = YouTubeTranscriptApi(http_client=session)
                transcript_list = api.list(video_id)

                try:
                    transcript = transcript_list.find_transcript(["en"])
                except NoTranscriptFound:
                    transcript = transcript_list.find_generated_transcript(["en"])

                return transcript.fetch().to_raw_data()

            except Exception as exc:
                logger.warning("Custom proxy attempt %d/%d failed: %s", 
                              attempt + 1, self.max_retries, exc)
                time.sleep(self._rand_delay() * (attempt + 1))

        raise RuntimeError(f"Custom proxy extraction failed after {self.max_retries} attempts")

    def extract_transcript(self, url: str, out_dir: str = "transcripts", 
                          proxy_strategy: str = "webshare", **proxy_kwargs) -> Tuple[str, str]:
        """
        Extract transcript with multiple fallback strategies

        Args:
            url: YouTube URL
            out_dir: Output directory
            proxy_strategy: 'webshare', 'tor', 'custom', or 'direct'
            **proxy_kwargs: Strategy-specific arguments

        Returns:
            Tuple of (title, output_path)
        """
        video_id = self._extract_video_id(url)
        title = self._fetch_title(url)

        # Try different proxy strategies
        if proxy_strategy == "webshare" and "username" in proxy_kwargs:
            transcript_data = self.extract_with_webshare(
                video_id, proxy_kwargs["username"], proxy_kwargs["password"]
            )
        elif proxy_strategy == "tor":
            tor_proxy = proxy_kwargs.get("proxy_url", "socks5h://127.0.0.1:9050")
            transcript_data = self.extract_with_tor(video_id, tor_proxy)
        elif proxy_strategy == "custom" and "proxy_url" in proxy_kwargs:
            transcript_data = self.extract_with_custom_proxy(video_id, proxy_kwargs["proxy_url"])
        else:
            # Direct connection (likely to fail on cloud servers)
            logger.warning("Using direct connection - may fail due to IP blocking")
            api = YouTubeTranscriptApi()
            transcript_list = api.list(video_id)
            try:
                transcript = transcript_list.find_transcript(["en"])
            except NoTranscriptFound:
                transcript = transcript_list.find_generated_transcript(["en"])
            transcript_data = transcript.fetch().to_raw_data()

        # Save transcript
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{title}.txt")

        with open(out_path, "w", encoding="utf-8") as f:
            for entry in transcript_data:
                f.write(entry["text"] + "\n")

        return title, out_path

# --------------------------------------------------------------------------- #
# Updated main function with modern proxy support
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Main function demonstrating various proxy strategies for 2025
    """
    extractor = ModernTranscriptExtractor()

    # Load configuration
    webshare_user = os.getenv("WEBSHARE_USERNAME")
    webshare_pass = os.getenv("WEBSHARE_PASSWORD")
    custom_proxy = os.getenv("CUSTOM_PROXY_URL")  # e.g., "socks5://user:pass@host:port"

    # Read URLs
    try:
        with open("urls.txt", "r", encoding="utf-8") as f:
            urls = [u.strip() for u in f if u.strip()]
        if not urls:
            raise FileNotFoundError
    except FileNotFoundError:
        logger.error("Create urls.txt with YouTube URLs (one per line)")
        sys.exit(1)

    logger.info("Found %d URLs to process", len(urls))
    success = fail = 0

    for idx, url in enumerate(urls, 1):
        logger.info("[%d/%d] Processing %s", idx, len(urls), url)

        try:
            # Strategy selection (priority order for 2025)
            if webshare_user and webshare_pass:
                # Best option: Native Webshare support
                title, path = extractor.extract_transcript(
                    url, proxy_strategy="webshare", 
                    username=webshare_user, password=webshare_pass
                )
                logger.info("✓ Extracted via Webshare: '%s' → %s", title, path)

            elif custom_proxy:
                # Second option: Custom proxy
                title, path = extractor.extract_transcript(
                    url, proxy_strategy="custom", proxy_url=custom_proxy
                )
                logger.info("✓ Extracted via custom proxy: '%s' → %s", title, path)

            elif REQUESTS_SOCKS_AVAILABLE:
                # Third option: Tor (if running)
                title, path = extractor.extract_transcript(
                    url, proxy_strategy="tor"
                )
                logger.info("✓ Extracted via Tor: '%s' → %s", title, path)

            else:
                # Last resort: Direct (likely to fail on cloud)
                logger.warning("No proxy configured - attempting direct connection")
                title, path = extractor.extract_transcript(url, proxy_strategy="direct")
                logger.info("✓ Extracted directly: '%s' → %s", title, path)

            success += 1

        except Exception as exc:
            logger.error("✗ Failed to process %s: %s", url, exc)
            fail += 1

    logger.info("Finished: %d succeeded, %d failed", success, fail)

if __name__ == "__main__":
    print("\n" + "="*70)
    print("MODERN YOUTUBE TRANSCRIPT EXTRACTOR (2025)")
    print("="*70)
    print("Addresses SOCKS library concerns and YouTube IP blocking")
    print()
    print("Setup Options (choose one):")
    print("1. Webshare (Recommended): pip install youtube-transcript-api>=1.0.0")
    print("   Set: WEBSHARE_USERNAME and WEBSHARE_PASSWORD environment variables")
    print()
    print("2. Requests SOCKS: pip install 'requests[socks]'")
    print("   For Tor: docker run -d -p9050:9050 dperson/torproxy")
    print()
    print("3. Modern python-socks: pip install 'python-socks[asyncio]'")
    print("   Set: CUSTOM_PROXY_URL=socks5://user:pass@host:port")
    print()
    print("Library Status Check:")
    print(f"- Native Webshare support: {'✓' if NATIVE_PROXY_SUPPORT else '✗'}")
    print(f"- requests[socks] available: {'✓' if REQUESTS_SOCKS_AVAILABLE else '✗'}")
    print(f"- python-socks available: {'✓' if PYTHON_SOCKS_AVAILABLE else '✗'}")
    print("="*70)
    print()

    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Interrupted by user")
        sys.exit(130)
