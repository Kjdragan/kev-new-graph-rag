# Google Drive Reader for kev-graph-rag

import io
from pathlib import Path
from typing import Dict, List, Any, Optional, Union

from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Assuming config_models.py is in the same utils directory
from .config_models import GDriveReaderConfig 


class GDriveReader:
    """Handles interaction with Google Drive for reading files."""

    def __init__(self, config: GDriveReaderConfig):
        """Initialize the Google Drive reader.

        Args:
            config: Configuration for Google Drive access.
        """
        self.config = config
        self._drive_service: Optional[Resource] = None
        self._validate_credentials_path()

    def _validate_credentials_path(self):
        path = Path(self.config.credentials_path)
        if not path.exists():
            logger.warning(
                f"Google Drive credentials file not found at {self.config.credentials_path}. "
                f"The GDriveReader will not be able to authenticate until this file is present."
            )
            # You might raise an error here or allow deferred initialization
            # For now, just log a warning.

    @property
    def drive_service(self) -> Resource:
        """Get or create the Google Drive API service.

        Returns:
            A configured Google Drive API service.
        
        Raises:
            FileNotFoundError: If credentials file is not found when service is accessed.
        """
        if self._drive_service is None:
            if not Path(self.config.credentials_path).exists():
                raise FileNotFoundError(
                    f"Cannot build Drive service: Credentials file not found at {self.config.credentials_path}"
                )
            self._drive_service = self._build_drive_service()
        return self._drive_service

    def _build_drive_service(self) -> Resource:
        """Build and return an authorized Google Drive API service instance."""
        logger.info(f"Authenticating to Google Drive using {self.config.credentials_path}")
        
        creds = service_account.Credentials.from_service_account_file(
            self.config.credentials_path,
            scopes=self.config.scopes
        )

        if self.config.impersonated_user_email:
            logger.info(f"Impersonating user: {self.config.impersonated_user_email}")
            creds = creds.with_subject(self.config.impersonated_user_email)
        
        service = build('drive', 'v3', credentials=creds)
        logger.info("Successfully built Google Drive service.")
        return service

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def list_files(
        self,
        folder_id: Optional[str] = None,
        page_size: int = 100,
        order_by: str = 'modifiedTime desc',
        query_filter: Optional[str] = None,
        recursive: bool = False # Added for potential future use
    ) -> List[Dict[str, Any]]:
        """List files in the configured Google Drive folder.

        Args:
            folder_id: Google Drive folder ID. If None, uses config.folder_id.
            page_size: Maximum number of files to return per page.
            order_by: Field to sort by (e.g., 'modifiedTime desc', 'name').
            query_filter: Additional query string to filter files (e.g., "mimeType='application/pdf'").
            recursive: If True, recursively list files in subfolders (not implemented yet).

        Returns:
            List of file metadata dictionaries.
        """
        target_folder_id = folder_id or self.config.folder_id
        if not target_folder_id:
            raise ValueError("Folder ID must be provided either in config or as an argument.")

        base_query = f"'{target_folder_id}' in parents and trashed = false"
        if query_filter:
            final_query = f"{base_query} and ({query_filter})"
        else:
            final_query = base_query
        
        logger.debug(f"Listing files with query: {final_query} from folder: {target_folder_id}")
        
        all_files = []
        page_token = None
        while True:
            results = self.drive_service.files().list(
                q=final_query,
                pageSize=page_size,
                orderBy=order_by,
                fields="nextPageToken, files(id, name, mimeType, size, modifiedTime, md5Checksum, parents, webViewLink, iconLink)",
                supportsAllDrives=True,
                includeItemsFromAllDrives=True,
                pageToken=page_token
            ).execute()
            
            files = results.get('files', [])
            all_files.extend(files)
            page_token = results.get('nextPageToken', None)
            if page_token is None:
                break
        
        logger.info(f"Found {len(all_files)} files in Drive folder {target_folder_id} matching query.")
        return all_files

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def download_file_to_path(self, file_id: str, target_path: Union[str, Path]) -> str:
        """Download a file from Google Drive to a local path.

        Args:
            file_id: Google Drive file ID.
            target_path: Local path where the file should be saved.

        Returns:
            Absolute path to the downloaded file as a string.
        """
        path_obj = Path(target_path)
        path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Downloading Drive file_id '{file_id}' to '{path_obj.absolute()}'")
        
        request = self.drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
        fh = io.FileIO(path_obj, 'wb') # Use FileIO for binary mode
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                logger.debug(f"Download progress for {file_id}: {int(status.progress() * 100)}%")
        
        logger.info(f"Successfully downloaded file_id '{file_id}' to '{path_obj.absolute()}'")
        return str(path_obj.absolute())

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def read_file_content(self, file_id: str) -> bytes:
        """Read the content of a file from Google Drive into memory.

        Args:
            file_id: Google Drive file ID.

        Returns:
            The file content as bytes.
        """
        logger.info(f"Reading content of Drive file_id '{file_id}' into memory")
        request = self.drive_service.files().get_media(fileId=file_id, supportsAllDrives=True)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
            if status:
                logger.debug(f"Download progress for {file_id} (in-memory): {int(status.progress() * 100)}%")
        
        content = fh.getvalue()
        logger.info(f"Successfully read {len(content)} bytes from file_id '{file_id}'")
        return content

# Example Usage (for testing purposes, can be removed or moved to a test file)
if __name__ == '__main__':
    from dotenv import load_dotenv
    import os

    # Load .env from the project root for testing
    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(dotenv_path=project_root / '.env')

    # Ensure credentials path is correct relative to where you store it
    # This example assumes it's in project_root/credentials/gdrive_service_account.json
    # and your .env has GOOGLE_DRIVE_FOLDER_ID and GOOGLE_IMPERSONATED_USER_EMAIL (optional)
    
    default_creds_path = project_root / 'credentials' / 'gdrive_service_account.json'
    if not default_creds_path.exists():
        print(f"SKIPPING GDriveReader example: Credentials not found at {default_creds_path}")
        print("Please set up your 'credentials/gdrive_service_account.json' file.")
    else:
        try:
            gdrive_config = GDriveReaderConfig(
                credentials_path=str(default_creds_path),
                folder_id=os.getenv('GOOGLE_DRIVE_FOLDER_ID', 'YOUR_FOLDER_ID_HERE'), # Replace or set in .env
                impersonated_user_email=os.getenv('GOOGLE_IMPERSONATED_USER_EMAIL')
            )

            if gdrive_config.folder_id == 'YOUR_FOLDER_ID_HERE':
                print("SKIPPING GDriveReader example: GOOGLE_DRIVE_FOLDER_ID not set in .env or code.")
            else:
                reader = GDriveReader(config=gdrive_config)
                
                print(f"Listing files from folder: {gdrive_config.folder_id}")
                files = reader.list_files(query_filter="mimeType='application/vnd.google-apps.document' or mimeType='application/pdf'")
                # files = reader.list_files() # List all files
                
                if files:
                    for file_item in files:
                        print(f"  - {file_item['name']} (ID: {file_item['id']}, Type: {file_item['mimeType']})")
                    
                    # Example: Download the first file
                    first_file_id = files[0]['id']
                    first_file_name = files[0]['name']
                    download_path = project_root / 'temp_downloads' / first_file_name
                    
                    print(f"\nDownloading '{first_file_name}' to {download_path}...")
                    reader.download_file_to_path(first_file_id, download_path)
                    print(f"Downloaded '{first_file_name}'.")

                    # Example: Read the first file's content into memory
                    print(f"\nReading content of '{first_file_name}'...")
                    content_bytes = reader.read_file_content(first_file_id)
                    print(f"Read {len(content_bytes)} bytes from '{first_file_name}'. First 100 bytes: {content_bytes[:100]}...")
                else:
                    print("No files found in the specified folder.")

        except FileNotFoundError as e:
            print(f"Error during GDriveReader example: {e}")
            print("Ensure your 'credentials/gdrive_service_account.json' is correctly placed and GOOGLE_DRIVE_FOLDER_ID is set.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            import traceback
            traceback.print_exc()
