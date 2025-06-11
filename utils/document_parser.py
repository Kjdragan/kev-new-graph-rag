# Document Parser for kev-graph-rag using LlamaParse

from pathlib import Path
from typing import Dict, Any, Optional, Union, List

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from llama_cloud_services import LlamaParse # Ensure this is installed via 'uv sync'

# Assuming config_models.py is in the same utils directory
from .config_models import LlamaParseConfig


class DocumentParser:
    """Handles document parsing using LlamaParse."""

    def __init__(self, config: LlamaParseConfig):
        """Initialize the LlamaParse processor.

        Args:
            config: Configuration for LlamaParse access.
        """
        self.config = config
        self._parser: Optional[LlamaParse] = None

    @property
    def parser(self) -> LlamaParse:
        """Get or create the LlamaParse client.

        Returns:
            A configured LlamaParse client.
        """
        if self._parser is None:
            kwargs = {"api_key": self.config.api_key}
            if self.config.base_url:
                kwargs["base_url"] = self.config.base_url
            
            self._parser = LlamaParse(**kwargs)
            logger.debug("Initialized LlamaParse client.")
        return self._parser

    @retry(
        stop=stop_after_attempt(3), # Reduced retries for parsing as it can be long
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def parse_file(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Parse a document from a local file path using LlamaParse.

        Args:
            file_path: Path to the document file.

        Returns:
            A list of parsed document objects (dictionaries).
            LlamaParse typically returns a list of 'documents' (pages or sections).
        """
        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found for parsing: {path_obj}")
        
        logger.info(f"Parsing document file: {path_obj.name} with LlamaParse")
        
        try:
            # LlamaParse's .parse() method expects a file path string
            # and returns a JobResult object with a 'pages' attribute containing parsed pages
            # We need to convert these to a more generic dict structure or extract text.
            job_result = self.parser.parse(str(path_obj))
            
            # Handle JobResult object which has 'pages' attribute
            if hasattr(job_result, 'pages'):
                parsed_llama_documents = job_result.pages
                logger.info(f"Successfully parsed {len(parsed_llama_documents)} pages from {path_obj.name}.")
            else:
                # Fallback for backward compatibility if the result is directly a list of documents
                parsed_llama_documents = job_result
                logger.info(f"Successfully parsed {len(parsed_llama_documents) if hasattr(parsed_llama_documents, '__len__') else 'unknown number of'} sections from {path_obj.name}.")
            
            # Extract text content from each parsed document/section
            # Handle different structures that might be returned by LlamaParse
            # depending on version and configuration
            extracted_data = []
            
            # Determine if we're dealing with Page objects (newer LlamaParse) or older format
            for i, item in enumerate(parsed_llama_documents):
                # Handle Page objects from newer LlamaParse versions
                if hasattr(item, 'page') and hasattr(item, 'text'):
                    extracted_data.append({
                        "page_or_section_index": item.page,  # Use actual page number
                        "text": item.text,
                        "metadata": {"page": item.page}
                    })
                # Handle Document objects (older LlamaParse versions)
                elif hasattr(item, 'text'):
                    extracted_data.append({
                        "page_or_section_index": i,
                        "text": item.text,
                        "metadata": item.metadata if hasattr(item, 'metadata') else {}
                    })
                # Handle dictionary format
                elif isinstance(item, dict) and 'text' in item:
                    extracted_data.append(item)
                else:
                    logger.warning(f"Parsed document section {i} from {path_obj.name} has unexpected format. Content type: {type(item)}")
                    logger.debug(f"Content preview: {str(item)[:100]}...")
            
            if not extracted_data:
                logger.warning(f"LlamaParse returned no text sections for {path_obj.name}.")

            return extracted_data
        except Exception as e:
            logger.error(f"LlamaParse failed for document {path_obj.name}: {str(e)}")
            # Print more detailed debugging info about the exception
            logger.debug(f"Exception type: {type(e)}, Details: {repr(e)}")
            return []

    def parse_file_to_concatenated_text(self, file_path: Union[str, Path]) -> str:
        """Parse a document and concatenate text from all sections/pages.

        Args:
            file_path: Path to the document file.

        Returns:
            A single string containing all extracted text, joined by newlines.
        """
        parsed_sections = self.parse_file(file_path)
        concatenated_text = "\n\n".join([section['text'] for section in parsed_sections if section.get('text')])
        if not concatenated_text and parsed_sections: # Parsed sections exist but no text was extracted
            logger.warning(f"Concatenated text is empty for {Path(file_path).name}, though sections were parsed.")
        elif not parsed_sections:
            logger.warning(f"No sections were parsed for {Path(file_path).name}, concatenated text is empty.")
        return concatenated_text

    # Potentially add a parse_content(content_bytes: bytes, filename: str) method later
    # if LlamaParse SDK supports direct byte ingestion without writing to a temp file.

# Example Usage (for testing purposes)
if __name__ == '__main__':
    from dotenv import load_dotenv
    import os

    project_root = Path(__file__).resolve().parent.parent.parent
    load_dotenv(dotenv_path=project_root / '.env')

    llama_api_key = os.getenv('LLAMA_CLOUD_API_KEY')

    if not llama_api_key:
        print("SKIPPING DocumentParser example: LLAMA_CLOUD_API_KEY not found in .env")
    else:
        parser_config = LlamaParseConfig(api_key=llama_api_key)
        parser = DocumentParser(config=parser_config)

        # Create a dummy file for testing
        dummy_file_dir = project_root / 'temp_for_parsing'
        dummy_file_dir.mkdir(exist_ok=True)
        dummy_file_path = dummy_file_dir / 'sample_document.txt'
        with open(dummy_file_path, 'w') as f:
            f.write("This is a sample document for LlamaParse testing.\nIt has multiple lines.")

        print(f"Attempting to parse dummy file: {dummy_file_path}")
        try:
            parsed_content_list = parser.parse_file(dummy_file_path)
            if parsed_content_list:
                for i, content_dict in enumerate(parsed_content_list):
                    print(f"--- Parsed Section {i+1} ---")
                    print(f"Text: {content_dict.get('text')[:200]}...")
                    print(f"Metadata: {content_dict.get('metadata')}")
            else:
                print("No content extracted by LlamaParse.")
        except Exception as e:
            print(f"Error during LlamaParse test: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Clean up dummy file
            if dummy_file_path.exists():
                dummy_file_path.unlink()
            if dummy_file_dir.exists() and not any(dummy_file_dir.iterdir()):
                dummy_file_dir.rmdir()
