#!/usr/bin/env python
"""
Diagnostic script to analyze the output structure from LlamaParse.
This script helps understand what format is returned when parsing documents,
which is essential for properly handling ingestion into databases.
"""

import os
import sys
import json
import pprint
from pathlib import Path
from typing import Any, Dict, List, Union

# Add project root to Python path to import local modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.document_parser import DocumentParser
from utils.config_models import LlamaParseConfig
from dotenv import load_dotenv
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stderr, level="INFO")


def analyze_structure(obj: Any, max_depth: int = 3, current_depth: int = 0) -> str:
    """
    Recursively analyze and describe the structure of an object.
    
    Args:
        obj: The object to analyze
        max_depth: Maximum recursion depth
        current_depth: Current recursion depth
        
    Returns:
        A string description of the object structure
    """
    if current_depth >= max_depth:
        return f"{type(obj).__name__} (max depth reached)"
    
    if obj is None:
        return "None"
    
    if isinstance(obj, (str, int, float, bool)):
        return f"{type(obj).__name__}: {obj if isinstance(obj, (int, float, bool)) else obj[:100] + '...' if len(str(obj)) > 100 else obj}"
    
    if isinstance(obj, list):
        if not obj:
            return "Empty list []"
        sample = obj[0] if len(obj) > 0 else None
        return f"List[{len(obj)}] of {type(sample).__name__} elements: [{analyze_structure(sample, max_depth, current_depth + 1)}, ...]"
    
    if isinstance(obj, dict):
        if not obj:
            return "Empty dict {}"
        keys_str = ", ".join(f"'{k}'" for k in list(obj.keys())[:10])
        if len(obj) > 10:
            keys_str += ", ..."
        sample_key = next(iter(obj)) if obj else None
        sample_value = obj.get(sample_key) if sample_key else None
        return f"Dict{{{len(obj)} keys: {keys_str}}} with sample value for '{sample_key}': {analyze_structure(sample_value, max_depth, current_depth + 1)}"
    
    # For other objects, check their attributes
    attributes = dir(obj)
    # Filter out private and dunder attributes
    public_attrs = [attr for attr in attributes if not attr.startswith('_')]
    
    if hasattr(obj, '__dict__'):
        # If the object has a __dict__, show its contents
        return f"{type(obj).__name__} with attributes: {list(sorted(public_attrs))[:10]}"
    else:
        # Otherwise just return the type
        return f"{type(obj).__name__} (no __dict__)"


def main():
    # Load environment variables
    load_dotenv()
    
    if "LLAMA_CLOUD_API_KEY" not in os.environ:
        logger.error("LLAMA_CLOUD_API_KEY environment variable is not set. Please set it in the .env file.")
        return
    
    # Initialize LlamaParseConfig and DocumentParser
    parser_config = LlamaParseConfig(api_key=os.environ["LLAMA_CLOUD_API_KEY"])
    document_parser = DocumentParser(config=parser_config)
    
    # Ask for a file path to analyze
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        print("Enter the path to a file to parse with LlamaParse: ", end="")
        file_path = input().strip()
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    logger.info(f"Parsing file: {file_path}")
    
    # Parse the file
    try:
        parsed_output = document_parser.parse_file(file_path)
        
        # Print overall structure
        logger.info(f"Overall parsed output structure: {analyze_structure(parsed_output)}")
        
        # Detailed information about the first few items
        logger.info("\n\nDetailed inspection of the first few parsed items:")
        for i, item in enumerate(parsed_output[:3] if len(parsed_output) > 3 else parsed_output):
            logger.info(f"\n--- Item {i} ---")
            
            # Print type information
            logger.info(f"Type: {type(item)}")
            
            # If it's a dictionary, show keys
            if isinstance(item, dict):
                logger.info(f"Keys: {list(item.keys())}")
                
                # Show each key's value type
                for key, value in item.items():
                    value_preview = str(value)
                    if len(value_preview) > 100:
                        value_preview = value_preview[:100] + "..."
                    logger.info(f"Key '{key}' ({type(value).__name__}): {value_preview}")
            
            # If it has attributes, show those
            elif hasattr(item, "__dict__"):
                attributes = vars(item)
                logger.info(f"Attributes: {list(attributes.keys())}")
                
                # Show each attribute's value type
                for attr, value in attributes.items():
                    if attr.startswith("_"):
                        continue
                    value_preview = str(value)
                    if len(value_preview) > 100:
                        value_preview = value_preview[:100] + "..."
                    logger.info(f"Attribute '{attr}' ({type(value).__name__}): {value_preview}")
        
        # Save full output to a JSON file for further inspection
        output_dir = Path("debug_output")
        output_dir.mkdir(exist_ok=True)
        
        output_data = []
        for item in parsed_output:
            if isinstance(item, dict):
                output_data.append(item)
            elif hasattr(item, "__dict__"):
                output_data.append(vars(item))
            else:
                output_data.append({"type": str(type(item)), "str_repr": str(item)})
        
        output_file = output_dir / f"llamaparse_output_{Path(file_path).stem}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"Full parsed output saved to {output_file}")
        
        # Provide guidance on next steps
        logger.info("\n\nNext steps:")
        logger.info("1. Examine the JSON output file for complete details")
        logger.info("2. Update ingest_gdrive_documents.py to properly handle this format")
        logger.info("3. Specifically, replace 'page.text' with the correct access method based on the structure shown above")
        
    except Exception as e:
        logger.error(f"Error parsing the file: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()
