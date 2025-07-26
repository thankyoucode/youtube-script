import streamlit as st
import os
import threading
import time
from yt_dlp import YoutubeDL
from src.transcript import YTTranscriptText
from src.video_info import show_video_info
from src.show_downloads import show_downloads
from src.audio_video import AudioVideoDownloader
# --- Config (Change these paths as per your folders) ---
VIDEO_DIR = "downloads/video"
AUDIO_DIR = "downloads/audio"
TRANSCRIPT_DIR = "downloads/transcript"
TEMP_DIR = "downloads/.temp"

# Create dirs if not exist
for d in [AUDIO_DIR, VIDEO_DIR, TRANSCRIPT_DIR, TEMP_DIR]:
    os.makedirs(d, exist_ok=True)

# --- UI layout ---
st.title("YouTube Downloader & Transcript Viewer")
st.markdown("A simple and easy-to-use YouTube downloader with transcript reading capabilities.")

# YouTube URL input
youtube_url = st.text_input("Enter YouTube URL", "")

if youtube_url:
    ydl_opts = {
            'quiet': True,
            'skip_download': True,
        }

    info = None

    with YoutubeDL(ydl_opts) as ydl:
        # Extract video info
        try:
            info = ydl.extract_info(youtube_url, download=False)
        except Exception as e:
            st.error(f"Error fetching video info: {e}")
            info = None

    if info:
        show_video_info(st, info)
        
        downloader = AudioVideoDownloader(
            url=youtube_url,
            video_dir=VIDEO_DIR,
            audio_dir=AUDIO_DIR,
            info=info,
            audio_only=False,
            temp_dir=TEMP_DIR
        )

        # Prepare options and labels for user selection
        video_audio_combos = downloader.get_video_audio_combinations()
        video_labels = [f"{combo.get('height') or 0}p {combo.get('ext_video')} - "
                        f"{combo.get('size') / (1024*1024):.2f} MB"
                        for combo in video_audio_combos]
        
        audio_options = downloader.get_audio_options()
        audio_labels = [f"{opt.get('abr') or 0} kbps ({opt.get('ext')}) - "
                        f"{(opt.get('filesize') or opt.get('filesize_approx') or 0) / (1024*1024):.2f} MB"
                        for opt in audio_options]



        # Two columns for option selection
        col1, col2 = st.columns(2)
        with col1:
            video_choice_idx = None
            if video_labels:
                video_choice = st.selectbox("Select Video Quality", video_labels)
                video_choice_idx = video_labels.index(video_choice)
            else:
                st.write("No video combinations available.")

            

        with col2:
            audio_choice_idx = None
            if audio_labels:
                audio_choice = st.selectbox("Select Audio Quality", audio_labels)
                audio_choice_idx = audio_labels.index(audio_choice)
            else:
                st.write("No audio-only options available.")
            
        # Download buttons layout
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        with btn_col1:
            download_video_btn = st.button("Download Video")
        with btn_col2:
            download_audio_btn = st.button("Download Audio")
        with btn_col3:
            download_transcript_btn = st.button("Download Transcript")

        # Placeholders for status/progress updates
        status_placeholder = st.empty()
        progress_placeholder = st.empty()

        # Connect UI callbacks directly to the downloader callbacks
        downloader.progress_hook = lambda stage, stats: progress_placeholder.progress(
            int(stats.get('percent', 0))) or status_placeholder.text(
                f"{stage.capitalize()} Downloading: "
                f"{stats.get('downloaded', 0) / 1024 / 1024:.2f} / {stats.get('total', 0) / 1024 / 1024:.2f} MB "
                f"({stats.get('percent', 0):.1f}%) @ {(stats.get('speed', 0) or 0) / 1024:.1f} KiB/s")

        def status_cb(stage, status):
            status_map = {
                "downloading": f"{stage.capitalize()} Downloading...",
                "completed": f"{stage.capitalize()} Download Complete.",
                "merging": "Merging Audio and Video...",
                "processing": "Post-processing...",
            }
            msg = status_map.get(status, f"{stage}: {status}")
            status_placeholder.text(msg)
            if status == "completed":
                progress_placeholder.progress(100)
        downloader.status_callback = status_cb

        # Button triggers call class methods with selected options, minimal logic here
        if download_video_btn:
            if video_choice_idx is not None and 0 <= video_choice_idx < len(video_audio_combos):
                status_placeholder.text("Starting video + audio download...")
                path = downloader.download_video_with_audio(video_audio_combos[video_choice_idx])
                status_placeholder.success(f"Video+Audio downloaded: {path}")
                progress_placeholder.progress(100)
            else:
                st.warning("Please select a valid video + audio option.")

        if download_audio_btn:
            if audio_choice_idx is not None and 0 <= audio_choice_idx < len(audio_options):
                status_placeholder.text("Starting audio download...")
                path = downloader.download_audio(audio_options[audio_choice_idx])
                status_placeholder.success(f"Audio downloaded: {path}")
                progress_placeholder.progress(100)
            else:
                st.warning("Please select a valid audio option.")

        if download_transcript_btn:
            status_placeholder.text("Downloading transcript...")
            progress_placeholder.progress(0)

            yt_transcript = YTTranscriptText(youtube_url, TRANSCRIPT_DIR)
            download_thread = threading.Thread(target=yt_transcript.download)
            download_thread.start()

            # Example fake-progress animation while the thread runs 
            progress = 0
            while download_thread.is_alive():
                progress = (progress + 1) % 100
                progress_placeholder.progress(progress)
                time.sleep(0.3)

            progress_placeholder.progress(100)
            status_placeholder.text("Transcript downloaded successfully!")


# Status and progress bar placeholders
status_placeholder = st.empty()
progress_placeholder = st.empty()

# --- Show media lists from directories ---
show_downloads(st, VIDEO_DIR, AUDIO_DIR, TRANSCRIPT_DIR)