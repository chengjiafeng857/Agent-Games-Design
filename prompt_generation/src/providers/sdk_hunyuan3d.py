# sdk_hunyuan3d.py - Tencent Cloud SDK Implementation of Hunyuan 3D Provider
#
# This module implements the Hunyuan 3D API using the official Tencent Cloud SDK.
# It's an alternative to the raw HTTP implementation with simpler code.
#
# REQUIRES:
#   pip install tencentcloud-sdk-python-ai3d
#   Or: uv add tencentcloud-sdk-python-ai3d
#
# Environment Variables (Required):
#   TENCENT_SECRET_ID: Tencent Cloud SecretId
#   TENCENT_SECRET_KEY: Tencent Cloud SecretKey
#
# Environment Variables (Optional - Hunyuan 3D Settings):
#   HUNYUAN3D_ENABLE_PBR: Enable PBR materials (true/false, default: false)
#   HUNYUAN3D_FACE_COUNT: Polygon face count (40000-1500000, default: 500000)
#   HUNYUAN3D_GENERATE_TYPE: Generation mode (Normal/LowPoly/Geometry/Sketch, default: Normal)
#   HUNYUAN3D_POLYGON_TYPE: Polygon type for LowPoly (triangle/quadrilateral, default: triangle)

import json
import os
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional, Any

import httpx

from .hunyuan3d_provider import (
    Hunyuan3DProvider,
    Hunyuan3DJobResult,
    Hunyuan3DFile,
    Hunyuan3DAPIError,
    JobStatus,
    ViewImage,
)
from .raw_http_hunyuan3d import (
    TENCENT_SECRET_ID_ENV,
    TENCENT_SECRET_KEY_ENV,
    HUNYUAN3D_ENABLE_PBR_ENV,
    HUNYUAN3D_FACE_COUNT_ENV,
    HUNYUAN3D_GENERATE_TYPE_ENV,
    HUNYUAN3D_POLYGON_TYPE_ENV,
    VALID_GENERATE_TYPES,
    VALID_POLYGON_TYPES,
    MIN_FACE_COUNT,
    MAX_FACE_COUNT,
)


# -----------------------------------------------------------------------------
# SDK AVAILABILITY CHECK
# -----------------------------------------------------------------------------

def is_sdk_available() -> bool:
    """
    Check if the Tencent Cloud SDK is installed.
    
    Returns:
        True if SDK is available, False otherwise
    """
    try:
        from tencentcloud.ai3d.v20250513 import ai3d_client, models
        return True
    except ImportError:
        return False


def get_sdk_install_instructions() -> str:
    """Get instructions for installing the SDK."""
    return (
        "Tencent Cloud SDK not installed.\n"
        "Install with: uv add tencentcloud-sdk-python-ai3d\n"
        "Or: pip install tencentcloud-sdk-python-ai3d\n"
        "Or use --provider http (default) which doesn't require the SDK."
    )


# -----------------------------------------------------------------------------
# SDK PROVIDER IMPLEMENTATION
# -----------------------------------------------------------------------------

class SDKHunyuan3DProvider(Hunyuan3DProvider):
    """
    Hunyuan 3D provider using the official Tencent Cloud SDK.
    
    This implementation uses the tencentcloud-sdk-python-ai3d package
    for a simpler, more maintainable integration.
    
    Pros over raw HTTP:
        - No need to implement TC3 signing manually
        - Official SDK handles auth, retries, errors
        - Type hints and models from SDK
    
    Cons:
        - Requires additional dependency
        - Larger package size
    
    Example:
        provider = SDKHunyuan3DProvider(
            secret_id=os.environ["TENCENT_SECRET_ID"],
            secret_key=os.environ["TENCENT_SECRET_KEY"],
        )
        job_id = provider.submit(prompt="A cute panda")
    """
    
    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        region: str = "ap-guangzhou",
    ):
        """
        Initialize the SDK provider.
        
        Args:
            secret_id: Tencent Cloud SecretId (or use env var)
            secret_key: Tencent Cloud SecretKey (or use env var)
            region: API region (default: ap-guangzhou)
            
        Raises:
            ImportError: If SDK is not installed
            ValueError: If credentials are not provided
        """
        # Check SDK availability
        if not is_sdk_available():
            raise ImportError(get_sdk_install_instructions())
        
        # Get credentials
        self.secret_id = secret_id or os.environ.get(TENCENT_SECRET_ID_ENV)
        self.secret_key = secret_key or os.environ.get(TENCENT_SECRET_KEY_ENV)
        
        if not self.secret_id or not self.secret_key:
            raise ValueError(
                f"Tencent Cloud credentials required. "
                f"Set {TENCENT_SECRET_ID_ENV} and {TENCENT_SECRET_KEY_ENV} "
                f"environment variables, or pass them to the constructor."
            )
        
        self.region = region
        self._client = None
        self._http_client = httpx.Client(timeout=120.0)
    
    def _get_client(self):
        """Get or create the SDK client (lazy initialization)."""
        if self._client is None:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.ai3d.v20250513 import ai3d_client
            
            cred = credential.Credential(self.secret_id, self.secret_key)
            
            http_profile = HttpProfile()
            http_profile.endpoint = "ai3d.tencentcloudapi.com"
            
            client_profile = ClientProfile()
            client_profile.httpProfile = http_profile
            
            self._client = ai3d_client.Ai3dClient(cred, self.region, client_profile)
        
        return self._client
    
    def submit(
        self,
        *,
        prompt: Optional[str] = None,
        image_url: Optional[str] = None,
        multi_view_images: Optional[list[ViewImage]] = None,
    ) -> str:
        """
        Submit a Hunyuan 3D generation job using SDK.
        
        Args:
            prompt: Text description of the 3D model
            image_url: URL of image to convert to 3D (front view)
            multi_view_images: Optional list of additional view images
                               (left, right, back views)
            
        Returns:
            Job ID for tracking
            
        Environment Variables (optional):
            HUNYUAN3D_ENABLE_PBR: Enable PBR materials (true/false)
            HUNYUAN3D_FACE_COUNT: Polygon count (40000-1500000)
            HUNYUAN3D_GENERATE_TYPE: Normal/LowPoly/Geometry/Sketch
            HUNYUAN3D_POLYGON_TYPE: triangle/quadrilateral (LowPoly only)
        """
        # Validate inputs (unless Sketch mode which allows both)
        generate_type = os.environ.get(HUNYUAN3D_GENERATE_TYPE_ENV, "Normal")
        if generate_type != "Sketch":
            if prompt and image_url:
                raise ValueError("Provide exactly one of: prompt OR image_url")
        if not prompt and not image_url:
            raise ValueError("Must provide either prompt or image_url")
        
        from tencentcloud.ai3d.v20250513 import models
        
        client = self._get_client()
        
        # Build request
        req = models.SubmitHunyuanTo3DProJobRequest()
        params: dict[str, Any] = {}
        if prompt:
            params["Prompt"] = prompt
        if image_url:
            params["ImageUrl"] = image_url
        
        # Add multi-view images if provided
        if multi_view_images:
            params["MultiViewImages"] = [
                img.to_api_dict() for img in multi_view_images
            ]
        
        # Add optional settings from environment variables
        self._add_optional_params(params)
        
        req.from_json_string(json.dumps(params))
        
        # Submit
        try:
            resp = client.SubmitHunyuanTo3DProJob(req)
            return resp.JobId
        except Exception as e:
            raise Hunyuan3DAPIError(
                message=str(e),
                code=getattr(e, 'code', None),
                request_id=getattr(e, 'requestId', None),
            )
    
    def _add_optional_params(self, params: dict[str, Any]) -> None:
        """
        Add optional parameters from environment variables.
        
        Args:
            params: Request parameters dict to modify in place
        """
        # EnablePBR
        enable_pbr = os.environ.get(HUNYUAN3D_ENABLE_PBR_ENV, "").lower()
        if enable_pbr in ("true", "1", "yes"):
            params["EnablePBR"] = True
        elif enable_pbr in ("false", "0", "no"):
            params["EnablePBR"] = False
        
        # FaceCount
        face_count_str = os.environ.get(HUNYUAN3D_FACE_COUNT_ENV, "")
        if face_count_str:
            try:
                face_count = int(face_count_str)
                if MIN_FACE_COUNT <= face_count <= MAX_FACE_COUNT:
                    params["FaceCount"] = face_count
                else:
                    print(f"Warning: {HUNYUAN3D_FACE_COUNT_ENV}={face_count} out of range "
                          f"({MIN_FACE_COUNT}-{MAX_FACE_COUNT}), using default")
            except ValueError:
                print(f"Warning: Invalid {HUNYUAN3D_FACE_COUNT_ENV}={face_count_str}, using default")
        
        # GenerateType
        generate_type = os.environ.get(HUNYUAN3D_GENERATE_TYPE_ENV, "")
        if generate_type:
            if generate_type in VALID_GENERATE_TYPES:
                params["GenerateType"] = generate_type
            else:
                print(f"Warning: Invalid {HUNYUAN3D_GENERATE_TYPE_ENV}={generate_type}, "
                      f"valid options: {', '.join(VALID_GENERATE_TYPES)}")
        
        # PolygonType (only effective for LowPoly mode)
        polygon_type = os.environ.get(HUNYUAN3D_POLYGON_TYPE_ENV, "")
        if polygon_type:
            if polygon_type in VALID_POLYGON_TYPES:
                params["PolygonType"] = polygon_type
            else:
                print(f"Warning: Invalid {HUNYUAN3D_POLYGON_TYPE_ENV}={polygon_type}, "
                      f"valid options: {', '.join(VALID_POLYGON_TYPES)}")
    
    def poll(self, job_id: str) -> Hunyuan3DJobResult:
        """
        Poll the status of a Hunyuan 3D job using SDK.
        
        Args:
            job_id: Job ID from submit()
            
        Returns:
            Hunyuan3DJobResult with current status
        """
        from tencentcloud.ai3d.v20250513 import models
        
        client = self._get_client()
        
        req = models.QueryHunyuanTo3DProJobRequest()
        req.from_json_string(json.dumps({"JobId": job_id}))
        
        try:
            resp = client.QueryHunyuanTo3DProJob(req)
        except Exception as e:
            raise Hunyuan3DAPIError(
                message=str(e),
                code=getattr(e, 'code', None),
            )
        
        # Parse status
        status_str = resp.Status or "FAIL"
        try:
            status = JobStatus(status_str)
        except ValueError:
            status = JobStatus.FAIL
        
        # Parse files if done
        files: list[Hunyuan3DFile] = []
        if status == JobStatus.DONE and resp.ResultFile3Ds:
            for f in resp.ResultFile3Ds:
                files.append(Hunyuan3DFile(
                    file_type=f.Type or "UNKNOWN",
                    url=f.Url or "",
                    preview_url=getattr(f, 'PreviewImageUrl', None),
                ))
        
        return Hunyuan3DJobResult(
            job_id=job_id,
            status=status,
            files=files,
            error_code=getattr(resp, 'ErrorCode', None),
            error_message=getattr(resp, 'ErrorMessage', None),
        )
    
    def download_result(
        self,
        result: Hunyuan3DJobResult,
        output_dir: Path,
    ) -> list[Path]:
        """
        Download generated 3D files to local disk.
        
        Args:
            result: Job result with status=DONE
            output_dir: Directory for downloads
            
        Returns:
            List of paths to downloaded/extracted files
        """
        if result.status != JobStatus.DONE:
            raise ValueError(f"Cannot download: job status is {result.status.value}")
        
        output_dir.mkdir(parents=True, exist_ok=True)
        downloaded_paths: list[Path] = []
        
        for file_info in result.files:
            if not file_info.url:
                continue
            
            # Download the file
            response = self._http_client.get(file_info.url)
            response.raise_for_status()
            
            content = response.content
            
            # Check if it's a ZIP file
            if file_info.url.endswith(".zip") or content[:4] == b"PK\x03\x04":
                # Extract ZIP
                extracted = self._extract_zip(content, output_dir)
                downloaded_paths.extend(extracted)
            else:
                # Save directly
                ext = file_info.file_type.lower()
                filename = f"model.{ext}"
                file_path = output_dir / filename
                file_path.write_bytes(content)
                downloaded_paths.append(file_path)
            
            # Download preview image if available
            if file_info.preview_url:
                try:
                    preview_resp = self._http_client.get(file_info.preview_url)
                    preview_resp.raise_for_status()
                    preview_path = output_dir / "preview.png"
                    preview_path.write_bytes(preview_resp.content)
                    downloaded_paths.append(preview_path)
                except Exception:
                    pass  # Preview is optional
        
        return downloaded_paths
    
    def _extract_zip(self, content: bytes, output_dir: Path) -> list[Path]:
        """Extract a ZIP file to the output directory."""
        extracted_paths: list[Path] = []
        
        with zipfile.ZipFile(BytesIO(content), "r") as zf:
            for name in zf.namelist():
                # Skip directories and hidden files
                if name.endswith("/") or name.startswith("__"):
                    continue
                
                # Extract the file
                extracted_path = output_dir / Path(name).name
                with zf.open(name) as src:
                    extracted_path.write_bytes(src.read())
                
                extracted_paths.append(extracted_path)
        
        return extracted_paths
    
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, "_http_client"):
            self._http_client.close()


# -----------------------------------------------------------------------------
# SDK COS UPLOADER
# -----------------------------------------------------------------------------

class SDKCOSUploader:
    """
    Upload files to Tencent COS using the official SDK.
    
    This is an alternative to the raw HTTP COS uploader.
    
    REQUIRES:
        pip install tencentcloud-sdk-python-cos
        Or: uv add tencentcloud-sdk-python-cos
    """
    
    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
    ):
        """Initialize the SDK COS uploader."""
        from .tencent_cos import (
            TENCENT_COS_BUCKET_ENV,
            TENCENT_COS_REGION_ENV,
        )
        
        self.secret_id = secret_id or os.environ.get(TENCENT_SECRET_ID_ENV)
        self.secret_key = secret_key or os.environ.get(TENCENT_SECRET_KEY_ENV)
        self.bucket = bucket or os.environ.get(TENCENT_COS_BUCKET_ENV)
        self.region = region or os.environ.get(TENCENT_COS_REGION_ENV)
        
        if not all([self.secret_id, self.secret_key, self.bucket, self.region]):
            raise ValueError(
                "COS credentials required. Set environment variables: "
                f"{TENCENT_SECRET_ID_ENV}, {TENCENT_SECRET_KEY_ENV}, "
                f"{TENCENT_COS_BUCKET_ENV}, {TENCENT_COS_REGION_ENV}"
            )
        
        # For now, use the raw HTTP uploader as COS SDK has different API
        # The tencentcloud-sdk-python-cos is for COS API, not the simple upload
        from .tencent_cos import TencentCOSUploader
        self._uploader = TencentCOSUploader(
            secret_id=self.secret_id,
            secret_key=self.secret_key,
            bucket=self.bucket,
            region=self.region,
        )
    
    def upload_file(self, file_path: Path, object_key: Optional[str] = None) -> str:
        """Upload a file to COS and return the URL."""
        return self._uploader.upload_file(file_path, object_key)
