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
            # and returns a list of Document objects (from llama_index.core.schema)
            # We need to convert these to a more generic dict structure or extract text.
            parsed_llama_documents = self.parser.parse(str(path_obj))
            logger.info(f"Successfully parsed {len(parsed_llama_documents)} sections from {path_obj.name}.")
            
            # Extract text content from each parsed document/section
            # For now, we'll assume each 'document' has a 'text' attribute.
            # The actual structure might vary based on LlamaParse version and output.
            # This part might need refinement based on actual LlamaParse output structure.
            extracted_data = []
            for i, doc in enumerate(parsed_llama_documents):
                if hasattr(doc, 'text'):
                    extracted_data.append({
                        "page_or_section_index": i,
                        "text": doc.text,
                        "metadata": doc.metadata if hasattr(doc, 'metadata') else {}
                    })
                elif isinstance(doc, dict) and 'text' in doc: # If it's already a dict
                     extracted_data.append(doc)
                else:
                    logger.warning(f"Parsed document section {i} from {path_obj.name} lacks a 'text' attribute. Content: {str(doc)[:100]}...")
            
            if not extracted_data:
                logger.warning(f"LlamaParse returned no text sections for {path_obj.name}.")

            return extracted_data
        except Exception as e:
            logger.error(f"LlamaParse failed for document {path_obj.name}: {str(e)}")
            raise

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
