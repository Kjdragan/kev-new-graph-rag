"""
Unit tests for GDriveReader module.

These tests focus on the GDriveReader functionality, mocking the Google Drive API
to test different response scenarios and error conditions.
"""
import io
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

# Add project root to path to ensure imports work
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.gdrive_reader import GDriveReader
from utils.config_models import GDriveReaderConfig

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit

@pytest.fixture
def mock_credentials_path(tmp_path):
    """Create a temporary credentials file for testing."""
    creds_path = tmp_path / "mock_credentials.json"
    with open(creds_path, 'w') as f:
        f.write('{"type": "service_account", "project_id": "mock-project"}')
    return str(creds_path)

@pytest.fixture
def gdrive_config(mock_credentials_path):
    """Create a GDriveReaderConfig with test values."""
    return GDriveReaderConfig(
        credentials_path=mock_credentials_path,
        folder_id="test_folder_id",
        impersonated_user_email="test@example.com"
    )

@pytest.fixture
def mock_drive_service():
    """Mock Google Drive service."""
    with patch("utils.gdrive_reader.build") as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        yield mock_service

@pytest.fixture
def gdrive_reader(gdrive_config, mock_drive_service):
    """Create a GDriveReader instance with mocked dependencies."""
    with patch("utils.gdrive_reader.service_account.Credentials.from_service_account_file") as mock_creds:
        mock_creds.return_value = MagicMock()
        mock_creds.return_value.with_subject.return_value = MagicMock()
        
        reader = GDriveReader(gdrive_config)
        # Force initialization of drive_service
        reader._drive_service = mock_drive_service
        return reader


class TestGDriveReader:
    """Test cases for GDriveReader class."""

    def test_initialization_with_valid_credentials(self, mock_credentials_path):
        """Test initialization with valid credentials path."""
        config = GDriveReaderConfig(
            credentials_path=mock_credentials_path,
            folder_id="test_folder_id"
        )
        reader = GDriveReader(config)
        assert reader.config.credentials_path == mock_credentials_path
        assert reader.config.folder_id == "test_folder_id"
        assert reader.config.impersonated_user_email is None

    def test_initialization_with_nonexistent_credentials(self, tmp_path):
        """Test initialization with nonexistent credentials shows warning but doesn't fail."""
        nonexistent_path = str(tmp_path / "nonexistent.json")
        config = GDriveReaderConfig(
            credentials_path=nonexistent_path,
            folder_id="test_folder_id"
        )
        
        with patch("utils.gdrive_reader.logger.warning") as mock_warning:
            reader = GDriveReader(config)
            mock_warning.assert_called_once()
            assert "credentials file not found" in mock_warning.call_args[0][0].lower()

    def test_build_drive_service(self, gdrive_config):
        """Test building the drive service with proper authentication."""
        with patch("utils.gdrive_reader.service_account.Credentials.from_service_account_file") as mock_creds:
            mock_creds.return_value = MagicMock()
            mock_creds.return_value.with_subject.return_value = MagicMock()
            
            with patch("utils.gdrive_reader.build") as mock_build:
                mock_service = MagicMock()
                mock_build.return_value = mock_service
                
                reader = GDriveReader(gdrive_config)
                service = reader.drive_service
                
                # Assert credentials were created with correct parameters
                mock_creds.assert_called_once_with(
                    gdrive_config.credentials_path,
                    scopes=gdrive_config.scopes
                )
                
                # Assert impersonation was used
                mock_creds.return_value.with_subject.assert_called_once_with(
                    gdrive_config.impersonated_user_email
                )
                
                # Assert Drive API was built correctly
                mock_build.assert_called_once_with(
                    'drive', 'v3', 
                    credentials=mock_creds.return_value.with_subject.return_value
                )
                
                assert service == mock_service

    def test_drive_service_missing_credentials(self, tmp_path):
        """Test accessing drive_service with missing credentials raises error."""
        nonexistent_path = str(tmp_path / "nonexistent.json")
        config = GDriveReaderConfig(
            credentials_path=nonexistent_path,
            folder_id="test_folder_id"
        )
        
        reader = GDriveReader(config)
        with pytest.raises(FileNotFoundError):
            reader.drive_service

    def test_list_files(self, gdrive_reader, mock_drive_service):
        """Test listing files from Google Drive."""
        # Mock the files().list().execute() chain
        mock_list_method = MagicMock()
        mock_drive_service.files.return_value.list.return_value.execute.return_value = {
            'files': [
                {'id': 'file1', 'name': 'Test File 1', 'mimeType': 'application/pdf'},
                {'id': 'file2', 'name': 'Test File 2', 'mimeType': 'application/vnd.google-apps.document'}
            ]
        }
        
        # Call method under test
        result = gdrive_reader.list_files()
        
        # Assertions
        mock_drive_service.files.return_value.list.assert_called_once()
        # Check query construction 
        call_kwargs = mock_drive_service.files.return_value.list.call_args[1]
        assert "'test_folder_id' in parents" in call_kwargs['q']
        assert "trashed = false" in call_kwargs['q']
        
        # Check result
        assert len(result) == 2
        assert result[0]['id'] == 'file1'
        assert result[1]['name'] == 'Test File 2'

    def test_list_files_with_filter(self, gdrive_reader, mock_drive_service):
        """Test listing files with additional query filter."""
        # Mock response
        mock_drive_service.files.return_value.list.return_value.execute.return_value = {
            'files': [{'id': 'file1', 'name': 'Test PDF', 'mimeType': 'application/pdf'}]
        }
        
        # Call with filter
        result = gdrive_reader.list_files(query_filter="mimeType='application/pdf'")
        
        # Assertions
        call_kwargs = mock_drive_service.files.return_value.list.call_args[1]
        assert "mimeType='application/pdf'" in call_kwargs['q']
        assert len(result) == 1
        assert result[0]['name'] == 'Test PDF'

    def test_list_files_with_pagination(self, gdrive_reader, mock_drive_service):
        """Test listing files with pagination."""
        # Setup mock to return paginated results
        mock_drive_service.files.return_value.list.return_value.execute.side_effect = [
            {
                'files': [{'id': 'file1', 'name': 'Test File 1'}],
                'nextPageToken': 'token123'
            },
            {
                'files': [{'id': 'file2', 'name': 'Test File 2'}],
                # No nextPageToken indicates last page
            }
        ]
        
        # Call method under test
        result = gdrive_reader.list_files()
        
        # Assertions
        assert mock_drive_service.files.return_value.list.call_count == 2
        # Second call should include the page token
        second_call_kwargs = mock_drive_service.files.return_value.list.call_args_list[1][1]
        assert second_call_kwargs['pageToken'] == 'token123'
        
        # Check combined results
        assert len(result) == 2
        assert result[0]['name'] == 'Test File 1'
        assert result[1]['name'] == 'Test File 2'

    def test_list_files_no_folder_id(self, gdrive_config):
        """Test list_files with no folder ID raises error."""
        # Create config with no folder_id
        config = GDriveReaderConfig(
            credentials_path=gdrive_config.credentials_path,
            folder_id=None  # No folder ID
        )
        
        reader = GDriveReader(config)
        with pytest.raises(ValueError, match="Folder ID must be provided"):
            reader.list_files()

    def test_download_file_to_path(self, gdrive_reader, mock_drive_service, tmp_path):
        """Test downloading a file to local path."""
        # Mock the get_media request and downloader
        mock_request = MagicMock()
        mock_drive_service.files.return_value.get_media.return_value = mock_request
        
        with patch("utils.gdrive_reader.MediaIoBaseDownload") as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader_class.return_value = mock_downloader
            # Mock the next_chunk method to return done=True
            mock_downloader.next_chunk.return_value = (MagicMock(progress=lambda: 1.0), True)
            
            # Call method under test
            target_path = tmp_path / "downloaded_file.pdf"
            result = gdrive_reader.download_file_to_path("file1", target_path)
            
            # Assertions
            mock_drive_service.files.return_value.get_media.assert_called_once_with(
                fileId="file1", supportsAllDrives=True
            )
            mock_downloader.next_chunk.assert_called_once()
            assert result == str(target_path.absolute())
            assert target_path.exists()

    def test_download_file_creates_parent_directories(self, gdrive_reader, mock_drive_service, tmp_path):
        """Test download creates parent directories if needed."""
        # Setup mock
        mock_drive_service.files.return_value.get_media.return_value = MagicMock()
        
        with patch("utils.gdrive_reader.MediaIoBaseDownload") as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader_class.return_value = mock_downloader
            mock_downloader.next_chunk.return_value = (MagicMock(progress=lambda: 1.0), True)
            
            # Create a nested path that doesn't exist
            target_path = tmp_path / "subfolder1" / "subfolder2" / "downloaded_file.pdf"
            
            # Call method under test
            gdrive_reader.download_file_to_path("file1", target_path)
            
            # Assertions - verify parent directories were created
            assert target_path.parent.exists()

    def test_read_file_content(self, gdrive_reader, mock_drive_service):
        """Test reading file content into memory."""
        # Mock file content
        test_content = b"Test file content bytes"
        
        # Setup mocks
        mock_request = MagicMock()
        mock_drive_service.files.return_value.get_media.return_value = mock_request
        
        with patch("utils.gdrive_reader.MediaIoBaseDownload") as mock_downloader_class:
            mock_downloader = MagicMock()
            mock_downloader_class.return_value = mock_downloader
            
            # Mock BytesIO
            with patch("utils.gdrive_reader.io.BytesIO") as mock_bytesio_class:
                mock_bytesio = MagicMock()
                mock_bytesio_class.return_value = mock_bytesio
                mock_bytesio.getvalue.return_value = test_content
                
                # Mock the next_chunk method to return done=True
                mock_downloader.next_chunk.return_value = (MagicMock(progress=lambda: 1.0), True)
                
                # Call method under test
                result = gdrive_reader.read_file_content("file1")
                
                # Assertions
                mock_drive_service.files.return_value.get_media.assert_called_once_with(
                    fileId="file1", supportsAllDrives=True
                )
                mock_downloader.next_chunk.assert_called_once()
                mock_bytesio.getvalue.assert_called_once()
                assert result == test_content
