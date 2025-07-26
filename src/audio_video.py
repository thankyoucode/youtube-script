import yt_dlp
import os
import ffmpeg
import threading

class AudioVideoDownloader:
    def __init__(
        self, url, video_dir, audio_dir, info=None,
        progress_hook=None, status_callback=None,
        audio_only=False, temp_dir="./temp"
    ):
        """
        url: string, video URL
        video_dir: path (must exist)
        audio_dir: path (must exist)
        progress_hook: function(stage, stats_dict), called for progress updates
        status_callback: function(stage, status), called for status messages
        audio_only: bool, if True only get/download audio
        temp_dir: temp path for combining, must exist
        """
        self.url = url
        self.video_dir = video_dir
        self.audio_dir = audio_dir
        self.progress_hook = progress_hook
        self.status_callback = status_callback
        self.audio_only = audio_only
        self.temp_dir = temp_dir
        self.info = info
        if not self.info:
            self.info = self.fetch_video_info()
        self.formats = self.info.get('formats', [])
        self.title = self.info.get('title', 'output').replace('/', '_').replace('\\', '_')

    def fetch_video_info(self):
        ydl_opts = {'quiet': True, 'no_warnings': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(self.url, download=False)

    def get_audio_options(self):
        auds = [f for f in self.formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
        # Bucket audio streams to common bitrates for easy menu
        newpipe_buckets = [32, 35, 48, 50, 70, 128, 160]
        bucket_map = {}
        for tier in newpipe_buckets:
            candidates = [a for a in auds if abs((a.get('abr') or 0) - tier) <= 5]
            if candidates:
                best = min(candidates, key=lambda a: a.get('filesize') or a.get('filesize_approx') or float('inf'))
                bucket_map[tier] = best
        return [bucket_map[t] for t in sorted(bucket_map.keys()) if t in bucket_map]

    def get_video_audio_combinations(self):
        # Get all video-only streams (deduplicate by height)
        vids = [f for f in self.formats if f.get('vcodec') != 'none' and f.get('acodec') == 'none']
        unique_vids = {}
        for f in sorted(vids, key=lambda x: (x.get('height') or 0)):
            h = f.get('height')
            size = f.get('filesize') or f.get('filesize_approx')
            if h and h not in unique_vids and size:
                unique_vids[h] = f
        vids = list(unique_vids.values())
        auds = self.get_audio_options()
        # Pair each video stream with the closest-quality audio
        def best_audio_for_video(h):
            target_abr = 48 + (h / 1080) * (160 - 48)
            closest = min(auds, key=lambda a: abs((a.get('abr') or 0) - target_abr), default=None)
            return closest
        combinations = []
        for v in vids:
            a = best_audio_for_video(v.get('height') or 0)
            v_size = v.get('filesize') or v.get('filesize_approx') or 0
            a_size = (a.get('filesize') or a.get('filesize_approx') or 0) if a else 0
            combinations.append({
                'video': v,
                'audio': a,
                'height': v.get('height'),
                'abr': a.get('abr') if a else None,
                'ext_video': v.get('ext'),
                'ext_audio': a.get('ext') if a else None,
                'size': v_size + a_size
            })
        return combinations

    def download_audio(self, option):
        """
        Downloads audio (option from get_audio_options), updates progress.
        Returns output path.
        """
        a_fmt = option['format_id']
        ext = option['ext']
        output_path = os.path.join(self.audio_dir, f"{self.title}_{option.get('abr')}kbps.{ext}")
        self._call_status("audio", "downloading")
        self._download_stream(a_fmt, output_path, stage="audio")
        self._call_status("audio", "completed")
        return output_path

    def download_video_with_audio(self, combination_option):
        """
        Downloads/merges video+audio (option from get_video_audio_combinations).
        Returns output path.
        """
        v_fmt = combination_option['video']['format_id']
        a_fmt = combination_option['audio']['format_id']
        ext_v = combination_option['ext_video']
        ext_a = combination_option['ext_audio']
        video_temp_path = os.path.join(self.temp_dir, f"{self.title}.video.{ext_v}")
        audio_temp_path = os.path.join(self.temp_dir, f"{self.title}.audio.{ext_a}")
        output_path = os.path.join(
            self.video_dir,
            f"{self.title}_{combination_option['height']}p_{combination_option['abr']}kbps.{ext_v}")
        self._call_status("video", "downloading")
        self._download_stream(v_fmt, video_temp_path, stage="video")
        self._call_status("video", "completed")
        self._call_status("audio", "downloading")
        self._download_stream(a_fmt, audio_temp_path, stage="audio")
        self._call_status("audio", "completed")
        self._call_status("merge", "merging")
        self._merge_video_audio(video_temp_path, audio_temp_path, output_path)
        self._call_status("merge", "completed")
        return output_path

    def _download_stream(self, format_id, output_path, stage):
        def ytdlp_hook(d):
            if d['status'] in ('downloading', 'finished'):
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes') or 0
                speed = d.get('speed') or 0
                self._call_progress(stage, {
                    'downloaded': downloaded,
                    'total': total,
                    'speed': speed,
                    'percent': (downloaded / total * 100) if total else 0.0,
                    'status': d['status'],
                })
        ydl_opts = {
            'format': format_id,
            'outtmpl': output_path,
            'progress_hooks': [ytdlp_hook],
            'quiet': True,
            'noplaylist': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([self.url])

    def _merge_video_audio(self, video_path, audio_path, output_path):
        # Simulate merge progress from 0 to 100% for UI updates
        def fake_merge_progress():
            import time
            for perc in range(0, 101, 2):
                self._call_progress('merge', {
                    'downloaded': perc,
                    'total': 100,
                    'speed': None,
                    'percent': perc,
                    'status': 'processing'
                })
                time.sleep(0.01)  # adjust for UI smoothness
        t = threading.Thread(target=fake_merge_progress)
        t.start()
        try:
            (
                ffmpeg.input(video_path)
                .input(audio_path)
                .output(output_path, c='copy', loglevel='quiet')
                .run(overwrite_output=True)
            )
        except Exception:
            import subprocess
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-i', audio_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                output_path
            ]
            subprocess.run(cmd, check=True)
        t.join()

    def _call_progress(self, stage, stats_dict):
        if self.progress_hook:
            self.progress_hook(stage, stats_dict)

    def _call_status(self, stage, status):
        if self.status_callback:
            self.status_callback(stage, status)
