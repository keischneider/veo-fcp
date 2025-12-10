"""
Lip-sync API client using D-ID Creative Reality Studio
"""
import os
import time
import logging
import requests
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LipSyncClient:
    """Client for D-ID lip-sync API"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize D-ID lip-sync client

        Args:
            api_key: D-ID API key
        """
        self.api_key = api_key or os.getenv("DID_API_KEY")
        if not self.api_key:
            raise ValueError("D-ID API key is required")

        self.base_url = "https://api.d-id.com"
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }

        logger.info("Initialized D-ID lip-sync client")

    def create_talk_video(
        self,
        video_path: str,
        audio_path: str,
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a lip-synced video using D-ID Talk API

        Args:
            video_path: Path to source video file
            audio_path: Path to audio file
            webhook_url: Optional webhook for completion notification

        Returns:
            Dictionary with talk ID and status
        """
        logger.info("Creating lip-synced video with D-ID")

        try:
            # Upload source video if it's a local file
            video_url = self._upload_video(video_path)

            # Upload audio if it's a local file
            audio_url = self._upload_audio(audio_path)

            # Create talk video
            endpoint = f"{self.base_url}/talks"
            payload = {
                "source_url": video_url,
                "script": {
                    "type": "audio",
                    "audio_url": audio_url
                },
                "config": {
                    "fluent": True,
                    "pad_audio": 0.0,
                    "stitch": True
                }
            }

            if webhook_url:
                payload["webhook"] = webhook_url

            response = requests.post(endpoint, json=payload, headers=self.headers)
            response.raise_for_status()

            result = response.json()
            talk_id = result.get("id")

            logger.info(f"Created D-ID talk video with ID: {talk_id}")
            return result

        except Exception as e:
            logger.error(f"Error creating lip-synced video: {str(e)}")
            raise

    def _upload_video(self, video_path: str) -> str:
        """
        Upload video to D-ID (or return URL if already remote)

        Args:
            video_path: Path to video file or URL

        Returns:
            Video URL
        """
        # If it's already a URL, return it
        if video_path.startswith(('http://', 'https://')):
            return video_path

        # Upload to D-ID
        logger.info(f"Uploading video: {video_path}")

        try:
            endpoint = f"{self.base_url}/images"

            with open(video_path, 'rb') as f:
                files = {'image': f}
                headers = {"Authorization": self.headers["Authorization"]}
                response = requests.post(endpoint, files=files, headers=headers)
                response.raise_for_status()

            result = response.json()
            video_url = result.get("url")
            logger.info(f"Video uploaded: {video_url}")
            return video_url

        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            raise

    def _upload_audio(self, audio_path: str) -> str:
        """
        Upload audio to D-ID (or return URL if already remote)

        Args:
            audio_path: Path to audio file or URL

        Returns:
            Audio URL
        """
        # If it's already a URL, return it
        if audio_path.startswith(('http://', 'https://')):
            return audio_path

        # Upload to D-ID
        logger.info(f"Uploading audio: {audio_path}")

        try:
            endpoint = f"{self.base_url}/audios"

            with open(audio_path, 'rb') as f:
                files = {'audio': f}
                headers = {"Authorization": self.headers["Authorization"]}
                response = requests.post(endpoint, files=files, headers=headers)
                response.raise_for_status()

            result = response.json()
            audio_url = result.get("url")
            logger.info(f"Audio uploaded: {audio_url}")
            return audio_url

        except Exception as e:
            logger.error(f"Error uploading audio: {str(e)}")
            raise

    def get_talk_status(self, talk_id: str) -> Dict[str, Any]:
        """
        Get status of a talk video

        Args:
            talk_id: Talk ID from create_talk_video

        Returns:
            Dictionary with status and result URL if completed
        """
        try:
            endpoint = f"{self.base_url}/talks/{talk_id}"
            response = requests.get(endpoint, headers=self.headers)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            logger.error(f"Error getting talk status: {str(e)}")
            raise

    def wait_for_completion(
        self,
        talk_id: str,
        timeout: int = 600,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Wait for lip-sync video to complete

        Args:
            talk_id: Talk ID from create_talk_video
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks in seconds

        Returns:
            Dictionary with completed video information
        """
        logger.info(f"Waiting for talk {talk_id} to complete...")

        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                status = self.get_talk_status(talk_id)

                if status.get("status") == "done":
                    logger.info(f"Talk {talk_id} completed successfully")
                    return status
                elif status.get("status") == "error":
                    error_msg = status.get("error", {}).get("description", "Unknown error")
                    raise Exception(f"Talk {talk_id} failed: {error_msg}")

                logger.debug(f"Talk {talk_id} status: {status.get('status')}")
                time.sleep(poll_interval)

            except Exception as e:
                logger.error(f"Error checking talk status: {str(e)}")
                raise

        raise TimeoutError(f"Talk {talk_id} did not complete within {timeout} seconds")

    def download_result(self, talk_id: str, output_path: str) -> str:
        """
        Download completed lip-sync video

        Args:
            talk_id: Talk ID
            output_path: Path to save the video

        Returns:
            Path to downloaded video
        """
        logger.info(f"Downloading result for talk {talk_id}")

        try:
            # Get final status to get result URL
            status = self.get_talk_status(talk_id)

            if status.get("status") != "done":
                raise Exception(f"Video not ready. Status: {status.get('status')}")

            result_url = status.get("result_url")
            if not result_url:
                raise Exception("No result URL found")

            # Download video
            response = requests.get(result_url, stream=True)
            response.raise_for_status()

            os.makedirs(os.path.dirname(output_path), exist_ok=True)

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"Downloaded lip-sync video to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error downloading result: {str(e)}")
            raise

    def create_and_wait(
        self,
        video_path: str,
        audio_path: str,
        output_path: str,
        timeout: int = 600
    ) -> str:
        """
        Complete pipeline: create, wait, and download lip-sync video

        Args:
            video_path: Path to source video
            audio_path: Path to audio file
            output_path: Path to save final video
            timeout: Maximum wait time

        Returns:
            Path to final lip-synced video
        """
        # Create talk video
        result = self.create_talk_video(video_path, audio_path)
        talk_id = result.get("id")

        # Wait for completion
        self.wait_for_completion(talk_id, timeout=timeout)

        # Download result
        return self.download_result(talk_id, output_path)
