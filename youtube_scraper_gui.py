#!/usr/bin/env python3
"""
YouTube Transcript Scraper - Neo-Skeuomorphic GUI Version
A modern, rounded interface with neo-skeuomorphic design for downloading transcripts from YouTube videos and channels.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import sys
import csv
import re
import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import queue

# External dependencies
try:
    import yt_dlp
    import whisper
    import pydub
    from pydub import AudioSegment
    import torch
except ImportError as e:
    messagebox.showerror("Missing Dependencies", f"Missing required dependency: {e}\n\nPlease install required packages using: pip install -r requirements.txt")
    sys.exit(1)


class YouTubeTranscriptGUI:
    """Neo-Skeuomorphic GUI for YouTube transcript scraping"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("WhisperTube - github.com/Pidav-Dev")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f0f0')
        self.root.resizable(True, True)
        
        # Theme / Style configuration
        self.theme_var = tk.StringVar(value="light")
        self.setup_styles()
        
        # Variables
        self.whisper_model = None
        self.model_name = "base"
        self.device = "auto"
        # Create YouTube_Transcripts folder in the program directory
        self.base_output_dir = Path(__file__).parent / "YouTube_Transcripts"
        self.setup_output_directory()
        self.current_session_dir = None
        self.keep_audio = tk.BooleanVar(value=True)
        
        # Timing variables
        self.start_time = None
        self.end_time = None
        
        # Preferences file
        self.prefs_file = Path(__file__).parent / "user_preferences.json"
        
        # Queue for thread communication
        self.log_queue = queue.Queue()
        
        # Create GUI
        self.create_widgets()
        self.setup_logging()
        
        # Load preferences after widgets are created
        self.load_preferences()
        
        # Set up preference saving when settings change
        self.setup_preference_saving()
        
        # Save preferences when window closes
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def setup_output_directory(self):
        """Setup the output directory, checking if it already exists"""
        if self.base_output_dir.exists():
            print(f"Using existing folder: {self.base_output_dir}")
        else:
            try:
                self.base_output_dir.mkdir(exist_ok=True)
                print(f"Created folder: {self.base_output_dir}")
            except Exception as e:
                print(f"Error creating folder: {e}")
                # Fallback to Desktop if program folder fails
                self.base_output_dir = Path.home() / "Desktop" / "YouTube_Transcripts"
                self.base_output_dir.mkdir(exist_ok=True)
                print(f"Fallback to Desktop: {self.base_output_dir}")
        
    def setup_styles(self):
        """Initialize ttk style and apply current theme"""
        self._style = ttk.Style()
        self._style.theme_use('clam')
        self.apply_theme(self.theme_var.get())

    def apply_theme(self, theme: str):
        """Apply light or dark theme dynamically"""
        if theme == 'dark':
            self.colors = {
                'bg_primary': '#121212',
                'bg_secondary': '#1e1e1e',
                'bg_elevated': '#232323',
                'accent_primary': '#7aa2f7',
                'accent_secondary': '#8f7af7',
                'text_primary': '#e6e6e6',
                'text_secondary': '#b0b0b0',
                'text_muted': '#8a8a8a',
                'success': '#27ae60',
                'warning': '#f39c12',
                'error': '#e74c3c',
                'shadow_light': '#2a2a2a',
                'shadow_dark': '#0a0a0a'
            }
        else:
            self.colors = {
                'bg_primary': '#f0f0f0',
                'bg_secondary': '#ffffff',
                'bg_elevated': '#f8f9fa',
                'accent_primary': '#667eea',
                'accent_secondary': '#764ba2',
                'text_primary': '#2c3e50',
                'text_secondary': '#7f8c8d',
                'text_muted': '#95a5a6',
                'success': '#27ae60',
                'warning': '#f39c12',
                'error': '#e74c3c',
                'shadow_light': '#ffffff',
                'shadow_dark': '#d1d8e0'
            }

        # Configure main window
        self.root.configure(bg=self.colors['bg_primary'])

        # Title styling
        self._style.configure('Title.TLabel',
                              background=self.colors['bg_primary'],
                              foreground=self.colors['text_primary'],
                              font=('Segoe UI', 20, 'bold'))

        # Section headers and info text
        self._style.configure('Section.TLabel', background=self.colors['bg_secondary'],
                              foreground=self.colors['text_primary'], font=('Segoe UI', 14, 'bold'))
        self._style.configure('Info.TLabel', background=self.colors['bg_secondary'],
                              foreground=self.colors['text_secondary'], font=('Segoe UI', 10))

        # Controls
        self._style.configure('Neo.TRadiobutton', background=self.colors['bg_secondary'],
                              foreground=self.colors['text_primary'], font=('Segoe UI', 11), focuscolor='none')
        self._style.configure('Neo.TButton', background=self.colors['accent_primary'], foreground='#ffffff',
                              font=('Segoe UI', 11, 'bold'), focuscolor='none', borderwidth=0)
        self._style.map('Neo.TButton', background=[('active', self.colors['accent_secondary']),
                                                   ('pressed', self.colors['accent_secondary'])])
        self._style.configure('Neo.TFrame', background=self.colors['bg_secondary'], relief='flat', borderwidth=0)
        self._style.configure('Neo.TLabelframe', background=self.colors['bg_secondary'],
                              foreground=self.colors['text_primary'], font=('Segoe UI', 12, 'bold'),
                              relief='flat', borderwidth=0)
        self._style.configure('Neo.TLabelframe.Label', background=self.colors['bg_secondary'],
                              foreground=self.colors['text_primary'], font=('Segoe UI', 12, 'bold'))
        self._style.configure('Neo.TEntry', fieldbackground=self.colors['bg_elevated'],
                              foreground=self.colors['text_primary'], font=('Segoe UI', 10), borderwidth=0, relief='flat')
        self._style.configure('Neo.TCombobox', fieldbackground=self.colors['bg_elevated'],
                              foreground=self.colors['text_primary'], font=('Segoe UI', 10), borderwidth=0, relief='flat')
        self._style.configure('Neo.TSpinbox', fieldbackground=self.colors['bg_elevated'],
                              foreground=self.colors['text_primary'], font=('Segoe UI', 10), borderwidth=0, relief='flat')
        self._style.configure('Neo.TCheckbutton', background=self.colors['bg_secondary'],
                              foreground=self.colors['text_primary'], font=('Segoe UI', 10), focuscolor='none')

        # Update log widget colors if it exists
        if hasattr(self, 'log_text') and self.log_text is not None:
            try:
                self.log_text.configure(bg=self.colors['bg_elevated'], fg=self.colors['text_primary'])
            except Exception:
                pass
    
    def create_widgets(self):
        """Create all GUI widgets with simplified, scrollable design"""
        # Main container
        main_frame = ttk.Frame(self.root, style='Neo.TFrame', padding=20)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Title with modern styling
        title_label = ttk.Label(main_frame, text="🎬 WhisperTube", style='Title.TLabel')
        title_label.pack(pady=(0, 15))
        
        # Warning banner (compact)
        warning_label = ttk.Label(main_frame, 
                                 text="⚠️ Start with 5-10 videos for testing (AI transcription takes time)", 
                                 style='Info.TLabel',
                                 foreground=self.colors['warning'])
        warning_label.pack(pady=(0, 15))
        
        # Create a two-column layout for better space usage
        self.create_main_content(main_frame)
        
        # Progress Log (always visible at bottom)
        self.create_progress_log(main_frame)
    
    def create_main_content(self, parent):
        """Create the main content in a compact two-column layout"""
        # Main content frame
        content_frame = ttk.Frame(parent, style='Neo.TFrame')
        content_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Left column
        left_column = ttk.Frame(content_frame, style='Neo.TFrame')
        left_column.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        # Right column  
        right_column = ttk.Frame(content_frame, style='Neo.TFrame')
        right_column.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        # Theme toggle (top-right)
        theme_frame = ttk.Frame(content_frame, style='Neo.TFrame')
        theme_frame.pack(side='top', anchor='ne', pady=(0, 8))
        ttk.Label(theme_frame, text="Theme:", style='Info.TLabel').pack(side='left', padx=(0, 6))
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var,
                                   values=["light", "dark"], state='readonly',
                                   width=8, style='Neo.TCombobox')
        theme_combo.pack(side='right')
        theme_combo.bind('<<ComboboxSelected>>', lambda e: self.on_theme_change())

        # Left column content
        self.create_transcription_section(left_column)
        self.create_ai_settings_section(left_column)
        
        # Right column content
        self.create_save_folder_section(right_column)
        self.create_url_section(right_column)
        
        # Control buttons (full width)
        self.create_control_buttons(parent)
    
    def create_transcription_section(self, parent):
        """Create transcription method selection with compact design"""
        section_frame = ttk.LabelFrame(parent, text="🎯 Method", style='Neo.TLabelframe', padding=10)
        section_frame.pack(fill='x', pady=(0, 10))
        
        self.transcription_method = tk.StringVar(value="ai_only")
        
        # Compact radio buttons
        ttk.Radiobutton(section_frame, 
                       text="🚀 API First (Recommended)", 
                       variable=self.transcription_method, 
                       value="api_first",
                       style='Neo.TRadiobutton').pack(anchor='w', pady=2)
        
        ttk.Radiobutton(section_frame, 
                       text="🤖 AI Only (Whisper)", 
                       variable=self.transcription_method, 
                       value="ai_only",
                       style='Neo.TRadiobutton').pack(anchor='w', pady=2)
        
        ttk.Radiobutton(section_frame, 
                       text="⚡ API Only (Fast)", 
                       variable=self.transcription_method, 
                       value="api_only",
                       style='Neo.TRadiobutton').pack(anchor='w', pady=2)
    
    def create_ai_settings_section(self, parent):
        """Create AI transcription settings with compact design"""
        section_frame = ttk.LabelFrame(parent, text="🤖 AI Settings", style='Neo.TLabelframe', padding=10)
        section_frame.pack(fill='x', pady=(0, 10))
        
        # Whisper Model
        model_frame = ttk.Frame(section_frame, style='Neo.TFrame')
        model_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(model_frame, text="Model:", style='Info.TLabel').pack(side='left')
        
        self.whisper_model_var = tk.StringVar(value="base")
        model_combo = ttk.Combobox(model_frame, 
                                  textvariable=self.whisper_model_var,
                                  values=["tiny", "base", "small", "medium", "large-v3"],
                                  state="readonly",
                                  width=12,
                                  style='Neo.TCombobox')
        model_combo.pack(side='right')
        
        # Device
        device_frame = ttk.Frame(section_frame, style='Neo.TFrame')
        device_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(device_frame, text="Device:", style='Info.TLabel').pack(side='left')
        
        self.device_var = tk.StringVar(value="auto")
        device_combo = ttk.Combobox(device_frame, 
                                   textvariable=self.device_var,
                                   values=["auto", "cpu", "cuda"],
                                   state="readonly",
                                   width=12,
                                   style='Neo.TCombobox')
        device_combo.pack(side='right')
        
        # Compact model guide
        guide_text = "tiny=fast, base=balanced, small=accurate, medium/large=best"
        guide_label = ttk.Label(section_frame, text=guide_text, style='Info.TLabel', justify='left')
        guide_label.pack(anchor='w', pady=(5, 0))
    
    def create_save_folder_section(self, parent):
        """Create save folder selection with compact design"""
        section_frame = ttk.LabelFrame(parent, text="📁 Save Folder", style='Neo.TLabelframe', padding=10)
        section_frame.pack(fill='x', pady=(0, 10))
        
        folder_frame = ttk.Frame(section_frame, style='Neo.TFrame')
        folder_frame.pack(fill='x', pady=(0, 8))
        
        self.folder_var = tk.StringVar(value=str(self.base_output_dir))
        folder_entry = ttk.Entry(folder_frame, textvariable=self.folder_var, width=30, style='Neo.TEntry')
        folder_entry.pack(side='left', fill='x', expand=True, padx=(0, 8))
        
        ttk.Button(folder_frame, 
                  text="📂 Browse", 
                  command=self.browse_folder,
                  style='Neo.TButton').pack(side='right')
        
        # Keep audio files checkbox
        ttk.Checkbutton(section_frame, 
                       text="💾 Keep audio files", 
                       variable=self.keep_audio,
                       style='Neo.TCheckbutton').pack(anchor='w', pady=(5, 0))
    
    def create_url_section(self, parent):
        """Create URL input section with compact design"""
        section_frame = ttk.LabelFrame(parent, text="🔗 URL", style='Neo.TLabelframe', padding=10)
        section_frame.pack(fill='x', pady=(0, 10))
        
        # URL input
        self.url_var = tk.StringVar()
        url_entry = ttk.Entry(section_frame, textvariable=self.url_var, width=40, style='Neo.TEntry')
        url_entry.pack(fill='x', pady=(0, 8))
        
        # Content type selection
        content_frame = ttk.Frame(section_frame, style='Neo.TFrame')
        content_frame.pack(fill='x', pady=(0, 8))
        
        ttk.Label(content_frame, text="Content type:", style='Info.TLabel').pack(side='left')
        
        self.content_type = tk.StringVar(value="videos")
        content_combo = ttk.Combobox(content_frame, 
                                    textvariable=self.content_type,
                                    values=["videos", "shorts", "both"],
                                    state="readonly",
                                    width=10,
                                    style='Neo.TCombobox')
        content_combo.pack(side='right')
        
        # Video count for channels
        count_frame = ttk.Frame(section_frame, style='Neo.TFrame')
        count_frame.pack(fill='x')
        
        ttk.Label(count_frame, text="Videos to scrape:", style='Info.TLabel').pack(side='left')
        
        self.video_count_var = tk.StringVar(value="10")
        count_spinbox = ttk.Spinbox(count_frame, 
                                   from_=1, 
                                   to=100, 
                                   textvariable=self.video_count_var,
                                   width=8,
                                   style='Neo.TSpinbox')
        count_spinbox.pack(side='right')
    
    def create_control_buttons(self, parent):
        """Create control buttons with compact design"""
        button_frame = ttk.Frame(parent, style='Neo.TFrame')
        button_frame.pack(fill='x', pady=(0, 10))
        
        # Compact action buttons
        self.start_button = ttk.Button(button_frame, 
                                      text="🚀 Start", 
                                      command=self.start_scraping,
                                      style='Neo.TButton')
        self.start_button.pack(side='left', padx=(0, 8))
        
        self.stop_button = ttk.Button(button_frame, 
                                     text="⏹️ Stop", 
                                     command=self.stop_scraping,
                                     style='Neo.TButton',
                                     state='disabled')
        self.stop_button.pack(side='left', padx=(0, 8))
        
        self.clear_button = ttk.Button(button_frame, 
                                      text="🗑️ Clear", 
                                      command=self.clear_log,
                                      style='Neo.TButton')
        self.clear_button.pack(side='right')
    
    def create_progress_log(self, parent):
        """Create progress log section with compact design"""
        section_frame = ttk.LabelFrame(parent, text="📊 Progress Log", style='Neo.TLabelframe', padding=10)
        section_frame.pack(fill='both', expand=True, pady=(10, 0))
        
        # Compact log text area
        self.log_text = scrolledtext.ScrolledText(section_frame, 
                                                 height=8, 
                                                 bg=self.colors['bg_elevated'], 
                                                 fg=self.colors['text_primary'],
                                                 font=('Consolas', 9),
                                                 wrap='word',
                                                 relief='flat',
                                                 borderwidth=0,
                                                 highlightthickness=0)
        self.log_text.pack(fill='both', expand=True)
    
    def setup_logging(self):
        """Setup logging system"""
        self.check_log_queue()
    
    def log_message(self, message):
        """Add message to log queue"""
        self.log_queue.put(message)
    
    def format_duration(self, seconds):
        """Format duration in a human-readable way"""
        if seconds < 60:
            return f"{seconds:.1f} seconds"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f} minutes"
        else:
            hours = seconds / 3600
            return f"{hours:.1f} hours"
    
    def save_preferences(self):
        """Save user preferences to file"""
        try:
            prefs = {
                "output_directory": str(self.base_output_dir),
                "whisper_model": self.whisper_model_var.get(),
                "device": self.device_var.get(),
                "transcription_method": self.transcription_method.get(),
                "content_type": self.content_type.get(),
                "theme": self.theme_var.get(),
                "video_count": self.video_count_var.get(),
                "keep_audio": self.keep_audio.get()
            }
            
            with open(self.prefs_file, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, indent=2)
                
        except Exception as e:
            self.log_message(f"⚠️ Could not save preferences: {e}")
    
    def load_preferences(self):
        """Load user preferences from file"""
        try:
            if self.prefs_file.exists():
                with open(self.prefs_file, 'r', encoding='utf-8') as f:
                    prefs = json.load(f)
                
                # Apply loaded preferences
                if "output_directory" in prefs:
                    self.base_output_dir = Path(prefs["output_directory"])
                    self.folder_var.set(str(self.base_output_dir))
                
                if "whisper_model" in prefs:
                    self.whisper_model_var.set(prefs["whisper_model"])
                
                if "device" in prefs:
                    self.device_var.set(prefs["device"])
                
                if "transcription_method" in prefs:
                    self.transcription_method.set(prefs["transcription_method"])
                
                if "content_type" in prefs:
                    self.content_type.set(prefs["content_type"])
                
                if "theme" in prefs:
                    self.theme_var.set(prefs["theme"])
                    self.apply_theme(self.theme_var.get())
                
                if "video_count" in prefs:
                    self.video_count_var.set(prefs["video_count"])
                
                if "keep_audio" in prefs:
                    self.keep_audio.set(prefs["keep_audio"])
                
                self.log_message("✅ Preferences loaded successfully")
                
        except Exception as e:
            self.log_message(f"⚠️ Could not load preferences: {e}")
            # Use defaults if loading fails
    
    def on_closing(self):
        """Handle window closing - save preferences and close"""
        self.save_preferences()
        self.root.destroy()
    
    def setup_preference_saving(self):
        """Set up automatic preference saving when settings change"""
        # Add trace callbacks to save preferences when values change
        self.whisper_model_var.trace('w', lambda *args: self.save_preferences())
        self.device_var.trace('w', lambda *args: self.save_preferences())
        self.transcription_method.trace('w', lambda *args: self.save_preferences())
        self.content_type.trace('w', lambda *args: self.save_preferences())
        self.video_count_var.trace('w', lambda *args: self.save_preferences())
        self.keep_audio.trace('w', lambda *args: self.save_preferences())
        self.theme_var.trace('w', lambda *args: (self.apply_theme(self.theme_var.get()), self.save_preferences()))

    def on_theme_change(self):
        """Handle theme change from UI control"""
        self.apply_theme(self.theme_var.get())
        self.save_preferences()
    
    def check_log_queue(self):
        """Check and process log queue"""
        try:
            while True:
                message = self.log_queue.get_nowait()
                timestamp = datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] {message}\n"
                self.log_text.insert(tk.END, formatted_message)
                self.log_text.see(tk.END)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.check_log_queue)
    
    def clear_log(self):
        """Clear the progress log"""
        self.log_text.delete(1.0, tk.END)
    
    def browse_folder(self):
        """Browse for save folder"""
        folder = filedialog.askdirectory(initialdir=str(self.base_output_dir))
        if folder:
            self.folder_var.set(folder)
            self.base_output_dir = Path(folder)
            self.save_preferences()  # Save preferences when folder changes
    
    def start_scraping(self):
        """Start the scraping process"""
        url = self.url_var.get().strip()
        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL")
            return
        
        # Update UI
        self.start_button.config(state='disabled')
        self.stop_button.config(state='normal')
        
        # Start scraping in separate thread
        self.scraping_thread = threading.Thread(target=self.run_scraping, daemon=True)
        self.scraping_thread.start()
    
    def stop_scraping(self):
        """Stop the scraping process"""
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
        self.log_message("❌ Scraping stopped by user")
    
    def run_scraping(self):
        """Run the actual scraping process"""
        try:
            # Start timing
            self.start_time = time.time()
            self.log_message(f"⏰ Started at: {datetime.now().strftime('%H:%M:%S')}")
            
            url = self.url_var.get().strip()
            video_count = int(self.video_count_var.get())
            
            # Load Whisper model
            model_name = self.whisper_model_var.get()
            self.log_message(f"Loading Whisper model: {model_name}")
            
            if not self.load_whisper_model(model_name):
                self.log_message("❌ Failed to load Whisper model")
                return
            
            # Determine if it's a single video or channel
            if self.is_channel_url(url):
                self.scrape_channel(url, video_count)
            else:
                self.scrape_single_video(url)
                
        except Exception as e:
            self.log_message(f"❌ Error during scraping: {str(e)}")
        finally:
            # End timing and display duration
            self.end_time = time.time()
            if self.start_time:
                duration = self.end_time - self.start_time
                self.log_message(f"⏱️ Total time taken: {self.format_duration(duration)}")
                self.log_message(f"⏰ Finished at: {datetime.now().strftime('%H:%M:%S')}")
            
            self.root.after(0, self.reset_buttons)
    
    def reset_buttons(self):
        """Reset button states"""
        self.start_button.config(state='normal')
        self.stop_button.config(state='disabled')
    
    def is_channel_url(self, url):
        """Check if URL is a channel URL"""
        channel_patterns = [
            r'youtube\.com/channel/',
            r'youtube\.com/c/',
            r'youtube\.com/@',
            r'youtube\.com/user/'
        ]
        return any(re.search(pattern, url) for pattern in channel_patterns)
    
    def create_session_folder(self, channel_name=None, is_single_video=False):
        """Create organized folder structure for scraping session"""
        # Use MM/DD/YY format for date
        now = datetime.now()
        date_str = now.strftime("%m_%d_%y")
        time_str = now.strftime("%H%M%S")
        timestamp = f"{date_str}_{time_str}"
        
        if is_single_video:
            # For single videos, we need to get the channel name from the video
            if channel_name and channel_name != "single_video":
                clean_name = re.sub(r'[<>:"/\\|?*]', '_', channel_name)
                session_name = f"single_video_{clean_name}_{timestamp}"
            else:
                session_name = f"single_video_unknown_{timestamp}"
        elif channel_name:
            # Clean channel name for folder name
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', channel_name)
            session_name = f"channel_{clean_name}_{timestamp}"
        else:
            session_name = f"session_{timestamp}"
        
        self.current_session_dir = self.base_output_dir / session_name
        self.current_session_dir.mkdir(exist_ok=True)
        
        self.log_message(f"📁 Created session folder: {self.current_session_dir.name}")
        return self.current_session_dir
    
    def create_video_folder(self, video_id, video_title):
        """Create individual folder for each video"""
        # Clean video title for folder name
        clean_title = re.sub(r'[<>:"/\\|?*]', '_', video_title)
        clean_title = clean_title[:50]  # Limit length
        video_folder_name = f"{video_id}_{clean_title}"
        
        video_folder = self.current_session_dir / video_folder_name
        video_folder.mkdir(exist_ok=True)
        
        return video_folder
    
    def extract_channel_name(self, channel_url):
        """Extract channel name from URL"""
        try:
            # Try to get channel name from URL
            if '@' in channel_url:
                return channel_url.split('@')[-1].split('/')[0]
            elif '/c/' in channel_url:
                return channel_url.split('/c/')[-1].split('/')[0]
            elif '/user/' in channel_url:
                return channel_url.split('/user/')[-1].split('/')[0]
            elif '/channel/' in channel_url:
                return f"channel_{channel_url.split('/channel/')[-1].split('/')[0]}"
            else:
                return "unknown_channel"
        except:
            return "unknown_channel"
    
    def save_video_metadata(self, video_id, video_folder):
        """Save video metadata to video folder"""
        try:
            video_info = self.get_video_info(video_id)
            metadata_file = video_folder / f"{video_id}_metadata.txt"
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                f.write(f"Video ID: {video_id}\n")
                f.write(f"Title: {video_info['title']}\n")
                f.write(f"View Count: {video_info['view_count']:,}\n")
                f.write(f"Duration: {video_info['duration']} seconds\n")
                f.write(f"Uploader: {video_info['uploader']}\n")
                f.write(f"Upload Date: {video_info['upload_date']}\n")
                f.write(f"Description: {video_info['description']}\n")
                f.write(f"Video URL: https://www.youtube.com/watch?v={video_id}\n")
                f.write(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            self.log_message(f"💾 Saved metadata to: {metadata_file.name}")
            
        except Exception as e:
            self.log_message(f"⚠️ Could not save metadata: {e}")
    
    def load_whisper_model(self, model_name):
        """Load Whisper model"""
        try:
            self.whisper_model = whisper.load_model(model_name)
            self.model_name = model_name
            self.log_message(f"✅ Whisper model '{model_name}' loaded successfully")
            return True
        except Exception as e:
            self.log_message(f"❌ Error loading Whisper model: {e}")
            return False
    
    def extract_video_id(self, url):
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
    
    def get_video_info(self, video_id):
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
                    'uploader': info.get('uploader', 'Unknown'),
                    'upload_date': info.get('upload_date', ''),
                    'description': info.get('description', '')[:200] + '...' if info.get('description') else ''
                }
        except Exception as e:
            self.log_message(f"Error getting video info: {e}")
            return {
                'title': 'Unknown Title',
                'view_count': 0,
                'duration': 0,
                'uploader': 'Unknown',
                'upload_date': '',
                'description': ''
            }
    
    def download_audio(self, video_id, video_folder):
        """Download audio from YouTube video to organized folder"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': str(video_folder / f'{video_id}.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                url = f"https://www.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(url, download=True)
                
                # Find the downloaded file in the video folder
                filename = ydl.prepare_filename(info)
                if os.path.exists(filename):
                    return filename
                
                # Try different extensions in the video folder
                for ext in ['webm', 'm4a', 'mp3', 'wav']:
                    test_file = video_folder / f"{video_id}.{ext}"
                    if test_file.exists():
                        return str(test_file)
                
                return None
                
        except Exception as e:
            self.log_message(f"Error downloading audio: {e}")
            return None
    
    def whisper_transcribe(self, audio_file):
        """Convert audio file to text using Whisper AI"""
        try:
            if not self.whisper_model:
                return ""
            
            # Load and process audio with Whisper
            result = self.whisper_model.transcribe(audio_file)
            
            # Extract text from result
            transcript_text = result["text"].strip()
            return transcript_text
            
        except Exception as e:
            self.log_message(f"Error in Whisper transcription: {e}")
            return ""
    
    def get_transcript(self, video_id, video_folder):
        """Get transcript for a video"""
        try:
            video_start_time = time.time()
            self.log_message(f"🤖 AI transcribing {video_id}...")
            
            # Download audio from video to organized folder
            audio_file = self.download_audio(video_id, video_folder)
            if not audio_file:
                return "", "Failed to download audio from video"
            
            # Convert audio to text using Whisper
            transcript_text = self.whisper_transcribe(audio_file)
            
            # Save transcript to video folder
            if transcript_text:
                transcript_file = video_folder / f"{video_id}_transcript.txt"
                with open(transcript_file, 'w', encoding='utf-8') as f:
                    f.write(transcript_text)
                self.log_message(f"💾 Saved transcript to: {transcript_file.name}")
            
            # Save video metadata to video folder
            self.save_video_metadata(video_id, video_folder)
            
            # Clean up audio file if user doesn't want to keep it
            if not self.keep_audio.get() and os.path.exists(audio_file):
                os.remove(audio_file)
                self.log_message(f"🗑️ Cleaned up audio file")
            elif self.keep_audio.get():
                self.log_message(f"💾 Kept audio file: {Path(audio_file).name}")
            
            # Calculate and display video processing time
            video_duration = time.time() - video_start_time
            
            if transcript_text:
                char_count = len(transcript_text)
                self.log_message(f"✅ AI transcribed {video_id}: {char_count} chars ({self.format_duration(video_duration)})")
                return transcript_text, f"AI Generated (Whisper {self.model_name})"
            else:
                self.log_message(f"❌ Failed to transcribe {video_id} ({self.format_duration(video_duration)})")
                return "", "Could not generate transcript from audio"
                
        except Exception as e:
            video_duration = time.time() - video_start_time if 'video_start_time' in locals() else 0
            self.log_message(f"❌ Error transcribing {video_id}: {str(e)[:100]} ({self.format_duration(video_duration)})")
            return "", f"Error generating transcript: {str(e)[:100]}"
    
    def scrape_single_video(self, url):
        """Scrape transcript for a single video"""
        video_id = self.extract_video_id(url)
        if not video_id:
            self.log_message("❌ Invalid YouTube URL")
            return
        
        # Get video info
        video_info = self.get_video_info(video_id)
        self.log_message(f"Processing: {video_info['title'][:50]}...")
        
        # Extract channel name from video info
        channel_name = video_info.get('uploader', 'unknown')
        if not channel_name or channel_name == 'Unknown':
            channel_name = 'unknown'
        
        # Create session folder for single video with channel name
        self.create_session_folder(channel_name, is_single_video=True)
        
        # Create video folder
        video_folder = self.create_video_folder(video_id, video_info['title'])
        
        # Get transcript
        transcript_text, transcript_type = self.get_transcript(video_id, video_folder)
        
        if transcript_text:
            self.log_message(f"✅ Transcript generated: {len(transcript_text)} characters")
            self.log_message(f"📁 Files saved to: {video_folder}")
        else:
            self.log_message(f"❌ Failed to generate transcript: {transcript_type}")
        
        # Display single video timing
        if self.start_time:
            single_video_duration = time.time() - self.start_time
            self.log_message(f"⏱️ Single video processing time: {self.format_duration(single_video_duration)}")
    
    def scrape_channel(self, channel_url, max_videos):
        """Scrape transcripts for multiple videos in a channel"""
        try:
            content_type = self.content_type.get()
            self.log_message(f"🚀 Starting Advanced Scraping...")
            self.log_message(f"📺 Content type: {content_type.title()}")
            
            # Get channel videos
            video_ids = self.get_channel_videos(channel_url, max_videos, content_type)
            
            if not video_ids:
                self.log_message("❌ No videos found or error accessing channel")
                return
            
            self.log_message(f"Found {len(video_ids)} videos to process")
            
            # Get channel name for folder
            channel_name = self.extract_channel_name(channel_url)
            
            # Create session folder
            self.create_session_folder(channel_name, is_single_video=False)
            
            # Create CSV file in session folder
            now = datetime.now()
            date_str = now.strftime("%m_%d_%y")
            time_str = now.strftime("%H%M%S")
            timestamp = f"{date_str}_{time_str}"
            csv_filename = f"youtube_transcripts_{timestamp}.csv"
            csv_path = self.current_session_dir / csv_filename
            
            # Process videos
            processed_count = 0
            successful_count = 0
            
            with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = [
                    'Title', 'Video URL', 'View Count', 'Duration (seconds)', 
                    'Uploader', 'Upload Date', 'Description', 'Transcript', 
                    'Transcript Type', 'Character Count', 'Processing Date'
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for i, video_id in enumerate(video_ids, 1):
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    
                    # Get video info
                    video_info = self.get_video_info(video_id)
                    self.log_message(f"[{i}/{len(video_ids)}] Processing: {video_info['title'][:50]}...")
                    
                    # Create video folder
                    video_folder = self.create_video_folder(video_id, video_info['title'])
                    
                    # Get transcript
                    transcript_text, transcript_type = self.get_transcript(video_id, video_folder)
                    
                    # Calculate duration in minutes:seconds
                    duration_seconds = video_info['duration']
                    duration_formatted = f"{duration_seconds // 60}:{duration_seconds % 60:02d}" if duration_seconds > 0 else "Unknown"
                    
                    # Write to CSV with enhanced data
                    writer.writerow({
                        'Title': video_info['title'],
                        'Video URL': video_url,
                        'View Count': video_info['view_count'],
                        'Duration (seconds)': duration_formatted,
                        'Uploader': video_info['uploader'],
                        'Upload Date': video_info['upload_date'],
                        'Description': video_info['description'],
                        'Transcript': transcript_text if transcript_text else f"[{transcript_type}]",
                        'Transcript Type': transcript_type,
                        'Character Count': len(transcript_text) if transcript_text else 0,
                        'Processing Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                    
                    processed_count += 1
                    if transcript_text:
                        successful_count += 1
                    
                    self.log_message("")  # Empty line for spacing
            
            # Final results
            self.log_message("SCRAPING COMPLETED! 🎉")
            self.log_message("📊 Results:")
            self.log_message(f"• Total videos processed: {processed_count}")
            self.log_message(f"• Transcripts found: {successful_count}/{processed_count} ({(successful_count/processed_count)*100:.1f}%)")
            self.log_message(f"• CSV saved: {csv_path.name}")
            self.log_message(f"• Session folder: {self.current_session_dir}")
            self.log_message(f"• Individual video folders: {processed_count}")
            if self.keep_audio.get():
                self.log_message(f"• Audio files kept: {successful_count}")
            
            # Calculate and display timing statistics
            if self.start_time:
                total_duration = time.time() - self.start_time
                avg_time_per_video = total_duration / processed_count if processed_count > 0 else 0
                self.log_message(f"⏱️ Total processing time: {self.format_duration(total_duration)}")
                self.log_message(f"⏱️ Average time per video: {self.format_duration(avg_time_per_video)}")
            
            self.log_message("")  # Empty line for spacing
            
        except Exception as e:
            self.log_message(f"❌ Error during channel scraping: {str(e)}")
    
    def get_channel_videos(self, channel_url, max_videos, content_type="videos"):
        """Get list of video IDs from a channel"""
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,
                'playlist_items': f'1:{max_videos}',
            }
            
            # Build URL based on channel type and content type
            if 'youtube.com/channel/' in channel_url or 'youtube.com/c/' in channel_url or 'youtube.com/@' in channel_url:
                channel_url = channel_url.rstrip('/')
                
                if content_type == "shorts":
                    # Try shorts tab first
                    if channel_url.endswith('/shorts'):
                        uploads_url = channel_url
                    else:
                        uploads_url = f"{channel_url}/shorts"
                elif content_type == "videos":
                    # Try videos tab
                    if channel_url.endswith('/videos'):
                        uploads_url = channel_url
                    else:
                        uploads_url = f"{channel_url}/videos"
                else:  # both
                    # Try videos tab first, fallback to shorts if needed
                    if channel_url.endswith('/videos'):
                        uploads_url = channel_url
                    else:
                        uploads_url = f"{channel_url}/videos"
            else:
                uploads_url = channel_url
            
            video_ids = []
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                try:
                    info = ydl.extract_info(uploads_url, download=False)
                    
                    if 'entries' in info:
                        for entry in info['entries'][:max_videos]:
                            if entry and entry.get('id'):
                                video_ids.append(entry['id'])
                except Exception as e:
                    # If videos tab fails and we're trying "both", try shorts
                    if content_type == "both" and "videos tab" in str(e).lower():
                        self.log_message("📹 Videos tab not available, trying shorts...")
                        try:
                            shorts_url = f"{channel_url.rstrip('/')}/shorts"
                            info = ydl.extract_info(shorts_url, download=False)
                            
                            if 'entries' in info:
                                for entry in info['entries'][:max_videos]:
                                    if entry and entry.get('id'):
                                        video_ids.append(entry['id'])
                        except Exception as shorts_error:
                            self.log_message(f"❌ Shorts also not available: {shorts_error}")
                            raise e
                    else:
                        raise e
                
            return video_ids
            
        except Exception as e:
            self.log_message(f"Error getting channel videos: {e}")
            return []


def main():
    """Main function"""
    root = tk.Tk()
    app = YouTubeTranscriptGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
