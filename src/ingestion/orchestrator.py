# src/ingestion/orchestrator.py
# Main orchestrator for the modular ingestion pipeline.

from loguru import logger
from typing import List, Dict, Any, Optional

from src.ingestion.pipeline import IngestionPipeline, IngestionStep
from utils.config_loader import get_config
from utils.config_models import IngestionOrchestratorConfig
from utils.embedding import get_embedding_model
from utils.chroma_ingester import ChromaIngester
from utils.neo4j_ingester import Neo4jIngester
from src.graph_extraction.extractor import GraphExtractor
from src.ingestion.steps import (
    LoadDocumentsFromGDrive, 
    ParseDocuments, 
    ExtractGraph, 
    IngestToChromaDB, 
    IngestToNeo4j
)
from src.ontology_templates.universal_ontology import NODES as UniversalNodes, RELATIONSHIPS as UniversalRelationships
from llama_index.core.schema import Document as LlamaDocument
import uuid

class IngestionOrchestrator:
    """
    Configures and runs ingestion pipelines based on the application's configuration.
    """

    def __init__(self, config: Optional[IngestionOrchestratorConfig] = None):
        """Initializes the orchestrator with necessary configurations."""
        logger.info("Initializing IngestionOrchestrator...")
        self.config = config or get_config()
        self.embedding_model = get_embedding_model(self.config.embedding)
        
        # Initialize clients/ingesters that will be used by pipeline steps
        self.chroma_ingester = ChromaIngester(self.config.chromadb, self.embedding_model)
        self.neo4j_ingester = Neo4jIngester(self.config.neo4j)
        self.graph_extractor = GraphExtractor(
            config=self.config.graph_extractor,
            llm=None, # GraphExtractor will use its own LLM based on config
            embedding_model=self.embedding_model
        )
        
        # Load ontology
        self.ontology_nodes = UniversalNodes
        self.ontology_edges = UniversalRelationships

        logger.info("IngestionOrchestrator initialized.")

    def get_gdrive_pipeline(self) -> IngestionPipeline:
        """
        Constructs the specific pipeline for ingesting documents from Google Drive.
        This will be expanded to include parsing, graph extraction, and Neo4j ingestion.
        """
        logger.info("Constructing Google Drive ingestion pipeline...")
        steps: List[IngestionStep] = [
            LoadDocumentsFromGDrive(self.config.gdrive),
            ParseDocuments(self.config.llamaparse),
            ExtractGraph(self.graph_extractor, self.ontology_nodes, self.ontology_edges),
            IngestToChromaDB(self.chroma_ingester),
            IngestToNeo4j(self.neo4j_ingester)
        ]
        return IngestionPipeline(steps=steps)

    def get_local_file_pipeline(self) -> IngestionPipeline:
        """
        Constructs the pipeline for ingesting a local file.
        This pipeline omits the document loading step, as the document is provided directly.
        """
        logger.info("Constructing local file ingestion pipeline...")
        steps: List[IngestionStep] = [
            ParseDocuments(self.config.llamaparse),
            ExtractGraph(self.graph_extractor, self.ontology_nodes, self.ontology_edges),
            IngestToChromaDB(self.chroma_ingester),
            IngestToNeo4j(self.neo4j_ingester)
        ]
        return IngestionPipeline(steps=steps)

    async def run_local_file_ingestion(self, file_path: str, file_name: str) -> Dict[str, Any]:
        """
        Runs the full ingestion process for a local file.

        Args:
            file_path: The path to the local file to ingest.
            file_name: The original name of the file.

        Returns:
            A summary of the ingestion process.
        """
        pipeline = self.get_local_file_pipeline()
        
        # Create a LlamaDocument object to pass into the pipeline context
        # This standardizes the input for the ParseDocuments step
        doc = LlamaDocument(
            id_=str(uuid.uuid4()),
            metadata={"file_path": file_path, "file_name": file_name}
        )
        
        initial_context = {"documents": [doc]}
        
        result_context = await pipeline.run(initial_context)
        
        summary = {
            "total_documents_loaded": 1, # Since it's a single file
            "ingested_chroma_count": result_context.get("ingested_chroma_docs_count", 0),
            "ingested_neo4j_nodes": result_context.get("ingested_neo4j_nodes", 0),
            "ingested_neo4j_edges": result_context.get("ingested_neo4j_edges", 0),
            "errors": [str(e) for e in result_context.errors]
        }
        
        logger.info(f"Local file ingestion run finished for '{file_name}'. Summary: {summary}")
        return summary

    async def run_gdrive_ingestion(self, folder_id: str) -> Dict[str, Any]:
        """
        Runs the full ingestion process for a given Google Drive folder.

        Args:
            folder_id: The ID of the Google Drive folder to ingest.

        Returns:
            A summary of the ingestion process.
        """
        pipeline = self.get_gdrive_pipeline()
        initial_context = {"gdrive_folder_id": folder_id}
        
        result_context = await pipeline.run(initial_context)
        
        summary = {
            "total_documents_loaded": len(result_context.get("documents", [])),
            "ingested_chroma_count": result_context.get("ingested_chroma_docs_count", 0),
            "ingested_neo4j_nodes": result_context.get("ingested_neo4j_nodes", 0),
            "ingested_neo4j_edges": result_context.get("ingested_neo4j_edges", 0),
            "errors": [str(e) for e in result_context.errors]
        }
        
        logger.info(f"Google Drive ingestion run finished. Summary: {summary}")
        return summary
