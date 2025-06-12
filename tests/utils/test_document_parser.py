"""
Unit tests for DocumentParser module.

These tests focus on the document parsing functionality, mocking the LlamaParse
client to test different response scenarios and error conditions.
"""
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, ANY

# Add project root to path to ensure imports work
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from utils.document_parser import DocumentParser
from utils.config_models import LlamaParseConfig

# Mark all tests in this file as unit tests
pytestmark = pytest.mark.unit

@pytest.fixture
def mock_llama_parse():
    """Fixture providing a mocked LlamaParse client."""
    with patch("utils.document_parser.LlamaParse") as mock_llama:
        # Create a mock for the parse method result
        mock_result = MagicMock()
        mock_llama.return_value.parse.return_value = mock_result
        yield mock_llama


@pytest.fixture
def sample_document_path(tmp_path):
    """Create a temporary document file for testing."""
    doc_path = tmp_path / "test_document.txt"
    with open(doc_path, 'w') as f:
        f.write("Test document content.\nLine 2 of test document.")
    return doc_path


@pytest.fixture
def document_parser():
    """Create a DocumentParser instance with mocked configuration."""
    config = LlamaParseConfig(api_key="mock_api_key")
    return DocumentParser(config)


class TestDocumentParser:
    """Test cases for DocumentParser class."""
    
    def test_parser_initialization(self, document_parser, mock_llama_parse):
        """Test parser initialization and configuration."""
        # Access parser property to trigger initialization
        parser = document_parser.parser
        
        # Assert LlamaParse was initialized with correct parameters
        mock_llama_parse.assert_called_once_with(api_key="mock_api_key")
        assert parser is not None

    def test_parser_initialization_with_base_url(self, mock_llama_parse):
        """Test parser initialization with custom base URL."""
        config = LlamaParseConfig(
            api_key="mock_api_key", 
            base_url="https://custom-llamaparse.example.com"
        )
        parser = DocumentParser(config)
        
        # Access parser property to trigger initialization
        actual_parser = parser.parser
        
        # Assert LlamaParse was initialized with correct parameters
        mock_llama_parse.assert_called_once_with(
            api_key="mock_api_key",
            base_url="https://custom-llamaparse.example.com"
        )

    def test_parse_file_success_with_pages_attribute(self, document_parser, sample_document_path):
        """Test successful document parsing with newer LlamaParse format (pages attribute)."""
        # Configure mock for newer LlamaParse format
        mock_page_1 = MagicMock()
        mock_page_1.page = 1
        mock_page_1.text = "Page 1 content"
        
        mock_page_2 = MagicMock()
        mock_page_2.page = 2
        mock_page_2.text = "Page 2 content"
        
        job_result = MagicMock()
        job_result.pages = [mock_page_1, mock_page_2]
        
        # Patch the parser's parse method
        document_parser._parser = MagicMock()
        document_parser._parser.parse.return_value = job_result
        
        # Call method under test
        result = document_parser.parse_file(sample_document_path)
        
        # Assertions
        assert len(result) == 2
        assert result[0]["page_or_section_index"] == 1
        assert result[0]["text"] == "Page 1 content"
        assert result[1]["page_or_section_index"] == 2
        assert result[1]["text"] == "Page 2 content"
        document_parser._parser.parse.assert_called_once_with(str(sample_document_path))

    def test_parse_file_success_with_text_attribute(self, document_parser, sample_document_path):
        """Test successful document parsing with older LlamaParse format (text attribute)."""
        # Create simple custom class objects instead of complex mocks
        class MockDocument:
            def __init__(self, text_content, metadata_dict):
                self.text = text_content
                self.metadata = metadata_dict
                # No page attribute by design
                
        # Create document instances that explicitly do NOT have a 'page' attribute
        mock_doc_1 = MockDocument("Document 1 content", {"section": "intro"})
        mock_doc_2 = MockDocument("Document 2 content", {"section": "conclusion"})
        
        # Patch the parser's parse method
        document_parser._parser = MagicMock()
        document_parser._parser.parse.return_value = [mock_doc_1, mock_doc_2]
        
        # Call method under test
        result = document_parser.parse_file(sample_document_path)
        
        # Assertions
        assert len(result) == 2
        assert result[0]["page_or_section_index"] == 0
        assert result[0]["text"] == "Document 1 content"
        assert result[0]["metadata"] == {"section": "intro"}
        assert result[1]["page_or_section_index"] == 1
        assert result[1]["text"] == "Document 2 content"

    def test_parse_file_success_with_dict_format(self, document_parser, sample_document_path):
        """Test successful document parsing with dictionary format."""
        # Configure mock for dictionary format
        dict_format = [
            {"text": "Dict 1 content", "page_or_section_index": 1, "metadata": {"type": "header"}},
            {"text": "Dict 2 content", "page_or_section_index": 2, "metadata": {"type": "body"}}
        ]
        
        # Patch the parser's parse method
        document_parser._parser = MagicMock()
        document_parser._parser.parse.return_value = dict_format
        
        # Call method under test
        result = document_parser.parse_file(sample_document_path)
        
        # Assertions
        assert len(result) == 2
        assert result[0]["text"] == "Dict 1 content"
        assert result[0]["page_or_section_index"] == 1
        assert result[1]["text"] == "Dict 2 content"
        assert result[1]["metadata"] == {"type": "body"}

    def test_parse_file_with_unknown_format(self, document_parser, sample_document_path):
        """Test handling of unknown response format from LlamaParse."""
        # Configure mock for unknown format (objects without text attribute)
        unknown_format = [
            object(),
            object()
        ]
        
        # Patch the parser's parse method
        document_parser._parser = MagicMock()
        document_parser._parser.parse.return_value = unknown_format
        
        # Call method under test
        result = document_parser.parse_file(sample_document_path)
        
        # Assertions - should handle gracefully and return empty list
        assert len(result) == 0

    def test_parse_file_error_handling(self, document_parser, sample_document_path):
        """Test error handling during parsing."""
        # Configure parser to raise an exception
        document_parser._parser = MagicMock()
        document_parser._parser.parse.side_effect = Exception("Test parsing error")
        
        # Call method under test
        result = document_parser.parse_file(sample_document_path)
        
        # Assertions - should handle exception and return empty list
        assert result == []

    def test_parse_file_nonexistent_file(self, document_parser):
        """Test handling of nonexistent file."""
        # Try to parse a nonexistent file
        with pytest.raises(FileNotFoundError):
            document_parser.parse_file("/nonexistent/file.pdf")

    def test_parse_file_to_concatenated_text(self, document_parser, sample_document_path):
        """Test concatenation of text from multiple parsed sections."""
        # Mock parse_file to return test data
        mock_sections = [
            {"text": "Section 1 content."},
            {"text": "Section 2 content."}
        ]
        with patch.object(document_parser, 'parse_file', return_value=mock_sections):
            # Call method under test
            result = document_parser.parse_file_to_concatenated_text(sample_document_path)
            
            # Assertions
            assert result == "Section 1 content.\n\nSection 2 content."
            document_parser.parse_file.assert_called_once_with(sample_document_path)

    def test_parse_file_to_concatenated_text_empty_result(self, document_parser, sample_document_path):
        """Test concatenation with empty parsing results."""
        # Mock parse_file to return empty list
        with patch.object(document_parser, 'parse_file', return_value=[]):
            # Call method under test
            result = document_parser.parse_file_to_concatenated_text(sample_document_path)
            
            # Assertions
            assert result == ""

    def test_parse_file_to_concatenated_text_missing_text(self, document_parser, sample_document_path):
        """Test concatenation with sections missing 'text' key."""
        # Mock parse_file to return sections without 'text' key
        mock_sections = [
            {"metadata": "Section 1 metadata"},
            {"page_or_section_index": 2}
        ]
        with patch.object(document_parser, 'parse_file', return_value=mock_sections):
            # Call method under test
            result = document_parser.parse_file_to_concatenated_text(sample_document_path)
            
            # Assertions
            assert result == ""
