# tencent_cos.py - Tencent Cloud Object Storage (COS) Uploader
#
# This module handles uploading images to Tencent COS to get a public URL
# that can be used with the Hunyuan 3D API.
#
# Two implementations are provided:
#   - SDKCOSUploader: Uses official cos-python-sdk-v5 (default, recommended)
#   - TencentCOSUploader: Uses raw HTTP requests with manual signing (fallback)
#
# Reference: https://cloud.tencent.com/document/api/436/7751
#
# Environment Variables:
#   TENCENT_SECRET_ID: Tencent Cloud SecretId
#   TENCENT_SECRET_KEY: Tencent Cloud SecretKey
#   TENCENT_COS_BUCKET: COS bucket name (e.g., "mybucket-1250000000")
#   TENCENT_COS_REGION: COS region (e.g., "ap-guangzhou")

import hashlib
import hmac
import os
import time
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol
import mimetypes

import httpx


# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

TENCENT_SECRET_ID_ENV = "TENCENT_SECRET_ID"
TENCENT_SECRET_KEY_ENV = "TENCENT_SECRET_KEY"
TENCENT_COS_BUCKET_ENV = "TENCENT_COS_BUCKET"
TENCENT_COS_REGION_ENV = "TENCENT_COS_REGION"

# Default timeout
HTTP_TIMEOUT = 120.0


# -----------------------------------------------------------------------------
# COS UPLOADER PROTOCOL (Interface)
# -----------------------------------------------------------------------------

class COSUploaderProtocol(Protocol):
    """Protocol defining the COS uploader interface."""
    
    def upload_file(self, file_path: Path, object_key: Optional[str] = None) -> str:
        """Upload a local file to COS and return the public URL."""
        ...
    
    def upload_bytes(self, content: bytes, object_key: str, content_type: str = "image/png") -> str:
        """Upload bytes directly to COS and return the public URL."""
        ...


# -----------------------------------------------------------------------------
# COS SIGNATURE ALGORITHM (for raw HTTP implementation)
# -----------------------------------------------------------------------------

def _sha256_hex(data: bytes) -> str:
    """Calculate SHA256 hex digest."""
    return hashlib.sha256(data).hexdigest()


def _hmac_sha1(key: bytes, msg: str) -> bytes:
    """HMAC-SHA1 signing."""
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha1).digest()


def _get_cos_authorization(
    secret_id: str,
    secret_key: str,
    method: str,
    uri: str,
    headers: dict[str, str],
    params: Optional[dict[str, str]] = None,
    sign_time: Optional[str] = None,
) -> str:
    """
    Generate COS request authorization signature.
    
    COS uses a different signature algorithm than the main Tencent Cloud API.
    Reference: https://cloud.tencent.com/document/product/436/7778
    
    Args:
        secret_id: Tencent Cloud SecretId
        secret_key: Tencent Cloud SecretKey
        method: HTTP method (GET, PUT, etc.)
        uri: Request URI path
        headers: Request headers
        params: Query parameters
        sign_time: Signature time range (e.g., "1557902800;1557910000")
        
    Returns:
        Authorization header value
    """
    if sign_time is None:
        current_time = int(time.time())
        sign_time = f"{current_time};{current_time + 3600}"
    
    # Step 1: Generate SignKey
    sign_key = hmac.new(
        secret_key.encode("utf-8"),
        sign_time.encode("utf-8"),
        hashlib.sha1,
    ).hexdigest()
    
    # Step 2: Generate UrlParamList and HttpParameters
    params = params or {}
    sorted_params = sorted(params.items())
    url_param_list = ";".join(k.lower() for k, v in sorted_params)
    http_parameters = "&".join(
        f"{urllib.parse.quote(k.lower(), safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted_params
    )
    
    # Step 3: Generate HeaderList and HttpHeaders
    # Only sign specific headers
    headers_to_sign = {
        k.lower(): v for k, v in headers.items()
        if k.lower() in ("host", "content-type", "content-length", "content-md5")
    }
    sorted_headers = sorted(headers_to_sign.items())
    header_list = ";".join(k for k, v in sorted_headers)
    http_headers = "&".join(
        f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}"
        for k, v in sorted_headers
    )
    
    # Step 4: Generate HttpString
    http_string = f"{method.lower()}\n{uri}\n{http_parameters}\n{http_headers}\n"
    
    # Step 5: Generate StringToSign
    sha1_http_string = hashlib.sha1(http_string.encode("utf-8")).hexdigest()
    string_to_sign = f"sha1\n{sign_time}\n{sha1_http_string}\n"
    
    # Step 6: Generate Signature
    signature = hmac.new(
        sign_key.encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).hexdigest()
    
    # Step 7: Generate Authorization
    authorization = (
        f"q-sign-algorithm=sha1&"
        f"q-ak={secret_id}&"
        f"q-sign-time={sign_time}&"
        f"q-key-time={sign_time}&"
        f"q-header-list={header_list}&"
        f"q-url-param-list={url_param_list}&"
        f"q-signature={signature}"
    )
    
    return authorization


# -----------------------------------------------------------------------------
# COS UPLOADER CLASS
# -----------------------------------------------------------------------------

class TencentCOSUploader:
    """
    Upload files to Tencent Cloud Object Storage (COS).
    
    This class handles uploading local images to COS and returns
    a public URL that can be used with Hunyuan 3D API.
    
    Example:
        uploader = TencentCOSUploader(
            secret_id=os.environ["TENCENT_SECRET_ID"],
            secret_key=os.environ["TENCENT_SECRET_KEY"],
            bucket="mybucket-1250000000",
            region="ap-guangzhou",
        )
        url = uploader.upload_file(Path("image.png"))
    """
    
    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
    ):
        """
        Initialize the COS uploader.
        
        Args:
            secret_id: Tencent Cloud SecretId (or use env var)
            secret_key: Tencent Cloud SecretKey (or use env var)
            bucket: COS bucket name (or use env var)
            region: COS region (or use env var)
            
        Raises:
            ValueError: If required config is missing
        """
        self.secret_id = secret_id or os.environ.get(TENCENT_SECRET_ID_ENV)
        self.secret_key = secret_key or os.environ.get(TENCENT_SECRET_KEY_ENV)
        self.bucket = bucket or os.environ.get(TENCENT_COS_BUCKET_ENV)
        self.region = region or os.environ.get(TENCENT_COS_REGION_ENV)
        
        if not self.secret_id or not self.secret_key:
            raise ValueError(
                f"Tencent Cloud credentials required. "
                f"Set {TENCENT_SECRET_ID_ENV} and {TENCENT_SECRET_KEY_ENV}."
            )
        
        if not self.bucket:
            raise ValueError(
                f"COS bucket required. Set {TENCENT_COS_BUCKET_ENV}."
            )
        
        if not self.region:
            raise ValueError(
                f"COS region required. Set {TENCENT_COS_REGION_ENV}."
            )
        
        self._client = httpx.Client(timeout=HTTP_TIMEOUT)
        self._host = f"{self.bucket}.cos.{self.region}.myqcloud.com"
    
    def upload_file(
        self,
        file_path: Path,
        object_key: Optional[str] = None,
    ) -> str:
        """
        Upload a local file to COS.
        
        Args:
            file_path: Path to the local file
            object_key: Optional custom key (defaults to filename with timestamp)
            
        Returns:
            Public URL of the uploaded file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            httpx.HTTPError: If upload fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate object key if not provided
        if object_key is None:
            timestamp = int(time.time())
            object_key = f"hunyuan3d/{timestamp}_{file_path.name}"
        
        # Ensure key starts with /
        if not object_key.startswith("/"):
            object_key = f"/{object_key}"
        
        # Read file content
        content = file_path.read_bytes()
        
        # Determine content type
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        
        # Build request headers
        headers = {
            "Host": self._host,
            "Content-Type": content_type,
            "Content-Length": str(len(content)),
        }
        
        # Generate authorization
        auth = _get_cos_authorization(
            secret_id=self.secret_id,
            secret_key=self.secret_key,
            method="PUT",
            uri=object_key,
            headers=headers,
        )
        
        headers["Authorization"] = auth
        
        # Upload the file
        url = f"https://{self._host}{object_key}"
        response = self._client.put(url, headers=headers, content=content)
        response.raise_for_status()
        
        return url
    
    def upload_bytes(
        self,
        content: bytes,
        object_key: str,
        content_type: str = "image/png",
    ) -> str:
        """
        Upload bytes directly to COS.
        
        Args:
            content: File content as bytes
            object_key: Object key in the bucket
            content_type: MIME type of the content
            
        Returns:
            Public URL of the uploaded file
        """
        # Ensure key starts with /
        if not object_key.startswith("/"):
            object_key = f"/{object_key}"
        
        # Build request headers
        headers = {
            "Host": self._host,
            "Content-Type": content_type,
            "Content-Length": str(len(content)),
        }
        
        # Generate authorization
        auth = _get_cos_authorization(
            secret_id=self.secret_id,
            secret_key=self.secret_key,
            method="PUT",
            uri=object_key,
            headers=headers,
        )
        
        headers["Authorization"] = auth
        
        # Upload
        url = f"https://{self._host}{object_key}"
        response = self._client.put(url, headers=headers, content=content)
        response.raise_for_status()
        
        return url
    
    def __del__(self):
        """Clean up the HTTP client."""
        if hasattr(self, "_client"):
            self._client.close()


class COSUploadError(Exception):
    """Exception raised when COS upload fails."""
    pass


# -----------------------------------------------------------------------------
# SDK-BASED COS UPLOADER (Recommended)
# -----------------------------------------------------------------------------

class SDKCOSUploader:
    """
    Upload files to Tencent Cloud Object Storage using the official SDK.
    
    This is the recommended implementation as it handles authentication
    and edge cases more robustly than raw HTTP requests.
    
    Requires: pip install cos-python-sdk-v5
    
    Example:
        uploader = SDKCOSUploader(
            secret_id=os.environ["TENCENT_SECRET_ID"],
            secret_key=os.environ["TENCENT_SECRET_KEY"],
            bucket="mybucket-1250000000",
            region="ap-guangzhou",
        )
        url = uploader.upload_file(Path("image.png"))
    """
    
    def __init__(
        self,
        secret_id: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket: Optional[str] = None,
        region: Optional[str] = None,
    ):
        """
        Initialize the SDK-based COS uploader.
        
        Args:
            secret_id: Tencent Cloud SecretId (or use env var)
            secret_key: Tencent Cloud SecretKey (or use env var)
            bucket: COS bucket name (or use env var)
            region: COS region (or use env var)
            
        Raises:
            ValueError: If required config is missing
            ImportError: If COS SDK is not installed
        """
        self.secret_id = secret_id or os.environ.get(TENCENT_SECRET_ID_ENV)
        self.secret_key = secret_key or os.environ.get(TENCENT_SECRET_KEY_ENV)
        self.bucket = bucket or os.environ.get(TENCENT_COS_BUCKET_ENV)
        self.region = region or os.environ.get(TENCENT_COS_REGION_ENV)
        
        if not self.secret_id or not self.secret_key:
            raise ValueError(
                f"Tencent Cloud credentials required. "
                f"Set {TENCENT_SECRET_ID_ENV} and {TENCENT_SECRET_KEY_ENV}."
            )
        
        if not self.bucket:
            raise ValueError(
                f"COS bucket required. Set {TENCENT_COS_BUCKET_ENV}."
            )
        
        if not self.region:
            raise ValueError(
                f"COS region required. Set {TENCENT_COS_REGION_ENV}."
            )
        
        # Initialize the SDK client
        try:
            from qcloud_cos import CosConfig, CosS3Client
        except ImportError:
            raise ImportError(
                "COS SDK not installed. Install with: uv add cos-python-sdk-v5"
            )
        
        config = CosConfig(
            Region=self.region,
            SecretId=self.secret_id,
            SecretKey=self.secret_key,
            Token=None,
            Scheme='https',
        )
        self._client = CosS3Client(config)
        self._host = f"{self.bucket}.cos.{self.region}.myqcloud.com"
    
    def upload_file(
        self,
        file_path: Path,
        object_key: Optional[str] = None,
    ) -> str:
        """
        Upload a local file to COS.
        
        Args:
            file_path: Path to the local file
            object_key: Optional custom key (defaults to filename with timestamp)
            
        Returns:
            Public URL of the uploaded file
            
        Raises:
            FileNotFoundError: If file doesn't exist
            COSUploadError: If upload fails
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Generate object key if not provided
        if object_key is None:
            timestamp = int(time.time())
            object_key = f"hunyuan3d/{timestamp}_{file_path.name}"
        
        # Remove leading slash if present (SDK doesn't want it)
        if object_key.startswith("/"):
            object_key = object_key[1:]
        
        # Determine content type
        content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
        
        try:
            # Use put_object for simpler upload (avoids multipart complexity)
            # Set ACL to public-read so Hunyuan 3D API can access the file
            with open(file_path, 'rb') as fp:
                self._client.put_object(
                    Bucket=self.bucket,
                    Key=object_key,
                    Body=fp,
                    ContentType=content_type,
                    ACL='public-read',
                )
        except Exception as e:
            raise COSUploadError(f"Failed to upload {file_path}: {e}") from e
        
        return f"https://{self._host}/{object_key}"
    
    def upload_bytes(
        self,
        content: bytes,
        object_key: str,
        content_type: str = "image/png",
    ) -> str:
        """
        Upload bytes directly to COS.
        
        Args:
            content: File content as bytes
            object_key: Object key in the bucket
            content_type: MIME type of the content
            
        Returns:
            Public URL of the uploaded file
            
        Raises:
            COSUploadError: If upload fails
        """
        # Remove leading slash if present
        if object_key.startswith("/"):
            object_key = object_key[1:]
        
        try:
            from io import BytesIO
            # Set ACL to public-read so Hunyuan 3D API can access the file
            self._client.put_object(
                Bucket=self.bucket,
                Body=BytesIO(content),
                Key=object_key,
                ContentType=content_type,
                ACL='public-read',
            )
        except Exception as e:
            raise COSUploadError(f"Failed to upload bytes to {object_key}: {e}") from e
        
        return f"https://{self._host}/{object_key}"


# -----------------------------------------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------------------------------------

def get_cos_uploader(use_sdk: bool = True) -> COSUploaderProtocol:
    """
    Get the appropriate COS uploader based on preference.
    
    Args:
        use_sdk: If True, use SDK-based uploader (recommended).
                 If False, use raw HTTP uploader.
                 
    Returns:
        COS uploader instance
        
    Note:
        If use_sdk=True but SDK is not installed, will fall back to raw HTTP.
    """
    if use_sdk:
        try:
            return SDKCOSUploader()
        except ImportError:
            # Fall back to raw HTTP if SDK not installed
            pass
    
    return TencentCOSUploader()