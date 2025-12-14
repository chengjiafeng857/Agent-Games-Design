# test_stage5_hunyuan3d.py - Tests for Stage 5 orchestration

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.stage5_hunyuan3d import (
    generate_3d_model,
    _find_largest_obj,
    _validate_inputs,
    check_required_env_vars,
    Hunyuan3DResult,
)
from src.providers import JobStatus, Hunyuan3DJobResult, Hunyuan3DFile


class TestValidateInputs:
    """Tests for input validation."""
    
    def test_prompt_only(self):
        """Test validation with prompt only."""
        input_type, input_value = _validate_inputs(
            prompt="test prompt",
            image=None,
            image_url=None,
        )
        assert input_type == "prompt"
        assert input_value == "test prompt"
    
    def test_image_only(self, tmp_path):
        """Test validation with image only."""
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake image")
        
        input_type, input_value = _validate_inputs(
            prompt=None,
            image=image_path,
            image_url=None,
        )
        assert input_type == "image"
        assert str(image_path) in input_value
    
    def test_image_url_only(self):
        """Test validation with image URL only."""
        input_type, input_value = _validate_inputs(
            prompt=None,
            image=None,
            image_url="https://example.com/image.png",
        )
        assert input_type == "image_url"
        assert input_value == "https://example.com/image.png"
    
    def test_no_inputs(self):
        """Test validation fails with no inputs."""
        with pytest.raises(ValueError) as exc_info:
            _validate_inputs(prompt=None, image=None, image_url=None)
        assert "must provide exactly one" in str(exc_info.value).lower()
    
    def test_multiple_inputs(self, tmp_path):
        """Test validation fails with multiple inputs."""
        image_path = tmp_path / "test.png"
        image_path.write_bytes(b"fake")
        
        with pytest.raises(ValueError) as exc_info:
            _validate_inputs(
                prompt="test",
                image=image_path,
                image_url=None,
            )
        assert "only one input" in str(exc_info.value).lower()


class TestFindLargestObj:
    """Tests for finding the largest .obj file."""
    
    def test_single_obj(self, tmp_path):
        """Test with a single .obj file."""
        obj_file = tmp_path / "model.obj"
        obj_file.write_bytes(b"test content")
        
        result = _find_largest_obj([obj_file])
        assert result == obj_file
    
    def test_multiple_objs_different_sizes(self, tmp_path):
        """Test selecting the largest .obj from multiple."""
        small_obj = tmp_path / "small.obj"
        small_obj.write_bytes(b"small")
        
        large_obj = tmp_path / "large.obj"
        large_obj.write_bytes(b"this is a much larger obj file content")
        
        medium_obj = tmp_path / "medium.obj"
        medium_obj.write_bytes(b"medium content")
        
        result = _find_largest_obj([small_obj, large_obj, medium_obj])
        assert result == large_obj
    
    def test_no_obj_files(self, tmp_path):
        """Test with no .obj files."""
        mtl_file = tmp_path / "material.mtl"
        mtl_file.write_bytes(b"mtl content")
        
        result = _find_largest_obj([mtl_file])
        assert result is None
    
    def test_empty_list(self):
        """Test with empty file list."""
        result = _find_largest_obj([])
        assert result is None
    
    def test_mixed_extensions(self, tmp_path):
        """Test with mixed file extensions."""
        obj_file = tmp_path / "model.obj"
        obj_file.write_bytes(b"obj content here")
        
        mtl_file = tmp_path / "material.mtl"
        mtl_file.write_bytes(b"mtl content that is longer than obj")
        
        png_file = tmp_path / "texture.png"
        png_file.write_bytes(b"png")
        
        # Should return the .obj even though .mtl is larger
        result = _find_largest_obj([obj_file, mtl_file, png_file])
        assert result == obj_file


class TestCheckRequiredEnvVars:
    """Tests for environment variable checking."""
    
    def test_all_vars_set(self, mock_env_vars):
        """Test when all required vars are set."""
        missing = check_required_env_vars(include_cos=False)
        assert missing == []
    
    def test_all_vars_with_cos(self, mock_env_vars):
        """Test when all vars including COS are set."""
        missing = check_required_env_vars(include_cos=True)
        assert missing == []
    
    def test_missing_secret_id(self, monkeypatch):
        """Test detection of missing SECRET_ID."""
        monkeypatch.delenv("TENCENT_SECRET_ID", raising=False)
        monkeypatch.setenv("TENCENT_SECRET_KEY", "test-key")
        
        missing = check_required_env_vars(include_cos=False)
        assert "TENCENT_SECRET_ID" in missing
    
    def test_missing_cos_vars(self, monkeypatch):
        """Test detection of missing COS vars."""
        monkeypatch.setenv("TENCENT_SECRET_ID", "test-id")
        monkeypatch.setenv("TENCENT_SECRET_KEY", "test-key")
        monkeypatch.delenv("TENCENT_COS_BUCKET", raising=False)
        monkeypatch.delenv("TENCENT_COS_REGION", raising=False)
        
        missing = check_required_env_vars(include_cos=True)
        assert "TENCENT_COS_BUCKET" in missing
        assert "TENCENT_COS_REGION" in missing


class TestGenerate3DModel:
    """Tests for the main orchestration function."""
    
    def test_successful_generation(
        self,
        mock_env_vars,
        temp_output_dir,
        sample_zip_bytes,
    ):
        """Test successful 3D model generation."""
        with patch("src.stage5_hunyuan3d.get_provider") as mock_get_provider:
            # Setup mock provider
            mock_provider = MagicMock()
            mock_get_provider.return_value = MagicMock(return_value=mock_provider)
            
            # Mock submit
            mock_provider.submit.return_value = "test-job-123"
            
            # Mock poll to return DONE
            mock_poll_result = Hunyuan3DJobResult(
                job_id="test-job-123",
                status=JobStatus.DONE,
                files=[
                    Hunyuan3DFile(
                        file_type="OBJ",
                        url="https://example.com/model.zip",
                    ),
                ],
            )
            mock_provider.poll.return_value = mock_poll_result
            
            # Mock download to create actual files
            def mock_download(result, output_dir):
                obj_file = output_dir / "model.obj"
                obj_file.write_bytes(b"obj content")
                return [obj_file]
            
            mock_provider.download_result.side_effect = mock_download
            
            # Run the function
            result = generate_3d_model(
                prompt="test prompt",
                output_dir=temp_output_dir,
                poll_interval=0.1,
                timeout=5,
                verbose=False,
            )
            
            # Verify result
            assert result.status == "DONE"
            assert result.job_id == "test-job-123"
            assert result.obj_path is not None
            assert result.obj_path.name == "model.obj"
            assert result.metadata_path is not None
            
            # Verify metadata file was created
            assert result.metadata_path.exists()
            metadata = json.loads(result.metadata_path.read_text())
            assert metadata["job_id"] == "test-job-123"
            assert metadata["status"] == "DONE"
    
    def test_failed_generation(self, mock_env_vars, temp_output_dir):
        """Test handling of failed generation."""
        with patch("src.stage5_hunyuan3d.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_get_provider.return_value = MagicMock(return_value=mock_provider)
            
            mock_provider.submit.return_value = "test-job-123"
            
            # Mock poll to return FAIL
            mock_poll_result = Hunyuan3DJobResult(
                job_id="test-job-123",
                status=JobStatus.FAIL,
                error_code="GenerationFailed",
                error_message="Test failure",
            )
            mock_provider.poll.return_value = mock_poll_result
            
            result = generate_3d_model(
                prompt="test prompt",
                output_dir=temp_output_dir,
                poll_interval=0.1,
                timeout=5,
                verbose=False,
            )
            
            assert result.status == "FAIL"
            assert result.error_message == "Test failure"
            assert result.obj_path is None
    
    def test_timeout(self, mock_env_vars, temp_output_dir):
        """Test timeout handling."""
        with patch("src.stage5_hunyuan3d.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_get_provider.return_value = MagicMock(return_value=mock_provider)
            
            mock_provider.submit.return_value = "test-job-123"
            
            # Mock poll to always return WAIT
            mock_poll_result = Hunyuan3DJobResult(
                job_id="test-job-123",
                status=JobStatus.WAIT,
            )
            mock_provider.poll.return_value = mock_poll_result
            
            with pytest.raises(TimeoutError):
                generate_3d_model(
                    prompt="test prompt",
                    output_dir=temp_output_dir,
                    poll_interval=0.1,
                    timeout=0.5,  # Very short timeout
                    verbose=False,
                )
    
    def test_image_upload_flow(self, mock_env_vars, temp_output_dir, tmp_path):
        """Test that image upload is called for local images."""
        # Create a test image
        image_path = tmp_path / "test_image.png"
        image_path.write_bytes(b"fake image content")
        
        with patch("src.stage5_hunyuan3d.get_provider") as mock_get_provider, \
             patch("src.stage5_hunyuan3d.get_cos_uploader") as mock_get_cos_uploader:
            
            # Setup mock provider
            mock_provider = MagicMock()
            mock_get_provider.return_value = MagicMock(return_value=mock_provider)
            mock_provider.submit.return_value = "test-job-123"
            
            mock_poll_result = Hunyuan3DJobResult(
                job_id="test-job-123",
                status=JobStatus.DONE,
                files=[],
            )
            mock_provider.poll.return_value = mock_poll_result
            mock_provider.download_result.return_value = []
            
            # Setup mock COS uploader
            mock_uploader = MagicMock()
            mock_get_cos_uploader.return_value = mock_uploader
            mock_uploader.upload_file.return_value = "https://cos.example.com/image.png"
            
            result = generate_3d_model(
                image=image_path,
                output_dir=temp_output_dir,
                poll_interval=0.1,
                timeout=5,
                verbose=False,
            )
            
            # Verify uploader was called
            mock_uploader.upload_file.assert_called_once()
            
            # Verify submit was called with image_url (not prompt)
            mock_provider.submit.assert_called_once()
            call_kwargs = mock_provider.submit.call_args.kwargs
            assert call_kwargs.get("image_url") == "https://cos.example.com/image.png"
            assert call_kwargs.get("prompt") is None
    
    def test_provider_selection(self, mock_env_vars, temp_output_dir):
        """Test that provider_type selects the correct provider."""
        with patch("src.stage5_hunyuan3d.get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_get_provider.return_value = MagicMock(return_value=mock_provider)
            
            mock_provider.submit.return_value = "test-job-123"
            mock_provider.poll.return_value = Hunyuan3DJobResult(
                job_id="test-job-123",
                status=JobStatus.DONE,
                files=[],
            )
            mock_provider.download_result.return_value = []
            
            generate_3d_model(
                prompt="test",
                output_dir=temp_output_dir,
                poll_interval=0.1,
                timeout=5,
                verbose=False,
                provider_type="http",
            )
            
            # Verify get_provider was called with correct type
            mock_get_provider.assert_called_once_with("http")


class TestHunyuan3DResult:
    """Tests for the result dataclass."""
    
    def test_default_values(self):
        """Test default values are set correctly."""
        result = Hunyuan3DResult(
            job_id="test",
            status="DONE",
        )
        assert result.all_files == []
        assert result.obj_path is None
        assert result.metadata_path is None
        assert result.error_message is None
        assert result.elapsed_seconds == 0.0
