# src/ingestion/steps.py
# Concrete implementations of ingestion pipeline steps.

from loguru import logger
from typing import List, Any

from src.ingestion.pipeline import IngestionStep, IngestionContext
from utils.gdrive_reader import GDriveReader, GDriveReaderConfig
from utils.document_parser import DocumentParser, LlamaParseConfig
from utils.chroma_ingester import ChromaIngester
from src.ingestion.utils import convert_llama_docs_to_chroma_docs
from src.graph_extraction.extractor import GraphExtractor
from pydantic import BaseModel
from typing import Type
from utils.neo4j_ingester import Neo4jIngester, DocumentIngestionData

# Note: LlamaIndex documents are not directly JSON serializable, so we handle them carefully.
from llama_index.core.schema import Document as LlamaDocument
from llama_index.core.node_parser import SentenceSplitter
from youtube_transcript_api import YouTubeTranscriptApi
import uuid

class LoadDocumentsFromGDrive(IngestionStep):
    """An ingestion step to load documents from a Google Drive folder."""

    def __init__(self, config: GDriveReaderConfig):
        self.config = config

    async def run(self, context: IngestionContext) -> IngestionContext:
        folder_id = context.get("gdrive_folder_id")
        if not folder_id:
            logger.warning("No 'gdrive_folder_id' found in context. Skipping GDrive document loading.")
            context.set("documents", [])
            return context

        self.config.folder_id = folder_id
        logger.info(f"Loading documents from Google Drive folder: {self.config.folder_id}")

        try:
            reader = GDriveReader(self.config)
            documents = await reader.load_data()
            context.set("documents", documents)
            logger.success(f"Successfully loaded {len(documents)} documents from Google Drive.")
        except Exception as e:
            logger.error(f"Failed to load documents from Google Drive: {e}", exc_info=True)
            context.add_error(e)
            context.abort()

        return context


class ChunkDocument(IngestionStep):
    """An ingestion step to chunk a single document into multiple smaller documents."""

    def __init__(self, chunk_size=1024, chunk_overlap=20):
        self.text_splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    async def run(self, context: IngestionContext) -> IngestionContext:
        documents: List[LlamaDocument] = context.get("documents")
        if not documents or len(documents) != 1:
            logger.warning(f"ChunkDocument step expects a single document in the context, but found {len(documents) if documents else 0}. Skipping chunking.")
            # Pass through the original documents if they exist
            if documents:
                context.set("parsed_llama_docs", documents)
            return context

        doc = documents[0]
        logger.info(f"Chunking document: {doc.metadata.get('file_name', doc.id_)}")

        try:
            nodes = self.text_splitter.get_nodes_from_documents([doc])
            
            # Convert nodes back to LlamaDocument objects for compatibility
            chunked_docs = [LlamaDocument(text=node.get_content(), metadata=node.metadata) for node in nodes]

            context.set("parsed_llama_docs", chunked_docs)
            logger.success(f"Successfully chunked document into {len(chunked_docs)} smaller documents.")

        except Exception as e:
            logger.error(f"Failed to chunk document {doc.id_}: {e}", exc_info=True)
            context.add_error(e)
            context.abort()

        return context


class ParseDocuments(IngestionStep):
    """An ingestion step to parse documents using LlamaParse."""

    def __init__(self, config: LlamaParseConfig):
        self.parser = DocumentParser(config)

    async def run(self, context: IngestionContext) -> IngestionContext:
        raw_docs: List[LlamaDocument] = context.get("documents")
        if not raw_docs:
            logger.warning("No 'documents' found in context to parse. Skipping parsing step.")
            return context

        # This example processes one document at a time for simplicity.
        # A batching mechanism would be more efficient for production.
        doc_to_parse = raw_docs[0] # Assuming one document for now
        file_path = doc_to_parse.metadata.get('file_path')

        if not file_path:
            msg = "Document in context is missing 'file_path' in metadata for parsing."
            logger.error(msg)
            context.add_error(ValueError(msg))
            context.abort()
            return context

        logger.info(f"Parsing document: {doc_to_parse.metadata.get('file_name')}")
        try:
            # Use the more flexible method that returns LlamaIndex Documents
            parsed_llama_docs = await self.parser.aparse_file(file_path)
            
            # Set context for downstream steps
            context.set("parsed_llama_docs", parsed_llama_docs)
            context.set("source_document_id", doc_to_parse.id_)
            context.set("source_file_name", doc_to_parse.metadata.get('file_name'))

            logger.success(f"Successfully parsed document into {len(parsed_llama_docs)} chunks.")

        except Exception as e:
            logger.error(f"Failed to parse document {file_path}: {e}", exc_info=True)
            context.add_error(e)
            context.abort()

        return context


class ExtractGraph(IngestionStep):
    """An ingestion step to extract graph data from text."""

    def __init__(self, extractor: GraphExtractor, ontology_nodes: List[Type[BaseModel]], ontology_edges: List[Type[BaseModel]]):
        self.extractor = extractor
        self.ontology_nodes = ontology_nodes
        self.ontology_edges = ontology_edges

    async def run(self, context: IngestionContext) -> IngestionContext:
        parsed_docs: List[LlamaDocument] = context.get("parsed_llama_docs")
        source_id = context.get("source_document_id")
        source_name = context.get("source_file_name")

        if not parsed_docs:
            logger.warning("No 'parsed_llama_docs' found in context. Skipping graph extraction.")
            return context

        # Concatenate text from all chunks for a holistic extraction
        full_text_content = "\n\n---\n\n".join([doc.text for doc in parsed_docs])
        logger.info(f"Starting graph extraction from {len(full_text_content)} characters of text for '{source_name}'.")

        try:
            extraction_results = await self.extractor.extract(
                text_content=full_text_content,
                ontology_nodes=self.ontology_nodes,
                ontology_edges=self.ontology_edges,
                group_id=source_id,
                episode_name_prefix=source_name[:50]
            )
            
            context.set("graph_extraction_data", extraction_results)
            nodes_count = len(extraction_results.get('nodes', []))
            edges_count = len(extraction_results.get('edges', []))
            logger.success(f"Graph extraction complete. Found {nodes_count} nodes and {edges_count} edges.")

        except Exception as e:
            logger.error(f"Failed during graph extraction for '{source_name}': {e}", exc_info=True)
            context.add_error(e)
            context.abort()

        return context


class IngestToNeo4j(IngestionStep):
    """An ingestion step to ingest graph data into Neo4j."""

    def __init__(self, ingester: Neo4jIngester):
        self.ingester = ingester

    async def run(self, context: IngestionContext) -> IngestionContext:
        graph_data = context.get("graph_extraction_data")
        source_name = context.get("source_file_name")

        if not graph_data:
            logger.warning("No 'graph_extraction_data' found in context. Skipping Neo4j ingestion.")
            return context

        logger.info(f"Ingesting graph data from '{source_name}' into Neo4j.")
        try:
            ingestion_data = DocumentIngestionData(
                nodes=graph_data.get('nodes', []),
                relationships=graph_data.get('edges', [])
            )
            await self.ingester.ingest_document(ingestion_data)

            nodes_count = len(ingestion_data.nodes)
            edges_count = len(ingestion_data.relationships)
            context.set("ingested_neo4j_nodes", nodes_count)
            context.set("ingested_neo4j_edges", edges_count)
            logger.success(f"Successfully ingested {nodes_count} nodes and {edges_count} edges into Neo4j.")

        except Exception as e:
            logger.error(f"Failed to ingest graph data into Neo4j for '{source_name}': {e}", exc_info=True)
            context.add_error(e)
            context.abort()

        return context


class IngestToChromaDB(IngestionStep):
    """An ingestion step to ingest documents into ChromaDB."""

    def __init__(self, ingester: 'ChromaIngester'):
        self.ingester = ingester

    async def run(self, context: IngestionContext) -> IngestionContext:
        parsed_docs: List[LlamaDocument] = context.get("parsed_llama_docs")
        source_id = context.get("source_document_id")
        source_name = context.get("source_file_name")

        if not parsed_docs:
            logger.warning("No 'parsed_llama_docs' found in context. Skipping ChromaDB ingestion.")
            return context
        
        if not source_id or not source_name:
            msg = "Context is missing 'source_document_id' or 'source_file_name' for ChromaDB ingestion."
            logger.error(msg)
            context.add_error(ValueError(msg))
            context.abort()
            return context

        logger.info(f"Preparing {len(parsed_docs)} chunks from '{source_name}' for ChromaDB ingestion.")
        try:
            chroma_documents = convert_llama_docs_to_chroma_docs(
                llama_docs=parsed_docs,
                source_document_id=source_id,
                source_file_name=source_name
            )
            
            await self.ingester.ingest_documents(chroma_documents)
            
            context.set("ingested_chroma_docs_count", len(chroma_documents))
            logger.success(f"Successfully ingested {len(chroma_documents)} chunks into ChromaDB.")

        except Exception as e:
            logger.error(f"Failed to ingest documents into ChromaDB: {e}", exc_info=True)
            context.add_error(e)
            context.abort()

        return context


class GetYoutubeTranscript(IngestionStep):
    """An ingestion step to load a transcript from a YouTube URL."""

    async def run(self, context: IngestionContext) -> IngestionContext:
        youtube_url = context.get("youtube_url")
        if not youtube_url:
            logger.warning("No 'youtube_url' found in context. Skipping YouTube transcript loading.")
            return context

        logger.info(f"Loading transcript from YouTube URL: {youtube_url}")

        try:
            # Extract video ID from URL
            if "v=" in youtube_url:
                video_id = youtube_url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in youtube_url:
                video_id = youtube_url.split("youtu.be/")[1].split("?")[0]
            else:
                raise ValueError("Invalid YouTube URL format.")

            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
            # Combine transcript parts into a single text block
            transcript_text = " ".join([item['text'] for item in transcript_list])

            # Create a LlamaDocument. This will be chunked by a subsequent step.
            doc = LlamaDocument(
                id_=str(uuid.uuid4()),
                text=transcript_text,
                metadata={
                    "source": "youtube",
                    "video_id": video_id,
                    "youtube_url": youtube_url,
                    "file_name": f"youtube_{video_id}.txt" # for compatibility with downstream steps
                }
            )
            
            # Set the single, raw document in the context
            context.set("documents", [doc])
            context.set("source_document_id", doc.id_) # for compatibility
            context.set("source_file_name", doc.metadata["file_name"]) # for compatibility

            logger.success(f"Successfully loaded transcript for video ID: {video_id}")

        except Exception as e:
            logger.error(f"Failed to load transcript from YouTube URL {youtube_url}: {e}", exc_info=True)
            context.add_error(e)
            context.abort()

        return context
