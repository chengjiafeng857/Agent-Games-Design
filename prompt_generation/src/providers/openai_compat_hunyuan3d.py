# openai_compat_hunyuan3d.py - OpenAI-Compatible Hunyuan 3D Provider (Stub)
#
# This module provides an OpenAI-compatible interface for Hunyuan 3D.
#
# IMPORTANT: As of the current API documentation, the Hunyuan 3D API
# is NOT OpenAI-compatible. It uses Tencent Cloud's proprietary
# TC3-HMAC-SHA256 authentication, not Bearer token auth.
#
# This stub is provided for:
#   1. Future compatibility if Tencent adds OpenAI-compatible endpoints
#   2. Clear documentation of why the OpenAI client cannot be used
#
# For now, use RawHttpHunyuan3DProvider instead.

from pathlib import Path
from typing import Optional

from .hunyuan3d_provider import (
    Hunyuan3DProvider,
    Hunyuan3DJobResult,
    Hunyuan3DAPIError,
)


class OpenAICompatHunyuan3DProvider(Hunyuan3DProvider):
    """
    OpenAI-compatible Hunyuan 3D provider.
    
    IMPORTANT: The Hunyuan 3D API is NOT currently OpenAI-compatible.
    This class will raise NotImplementedError for all methods.
    
    The Tencent Cloud Hunyuan 3D API uses:
        - TC3-HMAC-SHA256 signature authentication
        - Proprietary request/response format
        - Action-based endpoints (not /v1/* routes)
    
    If Tencent adds OpenAI-compatible endpoints in the future,
    this class can be updated to use the `openai` library with
    custom `base_url` and `api_key`.
    
    For now, use `RawHttpHunyuan3DProvider` instead.
    
    Example of what WOULD work if it were OpenAI-compatible:
        from openai import OpenAI
        
        client = OpenAI(
            base_url=os.environ.get("HUNYUAN_BASE_URL"),
            api_key=os.environ.get("HUNYUAN_API_KEY"),
        )
    """
    
    _NOT_COMPATIBLE_MESSAGE = (
        "The Hunyuan 3D API is NOT OpenAI-compatible. "
        "It uses Tencent Cloud's TC3-HMAC-SHA256 authentication, "
        "not Bearer token authentication. "
        "Use RawHttpHunyuan3DProvider instead."
    )
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the OpenAI-compatible provider.
        
        Note: This will raise NotImplementedError on any method call
        because Hunyuan 3D is not currently OpenAI-compatible.
        
        Args:
            base_url: Would be the API base URL (HUNYUAN_BASE_URL)
            api_key: Would be the API key (HUNYUAN_API_KEY)
            model: Would be the model name (HUNYUAN_MODEL)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        
        # Log a warning that this provider is not available
        import logging
        logging.warning(self._NOT_COMPATIBLE_MESSAGE)
    
    def submit(
        self,
        *,
        prompt: Optional[str] = None,
        image_url: Optional[str] = None,
    ) -> str:
        """Not implemented - Hunyuan 3D is not OpenAI-compatible."""
        raise NotImplementedError(self._NOT_COMPATIBLE_MESSAGE)
    
    def poll(self, job_id: str) -> Hunyuan3DJobResult:
        """Not implemented - Hunyuan 3D is not OpenAI-compatible."""
        raise NotImplementedError(self._NOT_COMPATIBLE_MESSAGE)
    
    def download_result(
        self,
        result: Hunyuan3DJobResult,
        output_dir: Path,
    ) -> list[Path]:
        """Not implemented - Hunyuan 3D is not OpenAI-compatible."""
        raise NotImplementedError(self._NOT_COMPATIBLE_MESSAGE)


def check_openai_compatibility() -> bool:
    """
    Check if Hunyuan 3D has OpenAI-compatible endpoints.
    
    As of the current documentation, it does NOT.
    This function is provided for future compatibility checks.
    
    Returns:
        False - Hunyuan 3D is not OpenAI-compatible
    """
    return False
