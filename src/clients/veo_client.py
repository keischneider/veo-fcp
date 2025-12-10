"""
Google Veo API Client for video generation using google-genai SDK
"""
import os
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class VeoClient:
    """Client for Google Veo video generation API"""

    def __init__(
        self,
        project_id: Optional[str] = None,
        location: Optional[str] = None,
        credentials_path: Optional[str] = None
    ):
        """
        Initialize Veo API client using google-genai SDK

        Args:
            project_id: Google Cloud project ID
            location: Google Cloud location (e.g., us-central1)
            credentials_path: Path to service account JSON key
        """
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.getenv("VEO_LOCATION", "us-central1")
        self.model_name = os.getenv("VEO_MODEL", "veo-2.0-generate-001")

        # Set up credentials path for google-genai
        creds_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if creds_path:
            # Resolve relative paths
            creds_path = Path(creds_path)
            if not creds_path.is_absolute():
                creds_path = Path.cwd() / creds_path

            # Set environment variable for google-genai to use
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(creds_path)

        # Import and initialize the client
        from google import genai
        from google.genai import types

        # Create Vertex AI client (not API key based)
        self.client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )
        self.types = types

        # Store operations by job_id for tracking
        self.operations = {}

        logger.info(f"Initialized Veo client for project {self.project_id} in {self.location}")

    def generate_video(
        self,
        prompt: str,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        input_video: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate video using Veo API

        Args:
            prompt: Text prompt for video generation
            duration: Video duration in seconds (5 or 8 seconds supported)
            aspect_ratio: Video aspect ratio (9:16, 16:9, or 1:1)
            input_video: Optional path to input video file for extension (1-30 seconds)
                        Or GCS URI (gs://bucket/path/video.mp4)
            **kwargs: Additional API parameters:
                - enhance_prompt (bool): Whether to enhance the prompt (default: True)
                - number_of_videos (int): Number of videos to generate (default: 1)

        Returns:
            Dictionary containing job_id, operation, and other metadata
        """
        if input_video:
            logger.info(f"Extending video from: {input_video}")
            logger.info(f"Extension prompt: {prompt[:100]}...")
        else:
            logger.info(f"Generating video with prompt: {prompt[:100]}...")

        try:
            # Prepare configuration
            config = self.types.GenerateVideosConfig(
                number_of_videos=kwargs.get("number_of_videos", 1),
                duration_seconds=duration,
                enhance_prompt=kwargs.get("enhance_prompt", True),
            )

            # Prepare video input if provided
            video_param = None
            if input_video:
                if input_video.startswith("gs://"):
                    # GCS URI
                    video_param = self.types.Video(uri=input_video)
                    logger.info(f"Using GCS video URI: {input_video}")
                else:
                    # Local file - load and encode
                    video_param = self.types.Video.from_file(input_video)
                    logger.info(f"Loaded video from file: {input_video}")

            # Generate video
            logger.info(f"Sending request to Veo API (model: {self.model_name})...")
            logger.info(f"Duration: {duration}s, Aspect ratio: {aspect_ratio}")

            operation = self.client.models.generate_videos(
                model=self.model_name,
                prompt=prompt,
                video=video_param,  # Add video parameter
                config=config,
            )

            # Create job ID and store operation
            job_id = f"veo_job_{int(time.time())}"
            self.operations[job_id] = operation

            job_data = {
                "job_id": job_id,
                "status": "PROCESSING",  # Operation is async
                "prompt": prompt,
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "created_at": time.time(),
                "operation": operation,  # Store the operation object
                "operation_name": operation.name if hasattr(operation, 'name') else None,
            }

            logger.info(f"Video generation started with job_id: {job_id}")
            logger.info(f"Operation: {operation.name if hasattr(operation, 'name') else 'N/A'}")

            return job_data

        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            raise

    def wait_for_completion(
        self,
        job_id: str,
        timeout: int = 600,
        poll_interval: int = 20
    ) -> Dict[str, Any]:
        """
        Wait for video generation to complete

        Args:
            job_id: Job identifier from generate_video
            timeout: Maximum wait time in seconds
            poll_interval: Time between status checks in seconds (recommended: 20s)

        Returns:
            Dictionary with job status and video data
        """
        logger.info(f"Waiting for job {job_id} to complete...")

        if job_id not in self.operations:
            raise ValueError(f"Job {job_id} not found. Did you call generate_video?")

        operation = self.operations[job_id]
        start_time = time.time()

        while time.time() - start_time < timeout:
            try:
                # Check if operation is done
                if operation.done:
                    logger.info(f"Job {job_id} completed successfully")

                    # Extract video data
                    if hasattr(operation, 'response') and operation.response:
                        generated_videos = operation.response.generated_videos

                        if generated_videos and len(generated_videos) > 0:
                            video = generated_videos[0].video

                            return {
                                "job_id": job_id,
                                "status": "COMPLETED",
                                "video": video,
                                "completed_at": time.time(),
                                "operation": operation,
                            }
                        else:
                            raise Exception("No videos were generated in the response")
                    else:
                        raise Exception(f"Operation completed but no response available: {operation}")

                # Poll for updates
                logger.info(f"Job {job_id} still processing... (elapsed: {int(time.time() - start_time)}s)")
                time.sleep(poll_interval)

                # Refresh operation status
                operation = self.client.operations.get(operation)
                self.operations[job_id] = operation

            except Exception as e:
                logger.error(f"Error checking job status: {str(e)}")
                raise

        raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")

    def _check_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Check status of a video generation job

        Args:
            job_id: Job identifier

        Returns:
            Dictionary with job status information
        """
        if job_id not in self.operations:
            raise ValueError(f"Job {job_id} not found")

        operation = self.operations[job_id]

        # Refresh operation
        operation = self.client.operations.get(operation)
        self.operations[job_id] = operation

        status = "COMPLETED" if operation.done else "PROCESSING"

        return {
            "job_id": job_id,
            "status": status,
            "operation": operation,
        }

    def get_video_url(self, job_id: str) -> Optional[str]:
        """
        Get download URL for generated video

        Args:
            job_id: Job identifier

        Returns:
            URL to download the video, or None if using video object directly
        """
        status = self._check_job_status(job_id)

        if status["status"] != "COMPLETED":
            raise Exception(f"Video not ready. Status: {status['status']}")

        operation = status["operation"]

        if hasattr(operation, 'response') and operation.response:
            generated_videos = operation.response.generated_videos
            if generated_videos and len(generated_videos) > 0:
                video = generated_videos[0].video
                # Video object might have a URI
                if hasattr(video, 'uri'):
                    return video.uri

        return None

    def save_video(self, job_id: str, output_path: str) -> str:
        """
        Save generated video to file

        Args:
            job_id: Job identifier
            output_path: Path where to save the video file

        Returns:
            Path to the saved video file
        """
        logger.info(f"Saving video from job {job_id} to {output_path}")

        if job_id not in self.operations:
            raise ValueError(f"Job {job_id} not found")

        operation = self.operations[job_id]

        if not operation.done:
            raise Exception(f"Video generation not complete yet. Call wait_for_completion first.")

        if hasattr(operation, 'response') and operation.response:
            generated_videos = operation.response.generated_videos

            if generated_videos and len(generated_videos) > 0:
                video = generated_videos[0].video

                # Save video using the SDK's save method
                video.save(output_path)
                logger.info(f"Video saved to {output_path}")

                return output_path
            else:
                raise Exception("No videos in response")
        else:
            raise Exception("Operation has no response")
