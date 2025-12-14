# hunyuan3d_provider.py - Provider Abstraction for Hunyuan 3D API
#
# This module defines the Protocol/ABC for Hunyuan 3D providers.
# Different implementations can use different HTTP clients or auth methods.
#
# The Hunyuan 3D API workflow:
#   1. submit() - Submit a job with prompt or image URL (optionally with multi-view images)
#   2. poll() - Check job status until DONE/FAIL
#   3. download_result() - Download the generated 3D files

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from pathlib import Path


class JobStatus(Enum):
    """Status of a Hunyuan 3D job."""
    WAIT = "WAIT"      # Waiting in queue
    RUN = "RUN"        # Processing
    DONE = "DONE"      # Completed successfully
    FAIL = "FAIL"      # Failed


# Valid view types for multi-view images
VALID_VIEW_TYPES = ("left", "right", "back")


@dataclass
class ViewImage:
    """
    A view image for multi-view 3D generation.
    
    Attributes:
        view: View type - "left", "right", or "back"
        image_url: URL of the image for this view
    """
    view: str
    image_url: str
    
    def __post_init__(self):
        if self.view not in VALID_VIEW_TYPES:
            raise ValueError(
                f"Invalid view type: {self.view}. "
                f"Valid options: {', '.join(VALID_VIEW_TYPES)}"
            )
    
    def to_api_dict(self) -> dict:
        """Convert to API parameter format."""
        return {
            "View": self.view,
            "ImageUrl": self.image_url,
        }


@dataclass
class Hunyuan3DFile:
    """
    Represents a file returned by the Hunyuan 3D API.
    
    Attributes:
        file_type: Type of file (OBJ, GLB, etc.)
        url: Download URL for the file
        preview_url: Optional preview image URL
    """
    file_type: str
    url: str
    preview_url: Optional[str] = None


@dataclass
class Hunyuan3DJobResult:
    """
    Result of a Hunyuan 3D job.
    
    Attributes:
        job_id: The job identifier
        status: Current job status
        files: List of generated files (when DONE)
        error_code: Error code (when FAIL)
        error_message: Error message (when FAIL)
    """
    job_id: str
    status: JobStatus
    files: list[Hunyuan3DFile] = field(default_factory=list)
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class Hunyuan3DProvider(ABC):
    """
    Abstract base class for Hunyuan 3D API providers.
    
    This defines the interface that all Hunyuan 3D providers must implement.
    Providers can use different HTTP clients (httpx, openai, etc.) and
    authentication methods.
    
    Usage:
        provider = RawHttpHunyuan3DProvider(secret_id, secret_key)
        job_id = provider.submit(prompt="A cute panda")
        result = provider.poll(job_id)
        if result.status == JobStatus.DONE:
            files = provider.download_result(result, output_dir)
    """
    
    @abstractmethod
    def submit(
        self,
        *,
        prompt: Optional[str] = None,
        image_url: Optional[str] = None,
        multi_view_images: Optional[list[ViewImage]] = None,
    ) -> str:
        """
        Submit a Hunyuan 3D generation job.
        
        Must provide exactly one of: prompt OR image_url.
        Optionally provide additional view images for better 3D reconstruction.
        
        Args:
            prompt: Text description of the 3D model to generate
            image_url: URL of an image to convert to 3D (front view)
            multi_view_images: Optional list of additional view images
                               (left, right, back views)
            
        Returns:
            The job ID for tracking the submission
            
        Raises:
            ValueError: If neither or both inputs are provided
            Hunyuan3DAPIError: If the API returns an error
        """
        pass
    
    @abstractmethod
    def poll(self, job_id: str) -> Hunyuan3DJobResult:
        """
        Poll the status of a Hunyuan 3D job.
        
        Args:
            job_id: The job ID returned by submit()
            
        Returns:
            Hunyuan3DJobResult with current status and files (if DONE)
            
        Raises:
            Hunyuan3DAPIError: If the API returns an error
        """
        pass
    
    @abstractmethod
    def download_result(
        self,
        result: Hunyuan3DJobResult,
        output_dir: Path,
    ) -> list[Path]:
        """
        Download the generated 3D files to local disk.
        
        Args:
            result: A job result with status=DONE and files list
            output_dir: Directory to save downloaded files
            
        Returns:
            List of paths to downloaded files
            
        Raises:
            ValueError: If result.status is not DONE
            Hunyuan3DAPIError: If download fails
        """
        pass


class Hunyuan3DAPIError(Exception):
    """
    Exception raised for Hunyuan 3D API errors.
    
    Attributes:
        code: Error code from the API
        message: Error message from the API
        request_id: Request ID for debugging
    """
    
    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        request_id: Optional[str] = None,
    ):
        self.code = code
        self.request_id = request_id
        super().__init__(f"{message} (code={code}, request_id={request_id})")
