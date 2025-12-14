# conftest.py - Pytest fixtures for Hunyuan 3D tests

import io
import json
import zipfile
from pathlib import Path
from typing import Generator

import pytest


# -----------------------------------------------------------------------------
# SYNTHETIC TEST DATA
# -----------------------------------------------------------------------------

SAMPLE_OBJ_CONTENT = b"""# Simple test OBJ file
# Cube vertices
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
v 0.0 0.0 1.0
v 1.0 0.0 1.0
v 1.0 1.0 1.0
v 0.0 1.0 1.0

# Faces
f 1 2 3 4
f 5 6 7 8
f 1 2 6 5
f 2 3 7 6
f 3 4 8 7
f 4 1 5 8
"""

SAMPLE_MTL_CONTENT = b"""# Simple test MTL file
newmtl material_0
Ka 0.2 0.2 0.2
Kd 0.8 0.8 0.8
Ks 1.0 1.0 1.0
d 1.0
illum 2
"""

# Larger OBJ (main model)
LARGE_OBJ_CONTENT = SAMPLE_OBJ_CONTENT * 10  # 10x larger


# -----------------------------------------------------------------------------
# FIXTURES
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_obj_bytes() -> bytes:
    """Return sample OBJ file content."""
    return SAMPLE_OBJ_CONTENT


@pytest.fixture
def sample_mtl_bytes() -> bytes:
    """Return sample MTL file content."""
    return SAMPLE_MTL_CONTENT


@pytest.fixture
def sample_zip_bytes() -> bytes:
    """
    Create a synthetic ZIP file containing:
    - model.obj (larger, main model)
    - material.mtl
    - texture.png (small dummy)
    - accessory.obj (smaller)
    """
    buffer = io.BytesIO()
    
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        # Main model (larger)
        zf.writestr("model.obj", LARGE_OBJ_CONTENT)
        
        # Material file
        zf.writestr("material.mtl", SAMPLE_MTL_CONTENT)
        
        # Small texture (fake PNG header)
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        zf.writestr("texture.png", fake_png)
        
        # Smaller accessory OBJ
        zf.writestr("accessory.obj", SAMPLE_OBJ_CONTENT)
    
    return buffer.getvalue()


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def mock_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set mock environment variables for Tencent Cloud."""
    monkeypatch.setenv("TENCENT_SECRET_ID", "test-secret-id")
    monkeypatch.setenv("TENCENT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("TENCENT_COS_BUCKET", "test-bucket-1250000000")
    monkeypatch.setenv("TENCENT_COS_REGION", "ap-guangzhou")


# -----------------------------------------------------------------------------
# MOCK API RESPONSES
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_submit_response() -> dict:
    """Mock response for SubmitHunyuanTo3DProJob."""
    return {
        "Response": {
            "JobId": "test-job-123",
            "RequestId": "req-456",
        }
    }


@pytest.fixture
def mock_poll_wait_response() -> dict:
    """Mock response for QueryHunyuanTo3DProJob (waiting)."""
    return {
        "Response": {
            "Status": "WAIT",
            "RequestId": "req-789",
        }
    }


@pytest.fixture
def mock_poll_run_response() -> dict:
    """Mock response for QueryHunyuanTo3DProJob (running)."""
    return {
        "Response": {
            "Status": "RUN",
            "RequestId": "req-789",
        }
    }


@pytest.fixture
def mock_poll_done_response() -> dict:
    """Mock response for QueryHunyuanTo3DProJob (done)."""
    return {
        "Response": {
            "Status": "DONE",
            "RequestId": "req-789",
            "ResultFile3Ds": [
                {
                    "Type": "OBJ",
                    "Url": "https://example.com/model.zip",
                    "PreviewImageUrl": "https://example.com/preview.png",
                },
                {
                    "Type": "GLB",
                    "Url": "https://example.com/model.glb",
                },
            ],
        }
    }


@pytest.fixture
def mock_poll_fail_response() -> dict:
    """Mock response for QueryHunyuanTo3DProJob (failed)."""
    return {
        "Response": {
            "Status": "FAIL",
            "ErrorCode": "GenerationFailed",
            "ErrorMessage": "Model generation failed",
            "RequestId": "req-789",
        }
    }
