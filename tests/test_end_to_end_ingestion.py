"""
End-to-end tests for the document ingestion workflow.

These tests cover the complete pipeline from fetching documents from Google Drive
through parsing with LlamaParse, embedding generation, and storage in both
ChromaDB and Neo4j.
"""
import os
import sys
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

# Add project root to path to ensure imports work
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.gdrive_reader import GDriveReader
from utils.document_parser import DocumentParser
from utils.embedding import CustomGeminiEmbedding
from utils.chroma_ingester import ChromaIngester
from utils.neo4j_ingester import Neo4jIngester, DocumentIngestionData
from utils.config_models import (
    GDriveReaderConfig,
    LlamaParseConfig,
    ChromaDBConfig,
    Neo4jConfig,
    IngestionOrchestratorConfig
)

# Mark these as e2e tests
pytestmark = pytest.mark.e2e

@pytest.fixture
def mock_gdrive_service():
    """Mock Google Drive API service."""
    with patch("utils.gdrive_reader.build") as mock_build:
        # Create mock service and files resource
        mock_service = MagicMock()
        mock_files_resource = MagicMock()
        mock_service.files.return_value = mock_files_resource
        mock_build.return_value = mock_service
        
        # Setup mock file list response
        mock_list_response = MagicMock()
        mock_list_response.execute.return_value = {
            "files": [
                {
                    "id": "file1",
                    "name": "document1.pdf",
                    "mimeType": "application/pdf",
                    "webViewLink": "https://drive.google.com/file/d/file1/view"
                },
                {
                    "id": "file2",
                    "name": "document2.docx",
                    "mimeType": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    "webViewLink": "https://drive.google.com/file/d/file2/view"
                }
            ]
        }
        mock_files_resource.list.return_value = mock_list_response
        
        # Setup mock file download
        mock_download_request = MagicMock()
        mock_files_resource.get_media.return_value = mock_download_request
        
        # Mock the download content
        def mock_download_to_file(fh):
            fh.write(b"Mock document content for testing.")
            return None
            
        mock_download_request.execute = mock_download_to_file
        
        yield mock_service

@pytest.fixture
def mock_llama_parser():
    """Mock LlamaParse client."""
    with patch("utils.document_parser.LlamaParse") as mock_parser_class:
        mock_parser = MagicMock()
        mock_parser_class.return_value = mock_parser
        
        # Setup mock parse response
        mock_response = [
            {"text": "Mock document content page 1.", "page_or_section_index": 0, "metadata": {"page": 1}},
            {"text": "Mock document content page 2.", "page_or_section_index": 1, "metadata": {"page": 2}}
        ]
        mock_parser.parse_document.return_value = mock_response
        
        yield mock_parser

@pytest.fixture
def mock_embedding_client():
    """Mock the Gemini embedding client."""
    with patch("utils.embedding.genai.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock embeddings response
        mock_embeddings = [0.1, 0.2, 0.3, 0.4, 0.5] * 100  # 500-dim vector
        mock_response = {"embeddings": [mock_embeddings]}
        mock_client.models.embed_content.return_value = mock_response
        
        yield mock_client

@pytest.fixture
def mock_chromadb_client():
    """Mock ChromaDB client."""
    with patch("utils.chroma_ingester.chromadb.HttpClient") as mock_client_class:
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client
        
        # Mock collection
        mock_collection = MagicMock()
        mock_client.get_or_create_collection.return_value = mock_collection
        
        yield mock_client

@pytest.fixture
def mock_neo4j_driver():
    """Mock Neo4j driver."""
    with patch("neo4j.GraphDatabase.driver") as mock_driver_func:
        mock_driver = MagicMock()
        mock_session = MagicMock()
        mock_driver.session.return_value.__enter__.return_value = mock_session
        mock_driver_func.return_value = mock_driver
        
        # Setup mock transaction and result
        mock_result = MagicMock()
        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "id": "file1", 
            "updatedAt": "2023-01-01T00:00:00", 
            "createdAt": "2023-01-01T00:00:00"
        }.get(key)
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        
        yield mock_driver

@pytest.fixture
def mock_config():
    """Create mock config for testing."""
    gdrive_config = GDriveReaderConfig(
        credentials_file="mock_creds.json",
        folder_id="test_folder",
        download_dir="/tmp/downloads"
    )
    
    llamaparse_config = LlamaParseConfig(
        api_key="test-llama-api-key"
    )
    
    chromadb_config = ChromaDBConfig(
        host="localhost",
        port=8000,
        collection_name="test_collection"
    )
    
    neo4j_config = Neo4jConfig(
        uri="bolt://localhost:7687",
        user="neo4j",
        password="password"
    )
    
    # Create the full orchestrator config
    return IngestionOrchestratorConfig(
        gdrive=gdrive_config,
        llamaparse=llamaparse_config,
        chromadb=chromadb_config,
        neo4j=neo4j_config,
        embedding=chromadb_config  # Using ChromaDBConfig as a stand-in
    )

class TestEndToEndIngestion:
    """End-to-end tests for document ingestion workflow."""
    
    def test_full_ingestion_pipeline(
        self,
        tmp_path,
        mock_gdrive_service,
        mock_llama_parser,
        mock_embedding_client,
        mock_chromadb_client,
        mock_neo4j_driver,
        mock_config,
        monkeypatch
    ):
        """Test the complete document ingestion workflow."""
        # Set environment variables
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
        monkeypatch.setenv("LLAMA_CLOUD_API_KEY", "test-llama-api-key")
        
        # Create temp download directory
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        
        # Update config with temp path
        mock_config.gdrive.download_dir = str(download_dir)
        
        # Initialize components
        gdrive_reader = GDriveReader(config=mock_config.gdrive)
        parser = DocumentParser(config=mock_config.llamaparse)
        
        embedding_model = CustomGeminiEmbedding(
            google_api_key="test-api-key",
            model_name="gemini-embedding-test-model"
        )
        
        chroma_ingester = ChromaIngester(config=mock_config.chromadb)
        neo4j_ingester = Neo4jIngester(mock_neo4j_driver)
        
        # 1. Fetch documents from GDrive
        with patch("utils.gdrive_reader.service_account.Credentials.from_service_account_file") as mock_creds:
            mock_creds.return_value = MagicMock()
            documents = gdrive_reader.list_documents()
            
            # Should have found 2 documents
            assert len(documents) == 2
            assert documents[0]["id"] == "file1"
            assert documents[1]["id"] == "file2"
            
            # Download the first document
            local_path = gdrive_reader.download_document(documents[0])
            
            # Should have downloaded to the temp directory
            assert local_path.exists()
            assert str(local_path).startswith(str(download_dir))
            
            # 2. Parse the document
            parsed_content = parser.parse_file(local_path)
            
            # Should have parsed 2 pages
            assert len(parsed_content) == 2
            assert "Mock document content" in parsed_content[0]["text"]
            
            # Extract concatenated text for embedding
            concatenated_text = parser.parse_file_to_concatenated_text(local_path)
            
            # 3. Generate embedding
            embedding = embedding_model._get_text_embedding(concatenated_text)
            assert len(embedding) > 0
            
            # 4. Ingest to ChromaDB
            doc_id = documents[0]["id"]
            metadata = {
                "filename": documents[0]["name"],
                "mime_type": documents[0]["mimeType"],
                "gdrive_id": documents[0]["id"],
                "gdrive_link": documents[0]["webViewLink"]
            }
            
            chroma_ingester.ingest_document(
                doc_id=doc_id,
                content=concatenated_text,
                embedding=embedding,
                metadata=metadata
            )
            
            # Check that ChromaDB collection was created and document added
            mock_chromadb_client.get_or_create_collection.assert_called_once_with(
                name="test_collection",
                metadata=ANY
            )
            mock_collection = mock_chromadb_client.get_or_create_collection.return_value
            mock_collection.upsert.assert_called_once()
            
            # 5. Ingest to Neo4j
            document_data = DocumentIngestionData(
                doc_id=doc_id,
                filename=documents[0]["name"],
                content=concatenated_text,
                embedding=embedding,
                source_type="google_drive",
                mime_type=documents[0]["mimeType"],
                gdrive_id=documents[0]["id"],
                gdrive_webview_link=documents[0]["webViewLink"],
                parsed_timestamp=datetime.now(),
                metadata=metadata
            )
            
            neo4j_ingester.ingest_document(document_data)
            
            # Check that Neo4j session.run was called
            mock_session = mock_neo4j_driver.session.return_value.__enter__.return_value
            mock_session.run.assert_called_once()
            
            # Clean up temporary file
            if local_path.exists():
                local_path.unlink()

    def test_pipeline_with_missing_file_handling(
        self,
        tmp_path,
        mock_gdrive_service,
        mock_llama_parser,
        mock_embedding_client,
        mock_chromadb_client,
        mock_neo4j_driver,
        mock_config,
        monkeypatch
    ):
        """Test handling of missing files in the pipeline."""
        # Set environment variables
        monkeypatch.setenv("GOOGLE_API_KEY", "test-api-key")
        monkeypatch.setenv("LLAMA_CLOUD_API_KEY", "test-llama-api-key")
        
        # Create temp download directory
        download_dir = tmp_path / "downloads"
        download_dir.mkdir()
        
        # Update config with temp path
        mock_config.gdrive.download_dir = str(download_dir)
        
        # Initialize components
        gdrive_reader = GDriveReader(config=mock_config.gdrive)
        parser = DocumentParser(config=mock_config.llamaparse)
        
        embedding_model = CustomGeminiEmbedding(
            google_api_key="test-api-key",
            model_name="gemini-embedding-test-model"
        )
        
        # Simulate download failure
        with patch("utils.gdrive_reader.service_account.Credentials.from_service_account_file") as mock_creds:
            mock_creds.return_value = MagicMock()
            
            # List documents
            documents = gdrive_reader.list_documents()
            
            # Make download_document raise an exception
            with patch.object(
                gdrive_reader, 
                "download_document", 
                side_effect=Exception("File not found")
            ):
                # Attempt to process documents with error handling
                processed_docs = []
                failed_docs = []
                
                for doc in documents:
                    try:
                        # Try to download
                        local_path = gdrive_reader.download_document(doc)
                        
                        # Parse
                        parsed_content = parser.parse_file(local_path)
                        concatenated_text = parser.parse_file_to_concatenated_text(local_path)
                        
                        # Generate embedding
                        embedding = embedding_model._get_text_embedding(concatenated_text)
                        
                        # Successfully processed
                        processed_docs.append(doc["id"])
                        
                    except Exception as e:
                        # Add to failed documents
                        failed_docs.append({"id": doc["id"], "error": str(e)})
                
                # Should have no successful docs and 2 failures
                assert len(processed_docs) == 0
                assert len(failed_docs) == 2
                assert all("File not found" in doc["error"] for doc in failed_docs)
                
                # Verify the pipeline can continue with the next batch after failures
                with patch.object(
                    gdrive_reader,
                    "download_document",
                    return_value=download_dir / "recovered_doc.pdf"
                ):
                    # Create a mock file
                    with open(download_dir / "recovered_doc.pdf", "w") as f:
                        f.write("Mock content")
                    
                    # Try processing again
                    for doc in documents:
                        try:
                            # Try to download
                            local_path = gdrive_reader.download_document(doc)
                            
                            # Parse
                            parsed_content = parser.parse_file(local_path)
                            
                            # Successfully processed
                            processed_docs.append(doc["id"])
                            
                        except Exception as e:
                            # Should not happen
                            assert False, f"Should not fail: {str(e)}"
                    
                    # Should now have 2 successful docs
                    assert len(processed_docs) == 2
                    
                    # Clean up
                    if os.path.exists(download_dir / "recovered_doc.pdf"):
                        os.unlink(download_dir / "recovered_doc.pdf")
