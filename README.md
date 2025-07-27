# YouTube Transcript Downloader

A Python script to download transcripts from YouTube videos using video URLs.

## Features

- Supports both youtube.com and youtu.be URLs
- Downloads transcripts from single videos
- Saves transcripts with video titles as filenames
- Detailed logging for debugging
- Error handling and recovery

## Setup

1. Clone the repository:

```bash
git clone <your-repo-url>
cd transcript_downloader
```

1. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

1. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Create a file named `urls.txt` with YouTube video URLs (one per line)

1. Run the script:

```bash
python transcript_extracter.py
```

1. Transcripts will be saved in the `transcripts` directory with the video titles as filenames

## Logs

Logs are saved in the `logs` directory:

- `transcript_extracter.log`: Detailed debug logs

## Project Structure

```plaintext
transcript_downloader/
├── transcript_extracter.py  # Main script
├── requirements.txt         # Python dependencies
├── urls.txt                # Input file with video URLs
├── transcripts/            # Output directory for transcripts
└── logs/                   # Log files directory
```

## Dependencies

- youtube_transcript_api
- requests

## Error Handling

The script handles various errors:

- Invalid URLs
- Missing transcripts
- Network issues
- File system errors

Each error is logged and the script continues processing the remaining URLs.
