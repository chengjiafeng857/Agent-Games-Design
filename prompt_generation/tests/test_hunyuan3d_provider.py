# test_hunyuan3d_provider.py - Tests for Hunyuan 3D provider

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import httpx

# Import the classes we're testing
from src.providers.hunyuan3d_provider import (
    JobStatus,
    Hunyuan3DFile,
    Hunyuan3DJobResult,
    Hunyuan3DAPIError,
)
from src.providers.raw_http_hunyuan3d import (
    RawHttpHunyuan3DProvider,
    _get_tc3_signature,
)


class TestTC3Signature:
    """Tests for the TC3-HMAC-SHA256 signature algorithm."""
    
    def test_signature_generation(self):
        """Test that signature headers are generated correctly."""
        headers = _get_tc3_signature(
            secret_id="test-id",
            secret_key="test-key",
            service="ai3d",
            host="ai3d.tencentcloudapi.com",
            action="SubmitHunyuanTo3DProJob",
            payload='{"Prompt": "test"}',
            timestamp=1700000000,
        )
        
        # Check required headers are present
        assert "Authorization" in headers
        assert "X-TC-Action" in headers
        assert "X-TC-Timestamp" in headers
        assert "X-TC-Version" in headers
        assert "X-TC-Region" in headers
        
        # Check authorization format
        assert headers["Authorization"].startswith("TC3-HMAC-SHA256")
        assert "Credential=" in headers["Authorization"]
        assert "Signature=" in headers["Authorization"]
        
        # Check other headers
        assert headers["X-TC-Action"] == "SubmitHunyuanTo3DProJob"
        assert headers["X-TC-Timestamp"] == "1700000000"


class TestRawHttpHunyuan3DProvider:
    """Tests for the raw HTTP Hunyuan 3D provider."""
    
    def test_init_with_env_vars(self, mock_env_vars):
        """Test provider initialization from environment variables."""
        provider = RawHttpHunyuan3DProvider()
        assert provider.secret_id == "test-secret-id"
        assert provider.secret_key == "test-secret-key"
    
    def test_init_with_explicit_credentials(self):
        """Test provider initialization with explicit credentials."""
        provider = RawHttpHunyuan3DProvider(
            secret_id="explicit-id",
            secret_key="explicit-key",
        )
        assert provider.secret_id == "explicit-id"
        assert provider.secret_key == "explicit-key"
    
    def test_init_missing_credentials(self, monkeypatch):
        """Test that missing credentials raise ValueError."""
        monkeypatch.delenv("TENCENT_SECRET_ID", raising=False)
        monkeypatch.delenv("TENCENT_SECRET_KEY", raising=False)
        
        with pytest.raises(ValueError) as exc_info:
            RawHttpHunyuan3DProvider()
        
        assert "credentials required" in str(exc_info.value).lower()
    
    def test_submit_validation_neither_input(self, mock_env_vars):
        """Test submit raises error when no input provided."""
        provider = RawHttpHunyuan3DProvider()
        
        with pytest.raises(ValueError) as exc_info:
            provider.submit()
        
        assert "must provide either" in str(exc_info.value).lower()
    
    def test_submit_validation_both_inputs(self, mock_env_vars):
        """Test submit raises error when both inputs provided."""
        provider = RawHttpHunyuan3DProvider()
        
        with pytest.raises(ValueError) as exc_info:
            provider.submit(prompt="test", image_url="https://example.com/img.png")
        
        assert "exactly one" in str(exc_info.value).lower()
    
    def test_submit_with_prompt(self, mock_env_vars, mock_submit_response):
        """Test successful job submission with prompt."""
        provider = RawHttpHunyuan3DProvider()
        
        # Mock the HTTP client
        with patch.object(provider, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_submit_response
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            
            job_id = provider.submit(prompt="A cute panda")
            
            assert job_id == "test-job-123"
            mock_client.post.assert_called_once()
    
    def test_submit_with_image_url(self, mock_env_vars, mock_submit_response):
        """Test successful job submission with image URL."""
        provider = RawHttpHunyuan3DProvider()
        
        with patch.object(provider, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_submit_response
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            
            job_id = provider.submit(image_url="https://example.com/image.png")
            
            assert job_id == "test-job-123"
    
    def test_poll_done(self, mock_env_vars, mock_poll_done_response):
        """Test polling a completed job."""
        provider = RawHttpHunyuan3DProvider()
        
        with patch.object(provider, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_poll_done_response
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            
            result = provider.poll("test-job-123")
            
            assert result.status == JobStatus.DONE
            assert result.job_id == "test-job-123"
            assert len(result.files) == 2
            assert result.files[0].file_type == "OBJ"
    
    def test_poll_fail(self, mock_env_vars, mock_poll_fail_response):
        """Test polling a failed job."""
        provider = RawHttpHunyuan3DProvider()
        
        with patch.object(provider, "_client") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_poll_fail_response
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            
            result = provider.poll("test-job-123")
            
            assert result.status == JobStatus.FAIL
            assert result.error_code == "GenerationFailed"
            assert result.error_message == "Model generation failed"
    
    def test_download_result(
        self,
        mock_env_vars,
        temp_output_dir,
        sample_zip_bytes,
    ):
        """Test downloading and extracting results."""
        provider = RawHttpHunyuan3DProvider()
        
        # Create a mock result
        result = Hunyuan3DJobResult(
            job_id="test-job-123",
            status=JobStatus.DONE,
            files=[
                Hunyuan3DFile(
                    file_type="OBJ",
                    url="https://example.com/model.zip",
                ),
            ],
        )
        
        with patch.object(provider, "_client") as mock_client:
            # Mock the download response
            mock_response = MagicMock()
            mock_response.content = sample_zip_bytes
            mock_response.raise_for_status = MagicMock()
            mock_client.get.return_value = mock_response
            
            downloaded = provider.download_result(result, temp_output_dir)
            
            # Should have extracted files from the ZIP
            assert len(downloaded) > 0
            
            # Check for .obj files
            obj_files = [f for f in downloaded if f.suffix == ".obj"]
            assert len(obj_files) > 0
    
    def test_download_result_not_done(self, mock_env_vars, temp_output_dir):
        """Test download raises error for non-DONE status."""
        provider = RawHttpHunyuan3DProvider()
        
        result = Hunyuan3DJobResult(
            job_id="test-job-123",
            status=JobStatus.WAIT,
        )
        
        with pytest.raises(ValueError) as exc_info:
            provider.download_result(result, temp_output_dir)
        
        assert "cannot download" in str(exc_info.value).lower()
    
    def test_extract_zip(self, mock_env_vars, temp_output_dir, sample_zip_bytes):
        """Test ZIP extraction."""
        provider = RawHttpHunyuan3DProvider()
        
        extracted = provider._extract_zip(sample_zip_bytes, temp_output_dir)
        
        # Should extract all files
        assert len(extracted) == 4  # model.obj, material.mtl, texture.png, accessory.obj
        
        # Check file names
        names = {f.name for f in extracted}
        assert "model.obj" in names
        assert "material.mtl" in names
        assert "texture.png" in names
        assert "accessory.obj" in names


class TestJobStatus:
    """Tests for JobStatus enum."""
    
    def test_status_values(self):
        """Test that all expected status values exist."""
        assert JobStatus.WAIT.value == "WAIT"
        assert JobStatus.RUN.value == "RUN"
        assert JobStatus.DONE.value == "DONE"
        assert JobStatus.FAIL.value == "FAIL"


class TestHunyuan3DAPIError:
    """Tests for Hunyuan3DAPIError exception."""
    
    def test_error_with_all_fields(self):
        """Test error with all fields set."""
        error = Hunyuan3DAPIError(
            message="Test error",
            code="TestCode",
            request_id="req-123",
        )
        
        assert error.code == "TestCode"
        assert error.request_id == "req-123"
        assert "Test error" in str(error)
        assert "TestCode" in str(error)
        assert "req-123" in str(error)
    
    def test_error_minimal(self):
        """Test error with only message."""
        error = Hunyuan3DAPIError(message="Simple error")
        
        assert error.code is None
        assert error.request_id is None
        assert "Simple error" in str(error)


class TestSDKAvailability:
    """Tests for SDK availability checking."""
    
    def test_is_sdk_available_returns_bool(self):
        """Test that is_sdk_available returns a boolean."""
        from src.providers.sdk_hunyuan3d import is_sdk_available
        result = is_sdk_available()
        assert isinstance(result, bool)
    
    def test_get_sdk_install_instructions(self):
        """Test that install instructions are helpful."""
        from src.providers.sdk_hunyuan3d import get_sdk_install_instructions
        instructions = get_sdk_install_instructions()
        assert "tencentcloud-sdk-python-ai3d" in instructions
        assert "uv add" in instructions or "pip install" in instructions


class TestGetProvider:
    """Tests for get_provider factory function."""
    
    def test_get_http_provider(self, mock_env_vars):
        """Test getting the HTTP provider."""
        from src.providers import get_provider, RawHttpHunyuan3DProvider
        provider_class = get_provider("http")
        assert provider_class == RawHttpHunyuan3DProvider
    
    def test_get_invalid_provider(self):
        """Test that invalid provider type raises ValueError."""
        from src.providers import get_provider
        with pytest.raises(ValueError) as exc_info:
            get_provider("invalid")
        assert "invalid" in str(exc_info.value).lower()
    
    def test_get_sdk_provider_without_sdk(self):
        """Test that SDK provider raises ImportError if SDK not installed."""
        from src.providers import get_provider, is_sdk_available
        if not is_sdk_available():
            with pytest.raises(ImportError) as exc_info:
                get_provider("sdk")
            assert "sdk" in str(exc_info.value).lower()
