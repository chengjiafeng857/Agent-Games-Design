# raw_http_hunyuan3d.py - Raw HTTP Implementation of Hunyuan 3D Provider
#
# This module implements the Hunyuan 3D API using raw HTTP requests with
# Tencent Cloud TC3-HMAC-SHA256 authentication signing.
#
# NO SDK REQUIRED - uses only httpx for HTTP requests.
#
# Reference: https://cloud.tencent.com/document/product/1804/120757
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

import hashlib
import hmac
import json
import os
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Any
from io import BytesIO

import httpx

from .hunyuan3d_provider import (
    Hunyuan3DProvider,
    Hunyuan3DJobResult,
    Hunyuan3DFile,
    Hunyuan3DAPIError,
    JobStatus,
    ViewImage,
)


# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

# Environment variable names (Required)
TENCENT_SECRET_ID_ENV = "TENCENT_SECRET_ID"
TENCENT_SECRET_KEY_ENV = "TENCENT_SECRET_KEY"

# Environment variable names (Optional - Hunyuan 3D Settings)
HUNYUAN3D_ENABLE_PBR_ENV = "HUNYUAN3D_ENABLE_PBR"
HUNYUAN3D_FACE_COUNT_ENV = "HUNYUAN3D_FACE_COUNT"
HUNYUAN3D_GENERATE_TYPE_ENV = "HUNYUAN3D_GENERATE_TYPE"
HUNYUAN3D_POLYGON_TYPE_ENV = "HUNYUAN3D_POLYGON_TYPE"

# Valid values for settings
VALID_GENERATE_TYPES = ("Normal", "LowPoly", "Geometry", "Sketch")
VALID_POLYGON_TYPES = ("triangle", "quadrilateral")
DEFAULT_FACE_COUNT = 500000
MIN_FACE_COUNT = 40000
MAX_FACE_COUNT = 1500000

# API Configuration
API_HOST = "ai3d.tencentcloudapi.com"
API_VERSION = "2025-05-13"
API_REGION = "ap-guangzhou"

# HTTP timeout in seconds
HTTP_TIMEOUT = 60.0


# -----------------------------------------------------------------------------
# TENCENT CLOUD TC3 SIGNATURE ALGORITHM
# -----------------------------------------------------------------------------

def _sign(key: bytes, msg: str) -> bytes:
    """HMAC-SHA256 signing."""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()


def _get_tc3_signature(
    secret_id: str,
    secret_key: str,
    service: str,
    host: str,
    action: str,
    payload: str,
    timestamp: int,
) -> dict[str, str]:
    """
    Generate Tencent Cloud TC3-HMAC-SHA256 authorization headers.
    
    This implements the Tencent Cloud API v3 signature algorithm.
    Reference: https://cloud.tencent.com/document/api/1278/85305
    
    Args:
        secret_id: Tencent Cloud SecretId
        secret_key: Tencent Cloud SecretKey
        service: Service name (e.g., "ai3d")
        host: API host (e.g., "ai3d.tencentcloudapi.com")
        action: API action (e.g., "SubmitHunyuanTo3DProJob")
        payload: JSON request body
        timestamp: Unix timestamp
        
    Returns:
        Dictionary of headers to include in the request
    """
    # Step 1: Build canonical request
    http_method = "POST"
    canonical_uri = "/"
    canonical_querystring = ""
    content_type = "application/json; charset=utf-8"
    
    # Calculate payload hash
    payload_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    
    # Signed headers (lowercase, sorted)
    signed_headers = "content-type;host;x-tc-action"
    
    canonical_headers = (
        f"content-type:{content_type}\n"
        f"host:{host}\n"
        f"x-tc-action:{action.lower()}\n"
    )
    
    canonical_request = (
        f"{http_method}\n"
        f"{canonical_uri}\n"
        f"{canonical_querystring}\n"
        f"{canonical_headers}\n"
        f"{signed_headers}\n"
        f"{payload_hash}"
    )
    
    # Step 2: Build string to sign
    algorithm = "TC3-HMAC-SHA256"
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
    credential_scope = f"{date}/{service}/tc3_request"
    
    hashed_canonical_request = hashlib.sha256(
        canonical_request.encode("utf-8")
    ).hexdigest()
    
    string_to_sign = (
        f"{algorithm}\n"
        f"{timestamp}\n"
        f"{credential_scope}\n"
        f"{hashed_canonical_request}"
    )
    
    # Step 3: Calculate signature
    secret_date = _sign(f"TC3{secret_key}".encode("utf-8"), date)
    secret_service = _sign(secret_date, service)
    secret_signing = _sign(secret_service, "tc3_request")
    signature = hmac.new(
        secret_signing,
        string_to_sign.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    
    # Step 4: Build authorization header
    authorization = (
        f"{algorithm} "
        f"Credential={secret_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, "
        f"Signature={signature}"
    )
    
    return {
        "Authorization": authorization,
        "Content-Type": content_type,
        "Host": host,
        "X-TC-Action": action,
        "X-TC-Timestamp": str(timestamp),
        "X-TC-Version": API_VERSION,
        "X-TC-Region": API_REGION,
    }


# -----------------------------------------------------------------------------
# RAW HTTP PROVIDER IMPLEMENTATION
# -----------------------------------------------------------------------------

class RawHttpHunyuan3DProvider(Hunyuan3DProvider):
    """
    Hunyuan 3D provider using raw HTTP requests with TC3 signature.
    
    This implementation uses httpx for HTTP requests and implements
    the Tencent Cloud TC3-HMAC-SHA256 authentication algorithm.
    
    No SDK required.
    
    Example:
        provider = RawHttpHunyuan3DProvider(
            secret_id=os.environ["TENCENT_SECRET_ID"],
            secret_key=os.environ["TENCENT_SECRET_KEY"],
        )
        job_id = provider.submit(prompt="A cute panda")
    """
    
    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
    ):
        """
        Initialize the provider.
        
        Args:
            secret_id: Tencent Cloud SecretId (or use env var)
            secret_key: Tencent Cloud SecretKey (or use env var)
            
        Raises:
            ValueError: If credentials are not provided
        """
        self.secret_id = secret_id or os.environ.get(TENCENT_SECRET_ID_ENV)
        self.secret_key = secret_key or os.environ.get(TENCENT_SECRET_KEY_ENV)
        
        if not self.secret_id or not self.secret_key:
            raise ValueError(
                f"Tencent Cloud credentials required. "
                f"Set {TENCENT_SECRET_ID_ENV} and {TENCENT_SECRET_KEY_ENV} "
                f"environment variables, or pass them to the constructor."
            )
        
        self._client = httpx.Client(timeout=HTTP_TIMEOUT)
    
    def _call_api(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """
        Make an authenticated API call to Tencent Cloud.
        
        Args:
            action: API action name
            params: Request parameters
            
        Returns:
            Response data dictionary
            
        Raises:
            Hunyuan3DAPIError: If the API returns an error
        """
        payload = json.dumps(params)
        timestamp = int(time.time())
        
        headers = _get_tc3_signature(
            secret_id=self.secret_id,
            secret_key=self.secret_key,
            service="ai3d",
            host=API_HOST,
            action=action,
            payload=payload,
            timestamp=timestamp,
        )
        
        url = f"https://{API_HOST}"
        
        response = self._client.post(
            url,
            headers=headers,
            content=payload,
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Check for API errors
        if "Response" in data:
            resp = data["Response"]
            if "Error" in resp:
                raise Hunyuan3DAPIError(
                    message=resp["Error"].get("Message", "Unknown error"),
                    code=resp["Error"].get("Code"),
                    request_id=resp.get("RequestId"),
                )
            return resp
        
        return data
    
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
        Additional settings are read from environment variables.
        
        Args:
            prompt: Text description of the 3D model
            image_url: URL of image to convert to 3D (front view)
            multi_view_images: Optional list of additional view images
                               (left, right, back views)
            
        Returns:
            Job ID for tracking
            
        Raises:
            ValueError: If inputs are invalid
            Hunyuan3DAPIError: If API fails
            
        Environment Variables (optional):
            HUNYUAN3D_ENABLE_PBR: Enable PBR materials (true/false)
            HUNYUAN3D_FACE_COUNT: Polygon count (40000-1500000)
            HUNYUAN3D_GENERATE_TYPE: Normal/LowPoly/Geometry/Sketch
            HUNYUAN3D_POLYGON_TYPE: triangle/quadrilateral (LowPoly only)
        """
        # Validate exactly one input (unless Sketch mode which allows both)
        generate_type = os.environ.get(HUNYUAN3D_GENERATE_TYPE_ENV, "Normal")
        if generate_type != "Sketch":
            if prompt and image_url:
                raise ValueError("Provide exactly one of: prompt OR image_url")
        if not prompt and not image_url:
            raise ValueError("Must provide either prompt or image_url")
        
        # Build request parameters
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
        
        # Call the API
        response = self._call_api("SubmitHunyuanTo3DProJob", params)
        
        job_id = response.get("JobId")
        if not job_id:
            raise Hunyuan3DAPIError(
                message="No JobId in response",
                request_id=response.get("RequestId"),
            )
        
        return job_id
    
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
        Poll the status of a Hunyuan 3D job.
        
        Args:
            job_id: Job ID from submit()
            
        Returns:
            Hunyuan3DJobResult with current status
        """
        response = self._call_api("QueryHunyuanTo3DProJob", {"JobId": job_id})
        
        status_str = response.get("Status", "FAIL")
        
        try:
            status = JobStatus(status_str)
        except ValueError:
            status = JobStatus.FAIL
        
        # Parse files if job is done
        files: list[Hunyuan3DFile] = []
        if status == JobStatus.DONE:
            result_files = response.get("ResultFile3Ds", [])
            for f in result_files:
                files.append(Hunyuan3DFile(
                    file_type=f.get("Type", "UNKNOWN"),
                    url=f.get("Url", ""),
                    preview_url=f.get("PreviewImageUrl"),
                ))
        
        return Hunyuan3DJobResult(
            job_id=job_id,
            status=status,
            files=files,
            error_code=response.get("ErrorCode"),
            error_message=response.get("ErrorMessage"),
        )
    
    def download_result(
        self,
        result: Hunyuan3DJobResult,
        output_dir: Path,
    ) -> list[Path]:
        """
        Download generated 3D files to local disk.
        
        If the file is a ZIP, it will be extracted.
        
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
            response = self._client.get(file_info.url)
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
                    preview_resp = self._client.get(file_info.preview_url)
                    preview_resp.raise_for_status()
                    preview_path = output_dir / "preview.png"
                    preview_path.write_bytes(preview_resp.content)
                    downloaded_paths.append(preview_path)
                except Exception:
                    pass  # Preview is optional, don't fail on it
        
        return downloaded_paths
    
    def _extract_zip(self, content: bytes, output_dir: Path) -> list[Path]:
        """
        Extract a ZIP file to the output directory.
        
        Args:
            content: ZIP file bytes
            output_dir: Directory to extract to
            
        Returns:
            List of extracted file paths
        """
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
        """Clean up the HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()
