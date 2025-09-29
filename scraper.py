#!/usr/bin/env python3
"""
YouTube Transcript Scraper
A command-line tool to download transcripts from YouTube videos and channels.
"""

import os
import sys
import csv
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# External dependencies
try:
    import yt_dlp
    import whisper
    import pydub
    from pydub import AudioSegment
    from tqdm import tqdm
    import tempfile
    import os
    import torch
    from datetime import datetime
except ImportError as e:
    print(f"Missing required dependency: {e}")
    print("Please install required packages using: pip install -r requirements.txt")
    sys.exit(1)


class YouTubeTranscriptScraper:
    """Main class for scraping YouTube transcripts using AI transcription"""
    
    def __init__(self):
        """Initialize the scraper with output directory setup"""
        # Create YouTube_Transcripts folder in the program directory
        self.output_dir = Path(__file__).parent / "YouTube_Transcripts"
        self.setup_output_directory()
    
    def setup_output_directory(self):
        """Setup the output directory, checking if it already exists"""
        if self.output_dir.exists():
            print(f"Using existing folder: {self.output_dir}")
        else:
            try:
                self.output_dir.mkdir(exist_ok=True)
                print(f"Created folder: {self.output_dir}")
            except Exception as e:
                print(f"Error creating folder: {e}")
                # Fallback to Desktop if program folder fails
                self.output_dir = Path.home() / "Desktop" / "YouTube_Transcripts"
                self.output_dir.mkdir(exist_ok=True)
                print(f"Fallback to Desktop: {self.output_dir}")
        
        print(f"Output directory: {self.output_dir}")
        
        # Initialize Whisper model
        self.whisper_model = None
        self.model_name = "base"  # Default model
        
    def load_whisper_model(self, model_name: str = "base"):
        """Load Whisper model for transcription"""
        try:
            print(f"Loading Whisper model: {model_name}")
            self.whisper_model = whisper.load_model(model_name)
            self.model_name = model_name
            print(f"✅ Whisper model '{model_name}' loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Error loading Whisper model: {e}")
            return False
    
    def get_user_choice(self) -> str:
        """Get user's choice for scraping mode"""
        print("\n" + "="*60)
        print("YouTube Transcript Scraper (AI-Powered)")
        print("="*60)
        print("Choose scraping mode:")
        print("1. Single video")
        print("2. Entire channel")
        
        while True:
            choice = input("\nEnter your choice (1 or 2): ").strip()
            if choice in ['1', '2']:
                return choice
            print("Invalid choice. Please enter 1 or 2.")
    
    def get_whisper_model_choice(self) -> str:
        """Get user's choice for Whisper model"""
        print("\n" + "="*40)
        print("Whisper Model Selection")
        print("="*40)
        print("Choose Whisper model:")
        print("1. tiny - Fastest, least accurate (good for testing)")
        print("2. base - Good balance of speed/accuracy (recommended)")
        print("3. small - Better accuracy, slower")
        print("4. medium - Best accuracy, requires more RAM/time")
        print("5. large-v3 - Best accuracy, requires most RAM/time")
        
        model_map = {
            '1': 'tiny',
            '2': 'base', 
            '3': 'small',
            '4': 'medium',
            '5': 'large-v3'
        }
        
        while True:
            choice = input("\nEnter your choice (1-5): ").strip()
            if choice in model_map:
                return model_map[choice]
            print("Invalid choice. Please enter 1-5.")
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([^&\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/embed/([^&\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/v/([^&\n?#]+)',
            r'(?:https?://)?youtu\.be/([^&\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([^&\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def extract_channel_id(self, url: str) -> Optional[str]:
        """Extract channel ID from YouTube URL"""
        patterns = [
            r'(?:https?://)?(?:www\.)?youtube\.com/channel/([^/\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/c/([^/\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/user/([^/\n?#]+)',
            r'(?:https?://)?(?:www\.)?youtube\.com/@([^/\n?#]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def get_video_info(self, video_id: str) -> Dict:
        """Get video information using yt-dlp"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                url = f"https://www.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(url, download=False)
                return {
                    'title': info.get('title', 'Unknown Title'),
                    'view_count': info.get('view_count', 0),
                    'duration': info.get('duration', 0),
                }
        except Exception as e:
            print(f"Error getting video info: {e}")
            return {
                'title': 'Unknown Title',
                'view_count': 0,
                'duration': 0,
            }
    
    def get_transcript(self, video_id: str) -> Tuple[str, str]:
        """Analyze video content and generate transcript using Whisper AI"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🤖 AI transcribing {video_id}...")
            
            # Download audio from video
            audio_file = self.download_audio(video_id)
            if not audio_file:
                return "", "Failed to download audio from video"
            
            # Convert audio to text using Whisper
            transcript_text = self.whisper_transcribe(audio_file)
            
            # Clean up temporary file
            if os.path.exists(audio_file):
                os.remove(audio_file)
            
            if transcript_text:
                char_count = len(transcript_text)
                timestamp = datetime.now().strftime("%H:%M:%S")
                print(f"[{timestamp}] ✅ AI transcribed {video_id}: {char_count} chars")
                return transcript_text, f"AI Generated (Whisper {self.model_name})"
            else:
                return "", "Could not generate transcript from audio"
                
        except Exception as e:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] ❌ Error transcribing {video_id}: {str(e)[:100]}")
            return "", f"Error generating transcript: {str(e)[:100]}"
    
    def download_audio(self, video_id: str) -> Optional[str]:
        """Download audio from YouTube video"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': '%(id)s.%(ext)s',
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                url = f"https://www.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(url, download=True)
                
                # Find the downloaded file
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    return filename
                
                # Try different extensions
                for ext in ['webm', 'm4a', 'mp3', 'wav']:
                    test_file = f"{video_id}.{ext}"
                    if os.path.exists(test_file):
                        return test_file
                
                return None
                
        except Exception as e:
            print(f"Error downloading audio: {e}")
            return None
    
    def whisper_transcribe(self, audio_file: str) -> str:
        """Convert audio file to text using Whisper AI"""
        try:
            if not self.whisper_model:
                print("Loading Whisper model...")
                if not self.load_whisper_model(self.model_name):
                    return ""
            
            # Load and process audio with Whisper
            result = self.whisper_model.transcribe(audio_file)
            
            # Extract text from result
            transcript_text = result["text"].strip()
            return transcript_text
            
        except Exception as e:
            print(f"Error in Whisper transcription: {e}")
            return ""
    
    
    def get_channel_videos(self, channel_url: str, max_videos: int, video_type: str = "all") -> List[str]:
        """Get list of video IDs from a channel"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlist_items': f'1:{max_videos}',
            }
            
            # Build URL based on channel type
            if 'youtube.com/channel/' in channel_url or 'youtube.com/c/' in channel_url or 'youtube.com/@' in channel_url:
                # Channel URL - get uploads playlist
                channel_url = channel_url.rstrip('/')
                if channel_url.endswith('/videos'):
                    uploads_url = channel_url
                else:
                    uploads_url = f"{channel_url}/videos"
            else:
                uploads_url = channel_url
            
            video_ids = []
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(uploads_url, download=False)
                
                if 'entries' in info:
                    for entry in info['entries'][:max_videos]:
                        if entry and entry.get('id'):
                            video_ids.append(entry['id'])
                
            return video_ids
            
        except Exception as e:
            print(f"Error getting channel videos: {e}")
            return []
    
    def scrape_single_video(self):
        """Scrape transcript for a single video"""
        print("\n" + "="*40)
        print("Single Video Mode")
        print("="*40)
        
        while True:
            url = input("\nEnter YouTube video URL: ").strip()
            if not url:
                print("Please enter a valid URL.")
                continue
            
            video_id = self.extract_video_id(url)
            if not video_id:
                print("Invalid YouTube URL. Please try again.")
                continue
            
            print(f"\nProcessing video: {video_id}")
            
            # Get video info
            video_info = self.get_video_info(video_id)
            print(f"Title: {video_info['title']}")
            print(f"Views: {video_info['view_count']:,}")
            if video_info['duration'] > 0:
                minutes, seconds = divmod(video_info['duration'], 60)
                print(f"Duration: {minutes}:{seconds:02d}")
            
            # Get transcript
            transcript_text, transcript_type = self.get_transcript(video_id)
            
            if transcript_text:
                print(f"\nTranscript Type: {transcript_type}")
                print("\n" + "="*60)
                print("TRANSCRIPT:")
                print("="*60)
                print(transcript_text)
                print("="*60)
            else:
                print(f"\nNo transcript available: {transcript_type}")
            
            break
    
    def scrape_channel(self):
        """Scrape transcripts for multiple videos in a channel"""
        print("\n" + "="*40)
        print("Channel Scrape Mode")
        print("="*40)
        
        # Get channel URL
        while True:
            channel_url = input("\nEnter YouTube channel URL: ").strip()
            if not channel_url:
                print("Please enter a valid URL.")
                continue
            break
        
        # Get number of videos to scrape
        while True:
            try:
                max_videos = int(input("\nNumber of videos to scrape (e.g., 25): "))
                if max_videos <= 0:
                    print("Please enter a positive number.")
                    continue
                break
            except ValueError:
                print("Please enter a valid number.")
        
        # Get video type preference
        print("\nVideo type preference:")
        print("1. Longform videos")
        print("2. Shorts")
        print("3. Both")
        
        while True:
            type_choice = input("Enter your choice (1, 2, or 3): ").strip()
            if type_choice in ['1', '2', '3']:
                video_type_map = {'1': 'longform', '2': 'shorts', '3': 'all'}
                video_type = video_type_map[type_choice]
                break
            print("Invalid choice. Please enter 1, 2, or 3.")
        
        print(f"\nFetching videos from channel...")
        video_ids = self.get_channel_videos(channel_url, max_videos, video_type)
        
        if not video_ids:
            print("No videos found or error accessing channel.")
            return
        
        print(f"Found {len(video_ids)} videos to process.")
        
        # Create CSV file
        channel_name = channel_url.split('/')[-1].replace('@', '').replace('c/', '')
        csv_filename = f"YouTube_Transcripts_{channel_name}_{len(video_ids)}videos.csv"
        csv_path = self.output_dir / csv_filename
        
        # Process videos with progress bar
        processed_count = 0
        successful_count = 0
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Title', 'Video URL', 'View Count', 'Transcript']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            print(f"\n🚀 Starting Advanced Scraping...")
            for i, video_id in enumerate(video_ids, 1):
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                
                # Get video info
                video_info = self.get_video_info(video_id)
                print(f"\n[{i}/{len(video_ids)}] Processing: {video_info['title'][:50]}...")
                
                # Get transcript
                transcript_text, transcript_type = self.get_transcript(video_id)
                
                # Write to CSV
                writer.writerow({
                    'Title': video_info['title'],
                    'Video URL': video_url,
                    'View Count': video_info['view_count'],
                    'Transcript': transcript_text if transcript_text else f"[{transcript_type}]"
                })
                
                processed_count += 1
                if transcript_text:
                    successful_count += 1
                
                print()  # Empty line for spacing
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"\nSCRAPING COMPLETED! 🎉")
        print(f"[{timestamp}] 📊 Results:")
        print(f"[{timestamp}] • Total videos processed: {processed_count}")
        print(f"[{timestamp}] • Transcripts found: {successful_count}/{processed_count} ({(successful_count/processed_count)*100:.1f}%)")
        print(f"[{timestamp}] • CSV saved: {csv_path.name}")
        print(f"[{timestamp}] ❌ Error during scraping:")
        print()  # Empty line for spacing
    
    def run(self):
        """Main entry point"""
        choice = self.get_user_choice()
        
        # Get Whisper model choice
        model_choice = self.get_whisper_model_choice()
        if not self.load_whisper_model(model_choice):
            print("Failed to load Whisper model. Exiting.")
            return
        
        if choice == '1':
            self.scrape_single_video()
        elif choice == '2':
            self.scrape_channel()


def main():
    """Main function"""
    try:
        scraper = YouTubeTranscriptScraper()
        scraper.run()
    except KeyboardInterrupt:
        print("\n\nScraping cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
