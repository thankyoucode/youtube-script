import os

def load_media_files(directory, extensions):
    files = [f for f in os.listdir(directory) if any(f.lower().endswith(ext) for ext in extensions)]
    return files

def show_downloads(st, VIDEO_DIR, AUDIO_DIR, TRANSCRIPT_DIR):
    st.header("Downloaded Video Files")
    video_files = load_media_files(VIDEO_DIR, [".mp4", ".webm", ".mkv"])
    if video_files:
        selected_video = st.selectbox("Select video to play", video_files, key="video_select")
        if selected_video:
            video_path = os.path.join(VIDEO_DIR, selected_video)
            with open(video_path, "rb") as video_file:
                video_bytes = video_file.read()
            st.video(video_bytes)
    else:
        st.info("No video files downloaded yet.")

    st.header("Downloaded Audio Files")
    audio_files = load_media_files(AUDIO_DIR, [".mp3", ".m4a", ".aac", ".wav"])
    if audio_files:
        selected_audio = st.selectbox("Select audio to play", audio_files, key="audio_select")
        if selected_audio:
            audio_path = os.path.join(AUDIO_DIR, selected_audio)
            with open(audio_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            st.audio(audio_bytes)
    else:
        st.info("No audio files downloaded yet.")

    st.header("Available Transcript Files")
    transcript_files = load_media_files(TRANSCRIPT_DIR, [".md", ".txt"])
    if transcript_files:
        selected_transcript = st.selectbox("Select transcript to view", transcript_files, key="transcript_select")
        if selected_transcript:
            transcript_path = os.path.join(TRANSCRIPT_DIR, selected_transcript)
            with open(transcript_path, "r", encoding="utf-8") as f:
                content = f.read()
            st.markdown(f"### Transcript: {selected_transcript}")
            st.markdown(content)
    else:
        st.info("No transcript files available.")
