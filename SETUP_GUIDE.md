# Modern YouTube Transcript Extractor Setup Guide (2025)

## The SOCKS Library Situation

**Good News**: PySocks is NOT archived! The library is still available on PyPI (v1.7.1). 
However, there are concerns about maintenance, so modern alternatives are recommended.

## Installation Options (Choose One)

### Option 1: Native Webshare Support (RECOMMENDED for 2025)
```bash
pip install "youtube-transcript-api>=1.0.0"
```

Set environment variables:
```bash
export WEBSHARE_USERNAME="your-username"
export WEBSHARE_PASSWORD="your-password"
```

**Pros**: 
- Native integration, no additional SOCKS libraries needed
- Residential proxies work best against YouTube blocks
- Recommended by youtube-transcript-api maintainer

### Option 2: requests[socks] (Easy Setup)
```bash
pip install "requests[socks]" "youtube-transcript-api>=1.1.0"
```

For Tor proxy:
```bash
docker run -d -p9050:9050 dperson/torproxy
```

**Pros**: 
- Automatically installs PySocks
- Works with any SOCKS proxy (Tor, commercial proxies)
- No need to manage PySocks directly

### Option 3: Modern python-socks (Most Future-Proof)
```bash
pip install "python-socks[asyncio]" "youtube-transcript-api>=1.1.0"
```

Set custom proxy:
```bash
export CUSTOM_PROXY_URL="socks5://user:pass@host:port"
```

**Pros**: 
- Actively maintained (last updated Feb 2025)
- Full async support
- No dependency on PySocks

## Library Status Comparison (July 2025)

| Library | Status | Last Update | Maintenance | Recommendation |
|---------|--------|-------------|-------------|----------------|
| PySocks | Active | Sep 2019 | Stagnant | ⚠️ Still works but consider alternatives |
| python-socks | Active | Feb 2025 | ✅ Active | ✅ Recommended for new projects |
| requests[socks] | Active | Ongoing | ✅ Active | ✅ Easy drop-in replacement |
| sockslib | Active | Jul 2023 | ⚠️ Moderate | ⭕ Alternative option |

## Quick Migration Guide

### From Old Script (with PySocks issues)
Replace:
```python
import socks  # Old direct PySocks import
session.proxies = {'http': 'socks5://127.0.0.1:9050'}
```

With:
```python
# Modern approach - let requests[socks] handle it
pip install 'requests[socks]'  # This installs PySocks automatically
session.proxies = {'http': 'socks5h://127.0.0.1:9050'}  # Note the 'h'
```

### Environment Variables Setup
```bash
# For Webshare (recommended)
export WEBSHARE_USERNAME="your-webshare-username"
export WEBSHARE_PASSWORD="your-webshare-password"

# For custom SOCKS proxy
export CUSTOM_PROXY_URL="socks5://user:pass@proxy-host:1080"

# For Tor
# No setup needed if running on localhost:9050
```

## Usage Examples

### 1. With Webshare (Best Success Rate)
```python
python modern_transcript_extractor.py
# Uses Webshare automatically if credentials are set
```

### 2. With Tor
```bash
# Start Tor proxy
docker run -d -p9050:9050 dperson/torproxy

# Run extractor
python modern_transcript_extractor.py
```

### 3. With Custom Proxy
```bash
export CUSTOM_PROXY_URL="socks5://username:password@proxy.example.com:1080"
python modern_transcript_extractor.py
```

## Troubleshooting

### "Missing dependencies for SOCKS support"
**Solution**: Use `requests[socks]` instead of manual PySocks installation:
```bash
pip uninstall PySocks  # Remove old installation
pip install 'requests[socks]'  # Let requests handle it
```

### "socks has been archived" Error
This is likely a misunderstanding. PySocks is not archived. However, use modern alternatives:
```bash
pip install python-socks[asyncio]  # Modern replacement
```

### Still Getting IP Blocks
1. **Use residential proxies** (Webshare, Smartproxy, etc.) instead of datacenter IPs
2. **Add more delay** between requests (increase min_delay/max_delay)
3. **Rotate user agents** and other headers
4. **Try different proxy locations**

## Cost Comparison (Monthly)

| Service | Price | Success Rate | Setup Complexity |
|---------|-------|--------------|------------------|
| Webshare Residential | $6-30/mo | ⭐⭐⭐⭐⭐ | Low |
| Tor (Free) | Free | ⭐⭐⭐ | Medium |
| Datacenter Proxies | $5-20/mo | ⭐⭐ | Low |
| VPN Services | $3-10/mo | ⭐⭐ | Medium |

## Final Recommendation

For production use in 2025:
1. **First choice**: Webshare + native youtube-transcript-api integration
2. **Budget option**: Tor + requests[socks]
3. **Developer option**: python-socks for custom integrations

The "socks archived" concern is addressed by using `requests[socks]` or `python-socks` instead of directly depending on PySocks.
