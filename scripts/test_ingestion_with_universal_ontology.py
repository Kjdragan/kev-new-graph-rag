import asyncio
import sys
from pathlib import Path
from loguru import logger

# Add project root to path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.graph_extraction.extractor import GraphExtractor
from utils.config_loader import get_config
from utils.config_models import GeminiModelInstanceConfig
from src.ontology_templates.universal_ontology import NODES as UNIVERSAL_NODES, RELATIONSHIPS as UNIVERSAL_RELATIONSHIPS

# Configure logging
logger.remove() # remove default logger
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)
log_filename = f"test_ingestion_with_universal_ontology_{Path(__file__).stem}.log"
logger.add(
    sys.stderr, 
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
)
logger.add(
    log_dir / log_filename,
    rotation="1 MB",
    retention="3 days",
    level="DEBUG",
    enqueue=True,
    backtrace=True,
    diagnose=True
)

async def main():
    logger.info("Starting test ingestion: WITH universal_ontology.")

    try:
        # Load configuration (specifically for Gemini model config)
        config = get_config()
        if not config.gemini_suite or not config.gemini_suite.pro_model:
            logger.error("Gemini Pro model configuration is missing. Please check your config.yaml and .env file.")
            return

        model_config: GeminiModelInstanceConfig = config.gemini_suite.pro_model
        logger.info(f"Using Gemini model: {model_config.model_id}")

        # Initialize GraphExtractor
        graph_extractor = GraphExtractor(
            neo4j_uri=config.neo4j.uri, 
            neo4j_user=config.neo4j.user, 
            neo4j_pass=config.neo4j.password, 
            pro_model_config=model_config
        )

        sample_text = (
            "Alice Wonderland, a software engineer at GenAI Corp, met Bob The Builder, a project manager also at GenAI Corp, "
            "in New York City on January 15th, 2024. They discussed Project Chimera, which aims to integrate "
            "advanced AI models into urban planning. GenAI Corp is headquartered in San Francisco."
        )

        logger.info(f"Loaded {len(UNIVERSAL_NODES)} node types and {len(UNIVERSAL_RELATIONSHIPS)} relationship types from universal_ontology.")
        logger.info("Extracting graph WITH universal_ontology...")
        
        extraction_results = await graph_extractor.extract(
            text_content=sample_text,
            ontology_nodes=UNIVERSAL_NODES,
            ontology_edges=UNIVERSAL_RELATIONSHIPS,
            group_id="test_universal_ontology_group",
            episode_name_prefix="test_universal_ontology_ep"
        )

        logger.info("Extraction complete.")
        logger.info(f"Extracted Nodes: {len(extraction_results.get('nodes', []))}")
        for node in extraction_results.get('nodes', []):
            logger.info(f"  Node: {node.get('name')} ({node.get('uuid')}), Labels: {node.get('labels')}, Attributes: {node.get('attributes')}")
        
        logger.info(f"Extracted Edges: {len(extraction_results.get('edges', []))}")
        for edge in extraction_results.get('edges', []):
            logger.info(f"  Edge: {edge.get('type')} from {edge.get('source_uuid')} to {edge.get('target_uuid')}, Attributes: {edge.get('attributes')}")

    except Exception as e:
        logger.exception(f"An error occurred during the test ingestion: {e}")
    finally:
        if 'graph_extractor' in locals() and graph_extractor:
            await graph_extractor.close()
            logger.info("GraphExtractor connection closed.")

if __name__ == "__main__":
    asyncio.run(main())
