# src/providers/__init__.py - Hunyuan 3D Provider Package
#
# This package contains provider implementations for the Hunyuan 3D API.
# The provider abstraction allows for different implementations:
#   - sdk: Uses official Tencent Cloud SDK (default, recommended)
#   - http: Direct HTTP calls with Tencent Cloud signing (fallback)

from .hunyuan3d_provider import (
    Hunyuan3DProvider,
    Hunyuan3DJobResult,
    Hunyuan3DFile,
    Hunyuan3DAPIError,
    JobStatus,
    ViewImage,
    VALID_VIEW_TYPES,
)

from .raw_http_hunyuan3d import (
    RawHttpHunyuan3DProvider,
    TENCENT_SECRET_ID_ENV,
    TENCENT_SECRET_KEY_ENV,
    # Hunyuan 3D settings env vars
    HUNYUAN3D_ENABLE_PBR_ENV,
    HUNYUAN3D_FACE_COUNT_ENV,
    HUNYUAN3D_GENERATE_TYPE_ENV,
    HUNYUAN3D_POLYGON_TYPE_ENV,
    VALID_GENERATE_TYPES,
    VALID_POLYGON_TYPES,
)

from .tencent_cos import (
    TencentCOSUploader,
    SDKCOSUploader,
    get_cos_uploader,
    TENCENT_COS_BUCKET_ENV,
    TENCENT_COS_REGION_ENV,
    COSUploadError,
)

from .sdk_hunyuan3d import (
    SDKHunyuan3DProvider,
    is_sdk_available,
    get_sdk_install_instructions,
)

__all__ = [
    # Provider abstraction
    "Hunyuan3DProvider",
    "Hunyuan3DJobResult",
    "Hunyuan3DFile",
    "Hunyuan3DAPIError",
    "JobStatus",
    "ViewImage",
    "VALID_VIEW_TYPES",
    # SDK implementation (default, recommended)
    "SDKHunyuan3DProvider",
    "is_sdk_available",
    "get_sdk_install_instructions",
    # Raw HTTP implementation (fallback)
    "RawHttpHunyuan3DProvider",
    "TENCENT_SECRET_ID_ENV",
    "TENCENT_SECRET_KEY_ENV",
    # Hunyuan 3D settings env vars
    "HUNYUAN3D_ENABLE_PBR_ENV",
    "HUNYUAN3D_FACE_COUNT_ENV",
    "HUNYUAN3D_GENERATE_TYPE_ENV",
    "HUNYUAN3D_POLYGON_TYPE_ENV",
    "VALID_GENERATE_TYPES",
    "VALID_POLYGON_TYPES",
    # COS uploader (SDK-based by default)
    "TencentCOSUploader",
    "SDKCOSUploader",
    "get_cos_uploader",
    "TENCENT_COS_BUCKET_ENV",
    "TENCENT_COS_REGION_ENV",
    "COSUploadError",
]


def get_provider(provider_type: str = "sdk") -> type[Hunyuan3DProvider]:
    """
    Get the appropriate provider class based on type.
    
    Args:
        provider_type: "sdk" (default, recommended) or "http" (fallback)
        
    Returns:
        Provider class to instantiate
        
    Raises:
        ValueError: If provider type is invalid
        ImportError: If SDK provider requested but SDK not installed
    """
    if provider_type == "sdk":
        if not is_sdk_available():
            raise ImportError(get_sdk_install_instructions())
        return SDKHunyuan3DProvider
    elif provider_type == "http":
        return RawHttpHunyuan3DProvider
    else:
        raise ValueError(
            f"Invalid provider type: {provider_type}. "
            f"Use 'sdk' (default) or 'http'."
        )
