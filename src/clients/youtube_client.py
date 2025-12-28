"""
YouTube video downloading client using yt-dlp
"""
import os
import logging
from pathlib import Path
from typing import Optional
import yt_dlp

logger = logging.getLogger(__name__)


class YouTubeClient:
    """Client for downloading videos from YouTube using yt-dlp"""

    def __init__(self, output_format: str = "mp4"):
        """
        Initialize YouTube client

        Args:
            output_format: Preferred output format (mp4, webm, etc.)
        """
        self.output_format = output_format

    def get_video_info(self, url: str) -> dict:
        """
        Get video metadata without downloading

        Args:
            url: YouTube URL

        Returns:
            Dictionary with video metadata
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'description': info.get('description'),
                    'uploader': info.get('uploader'),
                    'view_count': info.get('view_count'),
                    'width': info.get('width'),
                    'height': info.get('height'),
                    'fps': info.get('fps'),
                    'thumbnail': info.get('thumbnail'),
                }
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            raise

    def download_video(
        self,
        url: str,
        output_path: str,
        quality: str = "best",
        max_height: Optional[int] = None,
    ) -> str:
        """
        Download video from YouTube

        Args:
            url: YouTube URL
            output_path: Full path for output file (without extension)
            quality: Quality preset ('best', '1080p', '720p', '480p', 'worst')
            max_height: Maximum video height (e.g., 1080, 720)

        Returns:
            Path to downloaded file
        """
        logger.info(f"Downloading video from YouTube: {url}")

        # Create output directory
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Build format selector based on quality
        if max_height:
            format_selector = f'bestvideo[height<={max_height}]+bestaudio/best[height<={max_height}]'
        elif quality == 'best':
            format_selector = 'bestvideo+bestaudio/best'
        elif quality == '1080p':
            format_selector = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif quality == '720p':
            format_selector = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif quality == '480p':
            format_selector = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
        elif quality == 'worst':
            format_selector = 'worstvideo+worstaudio/worst'
        else:
            format_selector = 'bestvideo+bestaudio/best'

        ydl_opts = {
            'format': format_selector,
            'outtmpl': output_path,
            'merge_output_format': self.output_format,
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
            'postprocessors': [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': self.output_format,
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find the actual output file (yt-dlp adds extension)
            final_path = f"{output_path}.{self.output_format}"
            if os.path.exists(final_path):
                logger.info(f"Downloaded video to {final_path}")
                return final_path

            # Check if file exists without double extension
            if os.path.exists(output_path):
                logger.info(f"Downloaded video to {output_path}")
                return output_path

            # Look for any file with the base name
            output_base = Path(output_path)
            for ext in ['mp4', 'webm', 'mkv', 'mov']:
                check_path = str(output_base.parent / f"{output_base.name}.{ext}")
                if os.path.exists(check_path):
                    logger.info(f"Downloaded video to {check_path}")
                    return check_path

            raise FileNotFoundError(f"Downloaded file not found at expected path: {output_path}")

        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise

    def download_audio(
        self,
        url: str,
        output_path: str,
        audio_format: str = "wav",
    ) -> str:
        """
        Download only audio from YouTube video

        Args:
            url: YouTube URL
            output_path: Full path for output file (without extension)
            audio_format: Audio format (wav, mp3, m4a, etc.)

        Returns:
            Path to downloaded audio file
        """
        logger.info(f"Downloading audio from YouTube: {url}")

        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': False,
            'no_warnings': False,
            'progress_hooks': [self._progress_hook],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': audio_format,
                'preferredquality': '192',
            }],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            final_path = f"{output_path}.{audio_format}"
            if os.path.exists(final_path):
                logger.info(f"Downloaded audio to {final_path}")
                return final_path

            raise FileNotFoundError(f"Downloaded audio file not found: {final_path}")

        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            raise

    def _progress_hook(self, d: dict):
        """Progress callback for download status"""
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', 'N/A')
            speed = d.get('_speed_str', 'N/A')
            logger.debug(f"Download progress: {percent} at {speed}")
        elif d['status'] == 'finished':
            logger.info("Download finished, processing...")
