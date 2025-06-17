1. Introduction and Project GoalsThis document outlines the technical
   specifications for a Graph-Powered Hybrid Retrieval Augmented Generation
   (Graph RAG) system. The primary objective is to develop a robust and scalable
   solution capable of ingesting diverse document sources, including those from
   Google Drive, constructing a dynamic knowledge graph, and enabling
   sophisticated querying through a combination of graph-based and vector-based
   retrieval mechanisms. The system will leverage the graphitti framework for
   knowledge graph creation and management within a Neo4j AuraDB instance.
   Retrieval and generation will be orchestrated by LlamaIndex, utilizing
   Google's latest Gemini models via Vertex AI. A Supabase vector store will
   serve as a complementary retrieval source for unstructured text. The user
   interface will be a Streamlit-based chat application.A key aspect of this
   project is the investigation into the feasibility and potential benefits of
   incorporating Agentic RAG principles to enhance the system's reasoning and
   retrieval capabilities. This document will detail the architecture, component
   specifications, data flows, integration points, and deployment
   considerations, providing a comprehensive technical blueprint for
   development.Core Project Goals: Develop a data ingestion pipeline using
   graphitti to process documents from various sources, including Google Drive
   (authenticated via a service account key), and build a temporally-aware
   knowledge graph in Neo4j AuraDB. Implement a hybrid retrieval system
   combining structured graph queries (keyword, semantic, path-based) from Neo4j
   with semantic vector search from Supabase. Integrate Google Gemini models
   (via Vertex AI) for natural language understanding, generation, and embedding
   tasks, orchestrated by LlamaIndex. Provide a Streamlit-based chat interface
   for user interaction, potentially complemented by advanced graph
   visualization tools like Neo4j Bloom. Evaluate the potential of Agentic RAG
   to improve query understanding, retrieval strategy, and overall system
   performance. Ensure robust integration with specified Google Cloud Platform
   (GCP) services.
2. System Architecture OverviewThe proposed system architecture is designed
   around a modular set of components facilitating data ingestion, knowledge
   graph construction, hybrid retrieval, language model interaction, and user
   interfacing.Key Components: Data Ingestion & Knowledge Graph Creation
   (graphitti & Neo4j AuraDB): Documents are processed by graphitti, which
   extracts entities and relationships, populating a Neo4j AuraDB knowledge
   graph. This component is responsible for maintaining the temporal accuracy
   and dynamic nature of the graph. Document loading from sources like Google
   Drive will be handled by LlamaIndex readers, using a service account key for
   authentication. Vector Store (Supabase): Alongside the knowledge graph,
   relevant text chunks or documents will be embedded and stored in a Supabase
   PostgreSQL database utilizing the pgvector extension for efficient similarity
   search. Orchestration & Retrieval (LlamaIndex): LlamaIndex will serve as the
   central framework for managing data (including loading from Google Drive),
   orchestrating retrieval from both Neo4j and Supabase, and interacting with
   the LLM. Language Model Services (Google Gemini via Vertex AI): Google's
   Gemini models, accessed through Vertex AI, will provide the core AI
   capabilities for embedding generation, natural language understanding, and
   response generation. User Interface (Streamlit): A Streamlit application will
   provide a chat-based interface for users to interact with the RAG system.
   (Optional) Agentic Layer (Google ADK or LlamaIndex Agents): If implemented,
   an agentic layer would sit atop the retrieval and LLM components to enable
   more complex reasoning and tool use. Diagram 1: High-Level System
   ArchitectureCode snippetgraph TD A --> LA; LA -- Documents --> B{graphitti
   Engine}; B -- Entities & Relationships --> C; LA -- Text Chunks -->
   D{Embedding Model via Vertex AI}; D -- Embeddings --> E; F[User] --> G; G --
   Query --> H{LlamaIndex Orchestrator}; H -- Graph Query --> C; H -- Vector
   Query --> E; C -- Retrieved Graph Context --> H; E -- Retrieved Vector
   Context --> H; H -- Prompt + Context --> I{Gemini LLM via Vertex AI}; I --
   Generated Response --> H; H -- Final Answer --> G; This architecture supports
   a hybrid retrieval strategy where context can be pulled from the structured
   knowledge graph (offering precision and relationship-based insights) and the
   vector store (offering broad semantic similarity). The LlamaIndex
   orchestrator is pivotal in managing these heterogeneous data sources and
   synthesizing them for the LLM.3. Data Ingestion and Knowledge Graph Creation
   with graphittiThe foundation of the Graph RAG system is the dynamic knowledge
   graph (KG) built and maintained by graphitti. graphitti is specifically
   designed for AI agents operating in dynamic environments, offering
   capabilities beyond traditional RAG by continuously integrating data into a
   coherent, queryable graph.13.1. graphitti-core Overviewgraphitti-core is a
   Python framework for building and querying temporally-aware knowledge
   graphs.1 Its core strength lies in its ability to autonomously construct a KG
   while managing changing relationships and preserving historical context.1
   This is achieved through real-time incremental updates, eliminating the need
   for batch recomputation when new data arrives.1 A bi-temporal data model
   tracks both the event occurrence time and ingestion time, enabling precise
   point-in-time queries and analysis of data evolution.1Key features relevant
   to this project include: Real-Time Incremental Updates: New data episodes are
   immediately integrated without requiring full graph recomputation.1
   Bi-Temporal Data Model: Tracks event occurrence and ingestion times for
   historical accuracy.1 Efficient Hybrid Retrieval: Combines semantic
   embeddings, keyword (BM25) search, and graph traversal for low-latency
   queries, often without LLM summarization during retrieval.1 Custom Entity
   Definitions: Supports flexible ontology creation using Pydantic models to
   define domain-specific entities, enhancing the precision of context
   extraction.1 This allows for a more guided and structured information
   extraction process by the LLM, moving beyond generic entity recognition. LLM
   Integration: graphitti leverages LLMs for inference and embedding. It
   performs optimally with LLMs that support structured output, such as Google
   Gemini, as this ensures correct schema mapping and reduces ingestion
   failures.1 The quality of the graph built by graphitti is therefore directly
   influenced by the structured output capabilities of the chosen Gemini model.
   3.2. Neo4j AuraDB ConfigurationThe system will use a Neo4j AuraDB instance as
   the backend for graphitti. Connection details are provided in the .env file
   and confirmed by the latest user-provided images: NEO4J_URI:
   neo4j+s://037bf8a4.databases.neo4j.io (User-provided image) NEO4J_USER: neo4j
   (User-provided image) NEO4J_PASSWORD:
   o1ocsUT2c2Ye-3B2nkMHwppzYeK6Z3YBIxVM2LwZgk (User-provided image)
   NEO4J_DATABASE: neo4j (User-provided image) AURA_INSTANCEID: 037bf8a4
   (User-provided image) AURA_INSTANCENAME: Instance01 (User-provided image)
   graphitti will manage the schema, indices, and constraints within this Neo4j
   database.13.3. graphitti Schema: Nodes, Edges, and PropertiesWhile graphitti
   can autonomously build a KG, its schema is influenced by the input data and
   any custom entity definitions provided.1 Based on graphitti's design: Nodes
   (Entities): Represent extracted entities from documents (e.g., persons,
   organizations, locations, concepts). Nodes will have labels (e.g., Entity, or
   custom types defined via Pydantic models like Person, Company).

Properties: id (unique identifier), name (entity name), description
(LLM-generated summary if applicable), embedding (vector embedding for semantic
search), temporal properties managed by graphitti.

Edges (Relationships): Represent connections between entities (e.g., "works_at",
"located_in", "mentions"). Edges will have types (e.g., RELATES_TO, or more
specific types derived by the LLM).

Properties: source_node_id, target_node_id, description (context of the
relationship), t_valid (when the relationship became valid), t_invalid (when it
became invalid), t_ingested (when it was added to the graph).1

Episode Nodes: graphitti processes data as "episodes".1 These episodes (e.g., a
document, a user interaction) are linked to the entities and relationships
extracted from them, providing provenance. Text Chunks/Source Nodes: The raw
text from which information is extracted might be stored or referenced, linking
back to the entities and relationships to provide grounding for RAG. graphitti's
bi-temporal model is a significant differentiator. It explicitly tracks when an
event occurred in the real world and when it was ingested into the graph. Each
relationship (edge) includes validity intervals (t_valid, t_invalid), allowing
the system to preserve historical accuracy without discarding outdated
information, which is crucial for dynamic datasets.13.4. Document Processing
Pipeline with graphitti Input: Documents from various sources. This includes
files from a specified Google Drive folder (identified by DRIVE_FOLDER_ID in the
environment configuration, e.g., 1vbJ-5VnV_gTlegoW0bO0A26gR7rwJDajm). Document
loading from Google Drive will be handled by LlamaIndex's GoogleDriveReader.
Authentication will utilize a service account, with the path to its JSON key
file specified by the SERVICE_ACCOUNT_KEY_PATH environment variable (e.g.,
C:\Users\kevin\repos\kev-graph-rag\src\service_account_key.json). The
IMPERSONATED_USER_EMAIL (e.g., kevin@clearspringcg.com) suggests that this
service account may be configured with domain-wide delegation to act on behalf
of this user, or that the service account itself has been granted direct access
to the specified Google Drive folder and its contents. LlamaIndex Document
Loading: LlamaIndex readers (e.g., GoogleDriveReader, SimpleDirectoryReader)
convert source files into LlamaIndex Document objects. Preprocessing: Standard
text cleaning, potentially document parsing within LlamaIndex or prior to
graphitti ingestion. Episode Creation: The text content of LlamaIndex Document
objects is treated as an "episode" by graphitti.1 Entity & Relationship
Extraction: graphitti uses the configured LLM (Gemini) to extract entities and
their relationships from the episode content. If custom Pydantic entity types
are defined, the LLM will be guided to extract these specific structures.1
Embedding Generation: The configured embedder (Gemini) generates embeddings for
entities and potentially relationships or text chunks for semantic search
capabilities within graphitti. Graph Update: Extracted entities and
relationships are added to the Neo4j graph. graphitti handles de-duplication of
nodes and manages the temporal lifecycle of relationships.1 Indexing: graphitti
ensures necessary indices (vector and BM25 keyword) are created in Neo4j for
efficient retrieval.1 3.5. Key Code Examples: graphitti Initialization and Data
Ingestion

Loading Documents from Google Drive with LlamaIndex: Python# Based on LlamaIndex
documentation and.env (User-provided image for SERVICE_ACCOUNT_KEY_PATH) import
os from llama_index.readers.google import GoogleDriveReader from
llama_index.core import Document # For type hinting

# Configuration from.env

DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID",
"1vbJ-5VnV_gTlegoW0bO0A26gR7rwJDajm")

# Path to the service account key JSON file from.env

SERVICE_ACCOUNT_KEY_PATH = os.getenv("SERVICE_ACCOUNT_KEY_PATH")

if not SERVICE_ACCOUNT_KEY_PATH: print("Error: SERVICE_ACCOUNT_KEY_PATH
environment variable not set.") # Handle error appropriately, e.g., raise an
exception or skip Drive loading documents_from_drive = else: try: gdrive_reader
= GoogleDriveReader( folder_id=DRIVE_FOLDER_ID, # The service_account_key
parameter expects the path to the JSON key file.
service_account_key=SERVICE_ACCOUNT_KEY_PATH ) # documents_from_drive: list =
gdrive_reader.load_data() # print(f"Loaded {len(documents_from_drive)} documents
from Google Drive folder: {DRIVE_FOLDER_ID}") except Exception as e:
print(f"Error initializing or loading from GoogleDriveReader: {e}") #
print("Ensure SERVICE_ACCOUNT_KEY_PATH is correct, the file exists,") #
print("and the service account has access to the Drive folder and Drive API is
enabled.") documents_from_drive =

Initializing graphitti with Google Gemini (via Vertex AI context):The .env file
(Image 1) specifies Gemini models and a Google Cloud Project. graphitti-core
supports Google Gemini through the graphiti-core[google-genai] extra.1 Python#
Based on [1] and user-provided images for Neo4j credentials from graphiti_core
import Graphiti from graphiti_core.llm_client.gemini_client import GeminiClient,
LLMConfig from graphiti_core.embedder.gemini import GeminiEmbedder,
GeminiEmbedderConfig

# From user-provided images and.env

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://037bf8a4.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j") NEO4J_PASSWORD =
os.getenv("NEO4J_PASSWORD", "o1ocsUT2c2Ye-3B2nkMHwppzYeK6Z3YBIxVM2LwZgk")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") # From previous.env

LLM_MODEL_FOR_GRAPHITTI = os.getenv("LLM_MODEL", "gemini-2.5-pro")
EMBED_MODEL_FOR_GRAPHITTI = "embedding-001" # As per graphiti's GeminiEmbedder
example [1]

# graphiti_instance = Graphiti(

# NEO4J_URI,

# NEO4J_USER,

# NEO4J_PASSWORD,

# llm_client=GeminiClient(

# config=LLMConfig(

# api_key=GOOGLE_API_KEY,

# model=LLM_MODEL_FOR_GRAPHITTI

# )

# ),

# embedder=GeminiEmbedder(

# config=GeminiEmbedderConfig(

# api_key=GOOGLE_API_KEY,

# embedding_model=EMBED_MODEL_FOR_GRAPHITTI

# )

# )

# )

# print("Graphiti initialized with Gemini clients.")

Adding text episodes (from LlamaIndex Documents) to the graph: Python#
Conceptual example, assuming 'documents_from_drive' is a list of LlamaIndex
Document objects

# and 'graphiti_instance' is initialized.

# for doc in documents_from_drive:

# episode_content = doc.text

# source_description = f"Google Drive Document: {doc.metadata.get('file_name', 'Unknown')}"

# graphiti_instance.add_episode(

# text=episode_content,

# source_description=source_description,

# group_id="google_drive_documents",

# metadata=doc.metadata

# )

# print(f"Added episode from: {source_description}")

The dynamic, incremental updates and bi-temporal model of graphitti are central
to its utility.1 This ensures the KG can reflect evolving information without
costly rebuilds, a critical feature for systems dealing with frequently changing
data sources. The ability to define custom entity types via Pydantic models
provides a powerful mechanism to tailor the knowledge extraction process to
specific domain requirements, yielding a more semantically rich and accurate
KG.14. Hybrid Retrieval Strategy with LlamaIndexThe system will employ a hybrid
retrieval strategy, orchestrated by LlamaIndex, drawing information from both
the Neo4j knowledge graph (populated by graphitti) and a Supabase vector store.
This approach aims to combine the strengths of structured, contextual graph
queries with broad semantic vector search.4.1. Neo4j Graph RetrievalLlamaIndex
provides robust integrations for Neo4j, allowing for diverse query mechanisms
against the graph.7 Keyword Search: Leveraging Neo4j's native full-text indexing
capabilities and graphitti's use of BM25 indexing for efficient keyword searches
on node and edge properties.1 Vector Semantic Search: graphitti stores
embeddings for entities (and potentially relationships) within Neo4j. LlamaIndex
can perform semantic similarity searches against these embeddings.1 Graph
Traversal (Cypher Queries): For complex queries involving paths, subgraphs, or
specific relationship patterns, direct Cypher queries are essential.
LlamaIndex's TextToCypherRetriever can translate natural language questions into
Cypher queries.7 The effectiveness of this translation is highly dependent on
the LLM's understanding of the graph schema and its ability to generate correct
Cypher. To mitigate potential inaccuracies, LlamaIndex Workflows can be employed
to implement multi-step approaches involving retries or self-correction
mechanisms for the generated Cypher queries, as this technology is still
evolving.8 graphitti-Specific Retrieval: graphitti itself offers predefined
search recipes and a hybrid search mechanism for relationships/edges, which can
be exposed and utilized through LlamaIndex if custom tools are built.1 4.2.
Supabase Vector Store RetrievalA Supabase PostgreSQL instance, configured with
the pgvector extension, will serve as the vector store for RAG embeddings from
general document content. Configuration: LlamaIndex's SupabaseVectorStore will
be used.9 Connection parameters will be derived from the .env file (Image 1):

SUPABASE_URL: https://odpykcmtcwmyfolsrgcu.supabase.co SUPABASE_KEY: (Service
Role Key from .env) SUPABASE_PROJECT_ID: odpykcmtcwmyfolsrgcu (derived from URL)
SUPABASE_DATABASE_PASSWORD: Hlabaysirdtgycu SUPABASE_DATABASE_NAME: postgres The
postgres_connection_string for LlamaIndex will be constructed as:
postgresql://postgres:{SUPABASE_DATABASE_PASSWORD}@db.{SUPABASE_PROJECT_ID}.supabase.co:5432/{SUPABASE_DATABASE_NAME}.

Embedding Model: The EMBED_MODEL_LLM variable from .env (Image 1:
models/gemini-2.5-flash) will be used via Vertex AI, integrated
with LlamaIndex. The choice of embedding model impacts both graphitti's internal
semantic search and the Supabase vector store. Consistency in embedding models
or a clear strategy for handling potentially different embedding spaces is
important to ensure coherent semantic retrieval across both stores. Metadata
Filtering: Supabase and pgvector, when used with LlamaIndex, support metadata
filtering, allowing vector searches to be refined based on specific document
attributes.7 4.3. Fusion and Re-ranking of Heterogeneous ResultsCombining
results from Neo4j (which may include structured data, entity summaries,
relationship details, and text chunks linked to graph elements) and Supabase
(primarily text chunks with vector similarity scores) is a critical step.
Strategies:

LlamaIndex's RouterRetriever can be configured to direct queries to the
appropriate store (Neo4j or Supabase) or to query both and merge results.9
Custom LlamaIndex query pipelines can be designed to implement more
sophisticated fusion logic.

Re-ranking:

Standard re-ranking algorithms like Reciprocal Rank Fusion (RRF) can be applied.
graphitti offers a graph distance-based re-ranking mechanism, which could be
particularly useful if a central topic or entity from the query can be
identified in the graph.1 This method prioritizes results that are closely
connected to the query's core subject within the graph structure.

The hybrid retrieval approach is fundamental. Neo4j, powered by graphitti's
model, provides access to structured, contextual, and temporally nuanced
information. Supabase complements this with efficient semantic search over
potentially larger or different corpora of text. The main challenge and
opportunity lie in the intelligent fusion of these diverse result sets to
provide the most comprehensive context to the LLM.4.4. Key Code Examples:
LlamaIndex Retriever Configurations

Initializing SupabaseVectorStore and VectorStoreIndex: Python# Based on [9, 10]
and.env (Image 1) from llama_index.vector_stores.supabase import
SupabaseVectorStore from llama_index.core import VectorStoreIndex,
StorageContext from llama_index.embeddings.vertex import VertexAIEmbedding from
llama_index.core.settings import Settings

PROJECT_ID_SUPA = os.getenv("SUPABASE_PROJECT_ID", "odpykcmtcwmyfolsrgcu")
DB_PASSWORD_SUPA = os.getenv("SUPABASE_DATABASE_PASSWORD", "Hlabaysirdtgycu")
DB_NAME_SUPA = os.getenv("SUPABASE_DATABASE_NAME", "postgres")

postgres_connection_string =
f"postgresql://postgres:{DB_PASSWORD_SUPA}@db.{PROJECT_ID_SUPA}.supabase.co:5432/{DB_NAME_SUPA}"
collection_name = "rag_document_embeddings" embedding_dimension = 768

try: vector_store_supabase = SupabaseVectorStore(
postgres_connection_string=postgres_connection_string,
collection_name=collection_name, dimension=embedding_dimension )
print(f"SupabaseVectorStore for collection '{collection_name}' initialized
conceptually.") except Exception as e: print(f"Error initializing
SupabaseVectorStore: {e}")

Initializing Neo4j graph store and relevant retrievers: Python# Based on [7] and
user-provided images for Neo4j credentials from llama_index.core import
PropertyGraphIndex from llama_index.graph_stores.neo4j import
Neo4jPropertyGraphStore from llama_index.retrievers.neo4jgraph import
Neo4jGraphRetriever from llama_index.core.query_engine import
RetrieverQueryEngine from llama_index.llms.vertex import VertexAI from
llama_index.core.settings import Settings

NEO4J_URI_ENV = os.getenv("NEO4J_URI", "neo4j+s://037bf8a4.databases.neo4j.io")
NEO4J_USER_ENV = os.getenv("NEO4J_USER", "neo4j") NEO4J_PASSWORD_ENV =
os.getenv("NEO4J_PASSWORD", "o1ocsUT2c2Ye-3B2nkMHwppzYeK6Z3YBIxVM2LwZgk")
NEO4J_DATABASE_ENV = os.getenv("NEO4J_DATABASE", "neo4j")

try: graph_store_neo4j = Neo4jPropertyGraphStore( username=NEO4J_USER_ENV,
password=NEO4J_PASSWORD_ENV, url=NEO4J_URI_ENV, database=NEO4J_DATABASE_ENV, )
print("Neo4jPropertyGraphStore initialized.") print("Neo4j retrievers
(conceptual) initialized.") except Exception as e: print(f"Error initializing
Neo4j components: {e}")

5. LLM Integration: Google Gemini via Vertex AIThe system will use Google's
   Gemini models, accessed through Vertex AI, for all core LLM tasks, including
   natural language understanding, response generation, and embedding creation.
   LlamaIndex will facilitate the integration with these models.5.1. Model
   Selection and ConfigurationThe .env file (Image 1) specifies the Gemini
   models to be used: Primary LLM for Generation:
   LLM_MODEL="gemini-2.5-pro" (from .env). This model will be used
   for synthesizing answers from retrieved context. Embedding Model:
   EMBED_MODEL_LLM="models/gemini-2.5-flash" (from .env). This
   model is designated for creating embeddings. Fallback LLM:
   FALLBACK_LLM_MODEL="gemini-2.5-flash" (from .env). This model
   can be used if the primary generation model is unavailable or for less
   critical generation tasks to optimize cost/latency. The selection of a
   "flash" model for embeddings and fallback generation is a common practice,
   aiming to balance performance with cost-efficiency. More powerful "pro"
   models are reserved for the final answer synthesis where quality is
   paramount.Vertex AI Configuration: GCP_PROJECT_ID: neo4j-deployment-new1
   (Confirmed by user-provided images). GCP_LOCATION: us-central1 (From previous
   .env images, not contradicted by new ones). Table 1: Google Gemini Model
   Configurations and Usage PurposeModel Name (from.env)Vertex AI IdentifierKey
   Configuration Parameters Main
   GenerationLLM_MODELgemini-2.5-protemperature: 0.28,
   max_output_tokens: 1024 (adjust as
   needed)EmbeddingEMBED_MODEL_LLMgemini-embedding-001 (or compatible Gemini Flash
   endpoint)N/A (uses specific embedding API)Fallback
   GenerationFALLBACK_LLM_MODELgemini-2.5-flashtemperature: 0.3,
   max_output_tokens: 512 (adjust as needed)graphitti Internal LLMLLM_MODEL (or
   specific)gemini-2.5-pro(Depends on graphitti's internal
   needs)graphitti EmbedderEMBED_MODEL_LLMembedding-001 (as per graphiti
   example 1) or compatible Gemini Flash endpointN/A A potential discrepancy
   exists: EMBED_MODEL_LLM is set to models/gemini-2.5-flash,
   which is a generative model identifier. Vertex AI typically uses specific
   embedding model IDs like gemini-embedding-001 or multimodalembedding@001.
   graphitti-core's GeminiEmbedder 1 uses embedding-001 in its example.
   LlamaIndex's VertexAIEmbedding class expects specific embedding model names
   (e.g., gemini-embedding-001).11 This needs to be resolved to ensure consistent
   and correct embedding generation across graphitti and LlamaIndex. If
   gemini-2.5-flash cannot directly serve as an embedding model ID
   for VertexAIEmbedding, then a model like gemini-embedding-001 should be used
   for LlamaIndex, and graphitti's configuration must be aligned or
   verified.5.2. LlamaIndex Integration with Vertex AI for GeminiLlamaIndex will
   connect to Gemini models on Vertex AI using the llama-index-llms-vertex and
   llama-index-embeddings-vertex integrations.11 Alternatively, for more
   structured agentic workflows,
   vertexai.preview.reasoning_engines.LlamaIndexQueryPipelineAgent could be
   considered if building Vertex AI native agents.12Authentication will
   primarily rely on Application Default Credentials (ADC) when the application
   is running within a GCP environment (e.g., Cloud Run, GKE, GCE). The
   GOOGLE_API_KEY provided in the .env (Image 1, Image 2) might be used for
   local development or if ADC is not set up. The IMPERSONATED_USER_EMAIL
   (kevin@clearspringcg.com from Image 1, Image 2, user-provided image) suggests
   that service account impersonation might be used, allowing the application to
   run with the permissions of this specified service account.5.3. Prompt
   Engineering for Graph RAG ContextEffective prompt engineering is crucial for
   guiding the Gemini LLM to synthesize information accurately from the diverse
   contexts retrieved from Neo4j and Supabase. Prompts should be designed to:
   Clearly present the retrieved context, distinguishing between graph-derived
   information (entities, relationships, summaries) and text chunks from the
   vector store. Instruct the LLM to synthesize these varied pieces of
   information into a coherent answer. Encourage the LLM to respect temporal
   aspects if the query implies or graphitti provides relevant temporal
   metadata. Request citations or references back to the source data segments to
   enhance transparency and verifiability. 5.4. Key Code Examples: LLM
   Initialization and Invocation within LlamaIndex

Initializing VertexAI LLM and VertexAIEmbedding in LlamaIndex: Python# Based on
[11] and user-provided images for GCP Project ID from llama_index.llms.vertex
import VertexAI from llama_index.embeddings.vertex import VertexAIEmbedding from
llama_index.core.settings import Settings

GCP_PROJECT_ID_ENV = os.getenv("GCP_PROJECT_ID", "neo4j-deployment-new1")
GCP_LOCATION_ENV = os.getenv("GCP_LOCATION", "us-central1") LLM_MODEL_ENV =
os.getenv("LLM_MODEL", "gemini-2.5-pro") EMBEDDING_MODEL_ID_VERTEX
= "gemini-embedding-001"

llm_model_kwargs = { "temperature": 0.28, "max_output_tokens": 1024, }

try: Settings.llm = VertexAI( model=LLM_MODEL_ENV, project=GCP_PROJECT_ID_ENV,
location=GCP_LOCATION_ENV, additional_kwargs=llm_model_kwargs )

    Settings.embed_model = VertexAIEmbedding(
        model_name=EMBEDDING_MODEL_ID_VERTEX,
        project=GCP_PROJECT_ID_ENV,
        location=GCP_LOCATION_ENV,
    )
    print(f"VertexAI LLM ({LLM_MODEL_ENV}) and Embedder ({EMBEDDING_MODEL_ID_VERTEX}) configured globally for LlamaIndex.")

except Exception as e: print(f"Error configuring VertexAI models for LlamaIndex:
{e}")

Passing retrieved context to the LLM via a LlamaIndex query engine:This is
typically handled internally by LlamaIndex's query engines (e.g.,
RetrieverQueryEngine). The engine takes the retrieved NodeWithScore objects,
formats them into a context string (respecting context window limits), and
prepends this context to the user query within a larger prompt template before
sending it to the LLM. Python# Conceptual example of how a LlamaIndex query
engine uses the LLM

# from llama_index.core.query_engine import RetrieverQueryEngine

# from llama_index.core.response_synthesizers import get_response_synthesizer

# Assuming 'retriever' is a configured LlamaIndex retriever (hybrid, graph, or vector)

# response_synthesizer = get_response_synthesizer(llm=Settings.llm)

# query_engine = RetrieverQueryEngine(

# retriever=retriever,

# response_synthesizer=response_synthesizer

# )

# user_query = "What were the key findings in the latest financial report?"

# response_object = query_engine.query(user_query)

# print(f"Answer: {response_object.response}")

# for source_node in response_object.source_nodes:

# print(f"Source Node ID: {source_node.node_id}, Score: {source_node.score}")

# print(f"Source Text: {source_node.text[:200]}...") # Display snippet of source

6. Agentic RAG: Feasibility and Implementation PathwaysAgentic RAG involves
   using AI agents to enhance the Retrieval Augmented Generation process,
   enabling more complex reasoning, dynamic tool use, and multi-step
   interactions to address user queries.136.1. Assessing the Value of Agentic
   RAG for This ProjectAgentic RAG offers several potential benefits:
   Flexibility: Agents can dynamically choose to query multiple data sources
   (like Neo4j and Supabase) or use various tools based on the query's nature.13
   Adaptability: Instead of static rule-based retrieval, agents can adapt their
   strategy, potentially performing multi-hop queries in the graph or
   reformulating queries if initial results are insufficient.13 Accuracy: Agents
   could potentially validate information or cross-reference findings from
   different sources, leading to more accurate and reliable answers.13 However,
   these advantages come with trade-offs: Increased Complexity: Designing,
   implementing, and orchestrating multiple agents adds significant
   architectural and developmental complexity. Higher Cost and Latency: Agentic
   systems often involve more LLM calls for planning, tool selection, and
   reasoning by the agent itself, which can increase token consumption and
   overall response time.13 For this project, an agentic approach could be
   valuable if queries are often complex, ambiguous, or require synthesizing
   information from disparate parts of the knowledge graph and vector store in
   non-obvious ways. For instance, an agent could decide whether a query is best
   answered by historical graph data, current vector embeddings, or a
   combination, a task that might otherwise require intricate hard-coded
   logic.6.2. Potential Agent Design and RolesIf an agentic approach is adopted,
   several specialized agents could collaborate: Query Planner Agent: Analyzes
   the incoming user query, breaks it down if necessary, and determines the
   optimal retrieval strategy (e.g., graph-first, vector-first, parallel hybrid,
   specific graph traversal path, use of graphitti's temporal query features).
   Graph Query Agent: Specializes in interacting with the Neo4j knowledge graph.
   This agent could formulate Cypher queries (potentially using TextToCypher
   capabilities) or execute predefined graph algorithms. It would be responsible
   for leveraging graphitti's specific data model, including temporal aspects.
   Vector Store Agent: Focuses on querying the Supabase vector store, handling
   embedding generation for the query, and applying metadata filters.
   Synthesizer Agent: Receives context from the Graph Query Agent and Vector
   Store Agent, then prompts the main Gemini generation model to produce a
   final, coherent answer, ensuring all relevant information is integrated and
   cited. (Optional) Validation Agent: Could be tasked with checking the
   consistency of retrieved information or using external tools/APIs to verify
   facts before final synthesis. 6.3. Implementation Approaches: Google ADK vs.
   LlamaIndex AgentsTwo primary frameworks are considered for implementing an
   agentic layer:

Google Agent Development Kit (ADK):

An open-source Python toolkit designed for building, evaluating, and deploying
AI agents. While optimized for Gemini and the Google ecosystem, it is
model-agnostic and compatible with other frameworks.15 Features: Provides a rich
tool ecosystem (including pre-built tools, custom functions, OpenAPI
integration), code-first development, support for modular multi-agent systems
(with coordinator agents), and deployment options on Google Cloud Run or Vertex
AI Agent Engine.15 ADK supports both deterministic workflow agents (sequential,
parallel, loop) and LLM-driven dynamic routing for adaptive behavior.16 A
notable feature is its support for MCP (Model Context Protocol) tools.16 Given
that graphitti provides an MCP server 1, an ADK agent could potentially
interface with the graphitti-managed KG via this protocol, creating a
streamlined integration path. While general ADK documentation exists 16,
specific examples for RAG with multiple heterogeneous data source tools and
complex retriever choice logic were not readily found in the initial research.16

LlamaIndex Agents:

LlamaIndex itself offers abstractions for building agents, often leveraging its
existing data connectors, index structures, and query engines as tools.17 Agents
in LlamaIndex can use QueryEngineTool to interact with different data sources
(e.g., one for Neo4j, one for Supabase).17 LlamaIndex Workflows provide a way to
implement more complex, multi-step agentic processes, including error handling
and retries (e.g., for Text2Cypher).8 Since the core RAG pipeline is already
being built with LlamaIndex, extending it with LlamaIndex agents might offer a
more integrated development experience.

6.4. Recommendation and RationaleFor the initial version of this Graph RAG
system, it is recommended to start with a non-agentic, LlamaIndex-orchestrated
hybrid retrieval pipeline. This involves using LlamaIndex's standard retrievers
(e.g., Neo4jGraphRetriever, VectorStoreIndexRetriever) and potentially a
RouterRetriever or custom query pipeline to manage the flow between Neo4j and
Supabase.Rationale: Complexity Management: Building a robust hybrid RAG system
with graphitti, Neo4j, Supabase, and Gemini is already a complex undertaking.
Introducing an agentic layer from the outset significantly increases this
complexity. Baseline Performance: Establishing a strong baseline with a
well-tuned non-agentic RAG system is crucial before evaluating the incremental
benefits of an agentic approach. LlamaIndex Capabilities: LlamaIndex's existing
components (routers, query transformations, pipelines) can handle many aspects
of hybrid retrieval and conditional logic without requiring a full agentic
framework. Agentic RAG should be considered a Phase 2 enhancement. Once the core
system is stable and its limitations are understood, an agentic layer can be
introduced to address specific shortcomings or enable more sophisticated query
handling.If proceeding to Agentic RAG in a later phase: LlamaIndex Agents would
be a natural first choice due to the existing deep integration with LlamaIndex
for retrieval and LLM interaction. This would likely offer a smoother
development path. Google ADK could be considered if the project requires more
complex multi-agent orchestration, tighter integration with Vertex AI Agent
Engine for deployment, or if the MCP integration with graphitti proves to be a
significant advantage. Table 2: Agentic RAG Implementation Approach Comparison
(for future consideration) Feature/AspectGoogle ADKLlamaIndex
AgentsNotes/Recommendation (for Phase 2)Integration with LlamaIndex
CoreIndirect; ADK tools would need to wrap LlamaIndex retrievers/query
engines.Native; agents are built on LlamaIndex components.LlamaIndex offers
tighter integration for a system already using LlamaIndex.Gemini Model
SupportOptimized for Gemini; first-class support. 15Excellent support via
llama-index-llms-vertex.Both are strong.Multi-Agent OrchestrationSupports
multi-agent systems and various workflow agents (sequential, parallel, loop).
15Possible via LlamaIndex Workflows or custom agent compositions.ADK appears
more explicitly designed for complex multi-agent hierarchies.Tool UsageRich tool
ecosystem, including MCP tools, OpenAPI, custom functions. 15Flexible tool
usage, primarily through QueryEngineTool and FunctionTool. 17ADK's MCP tool
support is a potential advantage for graphitti. LlamaIndex tools are
well-integrated with its data abstractions.Deployment on GCPDesigned for Cloud
Run, Vertex AI Agent Engine. 15Deployable on any Python-supporting GCP service
(Cloud Run, GKE, GCE).ADK has more specialized deployment paths within Vertex
AI.Community/DocsGrowing; good documentation for core features. 15Large, active
community; extensive documentation and examples. 7LlamaIndex currently has a
larger user base and more readily available examples for diverse RAG
scenarios.Learning CurveModerate; introduces new concepts and a specific
framework.Lower if already familiar with LlamaIndex concepts.Leveraging existing
LlamaIndex expertise would be faster.graphitti MCP Server IntegrationPotential
direct integration via ADK's MCP tools. 16Would require a custom LlamaIndex tool
to act as an MCP client.ADK might offer a more out-of-the-box solution here if
graphitti MCP is central. 6.5. Key Code Examples (Conceptual for Phase 2)

Conceptual LlamaIndex agent using tools: Python# Based on [17] (Memgraph
example, adapted for Neo4j/Supabase)

# Ensure Settings.llm is configured (see section 5.4)

# from llama_index.core.tools import QueryEngineTool

# from llama_index.core.agent import ReActAgent

# Assume query_engine_neo4j and query_engine_supabase are defined LlamaIndex query engines

# neo4j_tool = QueryEngineTool.from_defaults(

# query_engine_neo4j,

# name="neo4j_knowledge_graph_retriever",

# description="Retrieves information about entities, relationships, and events from the Neo4j knowledge graph."

# )

# supabase_tool = QueryEngineTool.from_defaults(

# query_engine_supabase,

# name="supabase_document_vector_retriever",

# description="Retrieves relevant text chunks from a large corpus of documents stored in Supabase."

# )

# agent = ReActAgent.from_tools(

# [neo4j_tool, supabase_tool],

# llm=Settings.llm,

# verbose=True

# )

# response = agent.chat("Compare Company X in Q1 2023 (from graph) with news sentiment (from documents).")

# print(response)

Conceptual Google ADK agent definition: Python# Based on [15]

# from google.adk.agents import Agent

# from google.adk.tools import FunctionTool

# Assume LlamaIndex query engines (query_engine_neo4j, query_engine_supabase) are accessible

# def query_neo4j_via_llamaindex(query_str: str) -> str:

# return "Mocked Neo4j response for: " + query_str

# def query_supabase_via_llamaindex(query_str: str) -> str:

# return "Mocked Supabase response for: " + query_str

# neo4j_adk_tool = FunctionTool(

# name="query_knowledge_graph",

# description="Queries the Neo4j knowledge graph.",

# func=query_neo4j_via_llamaindex

# )

# supabase_adk_tool = FunctionTool(

# name="query_document_store",

# description="Queries the Supabase vector store.",

# func=query_supabase_via_llamaindex

# )

# rag_agent_adk = Agent(

# name="hybrid_rag_assistant_adk",

# model="gemini-2.5-pro",

# instruction="Answer user questions by retrieving and synthesizing information from a knowledge graph and a document vector store.",

# tools=[neo4j_adk_tool, supabase_adk_tool],

# )

# result = rag_agent_adk.process("What is the relationship between ClearSpring and Zep AI from the knowledge graph?")

# print(result.response_text if result else "No response from ADK agent.")

7. User Interface: Streamlit ApplicationA Streamlit application will serve as
   the primary user interface for interacting with the Graph RAG system.
   Streamlit is chosen for its rapid development capabilities and ease of
   creating interactive web applications for data science projects.197.1. Core
   Chat Functionality and Interaction FlowThe chat interface will be built using
   Streamlit's native chat elements: st.chat_input: For users to type and submit
   their queries.19 st.chat_message: To display the conversation history,
   differentiating between user messages and assistant responses.19
   st.session_state: To store and manage the chat history across user
   interactions, ensuring conversation context is maintained within a session.19
   The interaction flow will be: User enters a query in st.chat_input. The query
   is appended to st.session_state.messages and displayed in the chat UI. The
   Streamlit backend calls the LlamaIndex RAG pipeline with the user's query.
   The RAG pipeline retrieves context, generates an answer using Gemini, and
   returns the response. The assistant's response is appended to
   st.session_state.messages and displayed in the chat UI. 7.2. Displaying
   Retrieved Information and SourcesTo enhance transparency and allow users to
   verify the LLM's responses: The LLM's final synthesized answer will be the
   primary output. An optional, expandable section (e.g., using st.expander)
   will display the key pieces of retrieved context that informed the LLM's
   answer. This can include:

Snippets of text chunks retrieved from Supabase. Relevant entity names,
relationships, or brief summaries retrieved from the Neo4j knowledge graph.
Source document identifiers, if available.

7.3. Interactive Graph Visualization OptionsFor queries where graph
relationships are particularly important, or for users who wish to explore the
knowledge graph more deeply, providing graph visualization capabilities is
valuable. Two main approaches are considered: embedding visualizations directly
within Streamlit using Python libraries, and leveraging dedicated Neo4j graph
visualization tools like Bloom.

Embedding with neo4j-viz:

The neo4j-viz Python package is designed for creating interactive graph
visualizations from Neo4j data and can render its output (IPython.display.HTML)
directly in Streamlit applications using st.components.v1.html.24 This library
wraps the Neo4j Visualization JavaScript library (NVL). Features: Supports
node/relationship sizing, colors, captions, pinning, tooltips, zooming, panning,
and various layouts.24 It can import graphs from Neo4j query results, GDS
projections, or Pandas DataFrames.24 Challenges:

neo4j-viz is still under development, and its API is subject to change, which
introduces a risk of instability or bugs.24 Handling dynamic updates to
visualizations in Streamlit can be complex. Typically, any change in user input
that triggers a plot regeneration causes the entire plot to redraw, potentially
resetting zoom and pan states.27 While Streamlit supports various charting
libraries 21, truly interactive and dynamically updating graph visualizations
might require careful state management or face limitations.

Alternatives like st.graphviz_chart or integrating with more mature
JavaScript-based graph visualization libraries via Streamlit Components could be
explored if neo4j-viz proves insufficient, though these may require more data
transformation or custom development.

Leveraging Neo4j Bloom:

What it is: Neo4j Bloom is a dedicated, no-code/low-code graph data
visualization and exploration tool provided by Neo4j. It allows both novices and
experts to visually explore and investigate Neo4j graph data without writing
Cypher for basic exploration. Key Features:

Intuitive Exploration: Point-and-click interface for graph exploration, pattern
searching, and expanding nodes. Perspectives: Users can create and save
"perspectives" which define how data (categories, relationships, formatting,
saved searches, scene actions) is displayed, allowing focus on specific aspects
of the graph. Customization: Extensive styling options for nodes and
relationships (colors, sizes, icons, captions). Advanced Search: Supports graph
pattern searches (visual query building), custom Cypher search phrases, and
full-text search. Data Editing: Allows visual editing of graph data. GDS
Integration: Can run Graph Data Science algorithms and visualize results.
Filtering and Animation: Features like the "Slicer" allow dynamic filtering and
animation based on properties (e.g., time). Scenes and Sharing: Users can create
and share specific views of the graph ("scenes") and use deep links to share
specific Bloom states.

Deployment: Bloom is available with Neo4j AuraDB instances (via the "Explore"
tab in the Aura console) and Neo4j Desktop. It can also be deployed with a Bloom
server plugin for on-premise Neo4j instances, enabling multi-user collaboration
and persistent storage of perspectives. Licensing: Bloom is included with Neo4j
AuraDB subscriptions and Neo4j Desktop. The neo4j-apps/neo4j-bloom GitHub
repository is licensed under Apache 2.0, but for this project, Bloom is
considered as the product feature provided with the Neo4j database. Integration
with Streamlit: Direct embedding of the full Bloom application within a
Streamlit page is not its standard use case. However, the Streamlit application
could:

Provide deep links to pre-configured Bloom perspectives or scenes relevant to
the RAG system's output or the user's query context. This would open Bloom in a
separate browser tab or its own interface. Be used as a complementary tool by
analysts or power users who need more sophisticated, interactive graph
exploration capabilities than what might be feasible to embed directly in
Streamlit.

Bloom vs. neo4j-viz:

neo4j-viz is a developer library for embedding specific, potentially
RAG-generated, subgraphs into a Python application like Streamlit.24 It requires
coding to define the visualization. Bloom is a full-fledged application for
end-users (especially data analysts) to explore the entire graph interactively
with a rich UI and no coding required for most operations. It offers a more
comprehensive exploration environment.

Recommendation for Visualization: For displaying specific, contextually relevant
subgraphs generated by the RAG pipeline directly within the Streamlit chat
interface, neo4j-viz (or a similar embeddable library) is the more appropriate
choice, despite its developmental status. This allows for in-app visualization
of the immediate evidence. For users requiring deeper, more flexible, and
code-free exploration of the entire knowledge graph, the Streamlit application
should provide links or guidance on how to use Neo4j Bloom with the project's
Neo4j AuraDB instance. This caters to different user needs without
overcomplicating the primary chat interface. 7.4. Key Code Examples: Streamlit
UI Setup and Backend Communication

Basic Streamlit chat structure: Python# Based on [19] import streamlit as st
import time

def call_rag_pipeline(user_query: str, chat_history: list): print(f"RAG Pipeline
received query: {user_query}") print(f"Current chat history length:
{len(chat_history)}") time.sleep(2) response_text = f"I'm processing your query
about: '{user_query}'. This is a placeholder response." sources = return
{"answer": response_text, "sources": sources}

st.title("Graph RAG System with Gemini & Neo4j")

if "messages" not in st.session_state: st.session_state.messages =

for message in st.session_state.messages: with st.chat_message(message["role"]):
st.markdown(message["content"]) if "sources" in message and message["sources"]:
with st.expander("View Sources"): for source in message["sources"]:
st.write(f"**Source Type:** {source.get('type', 'N/A')}") st.caption(f"Content:
{source.get('content', 'N/A')}")

if prompt := st.chat_input("Ask a question about your documents:"):
st.session_state.messages.append({"role": "user", "content": prompt}) with
st.chat_message("user"): st.markdown(prompt)

    with st.spinner("Thinking..."):
        rag_response_data = call_rag_pipeline(prompt, st.session_state.messages)
        assistant_response_text = rag_response_data.get("answer", "Sorry, I couldn't find an answer.")
        retrieved_sources = rag_response_data.get("sources",)

    assistant_message = {"role": "assistant", "content": assistant_response_text, "sources": retrieved_sources}
    st.session_state.messages.append(assistant_message)
    with st.chat_message("assistant"):
        st.markdown(assistant_response_text)
        if retrieved_sources:
            with st.expander("View Sources"):
                for source in retrieved_sources:
                    st.write(f"**Source Type:** {source.get('type', 'N/A')}")
                    st.caption(f"Content: {source.get('content', 'N/A')}")

Conceptual code for using neo4j-viz in Streamlit (as previously outlined):
Python# Based on [24]

# import streamlit as st

# from neo4j_viz import Node, Relationship, VisualizationGraph

# from IPython.display import HTML

# def get_graph_data_for_visualization(rag_context_from_neo4j):

# nodes_data =

# rels_data =

# # nodes_data.append(Node(id="entity1", caption="Entity One", size=10, color="blue"))

# # nodes_data.append(Node(id="entity2", caption="Entity Two", size=12, color="green"))

# # rels_data.append(Relationship(source="entity1", target="entity2", caption="CONNECTED_TO"))

# if not nodes_data:

# nodes_data =

# rels_data =

# return nodes_data, rels_data

# if st.button("Visualize Retrieved Graph Context (if any)"):

# neo4j_context = True

# if neo4j_context:

# nodes_to_viz, rels_to_viz = get_graph_data_for_visualization(None)

# if nodes_to_viz:

# try:

# graph_visualization = VisualizationGraph(

# nodes_to_viz,

# rels_to_viz,

# directed=True,

# )

# html_output = graph_visualization.render().data

# st.components.v1.html(html_output, height=600, scrolling=True)

# except Exception as e:

# st.error(f"Failed to render graph visualization: {e}")

# else:

# st.info("No specific graph elements were retrieved for visualization in this response.")

# else:

# st.info("No graph context available to visualize for the last query.")

Streamlit's rapid development cycle makes it suitable for quickly building a
functional UI. However, for advanced interactive visualizations like dynamic
graph updates, careful consideration of its limitations and the maturity of
chosen libraries like neo4j-viz is necessary. Complementing this with access to
a powerful tool like Neo4j Bloom for deeper analysis provides a balanced
approach.8. Google Cloud Platform (GCP) Integration and Deployment StrategyThe
system leverages several Google Cloud Platform services, primarily for hosting
the Neo4j AuraDB (which can run on GCP infrastructure), running the LLM and
embedding models via Vertex AI, and potentially deploying the application
components.8.1. Neo4j AuraDB on GCPThe project utilizes an existing Neo4j AuraDB
instance: neo4j+s://037bf8a4.databases.neo4j.io (User-provided image). Neo4j
AuraDB is a fully managed cloud graph database service that can be deployed on
GCP. Integration primarily involves ensuring network connectivity from
application components (e.g., graphitti server, LlamaIndex backend) running on
GCP to the AuraDB endpoint. Standard security practices, such as IP allowlisting
and secure credential management, should be followed.8.2. graphitti MCP Server
Deployment on GCPgraphitti includes a Model Context Protocol (MCP) server and a
REST API server built with FastAPI, which can be used for interacting with the
knowledge graph.1 The mcp_server can be deployed using Docker 1, making it
suitable for various GCP container services: Google Cloud Run: Ideal for
stateless, containerized applications. If the graphitti MCP server or REST API
can be run as stateless instances (with Neo4j AuraDB as the external stateful
backend), Cloud Run offers serverless deployment, auto-scaling, and pay-per-use
pricing. Google Kubernetes Engine (GKE): For more complex deployments or if
managing multiple graphitti instances (e.g., using the mcp-graphiti multi-server
pattern 28), GKE provides a robust orchestration platform. Docker Compose
configurations from mcp-graphiti can be adapted into Kubernetes manifests.
Google Compute Engine (GCE): Virtual machines on GCE offer maximum control but
require more manual setup and management. This approach might involve
configuring VPCs, DNS, Load Balancers, and Instance Groups, similar to deploying
other database or backend services on VMs.29 The mcp-graphiti repository 28
proposes a Docker Compose-based deployment for managing multiple graphitti MCP
server instances with a shared Neo4j database. This pattern, promoting project
isolation and easier management, is well-suited for translation to GKE
deployments or multiple Cloud Run services.8.3. Utilizing Other GCP Services
Vertex AI: This is a core component, used for accessing Google Gemini models for
generation (gemini-2.5-pro) and embedding (gemini-embedding-001 or
the specified gemini-2.5-flash if compatible) as defined in the
.env and system design. The GCP Project ID for these services is
neo4j-deployment-new1 (User-provided image). Google Drive API: Used by
LlamaIndex's GoogleDriveReader to access documents from the specified
DRIVE_FOLDER_ID. This requires enabling the Drive API in the GCP project
(neo4j-deployment-new1) and configuring appropriate authentication using the
service account key specified by SERVICE_ACCOUNT_KEY_PATH. Cloud Storage (GCS):
While the .env files mention a DRIVE_FOLDER_ID (implying Google Drive), for
production-grade document storage beyond initial ingestion or for other
artifacts, GCS is recommended. GCS buckets can store raw documents, serve as a
backup location for the Neo4j graph data (analogous to GraphDB backups to Cloud
Storage 29), or store other large artifacts. Identity and Access Management
(IAM): Essential for managing permissions for all GCP resources. Service
accounts with least-privilege access should be configured for the graphitti
server, the LlamaIndex backend application, and any components interacting with
Vertex AI or other GCP services. The IMPERSONATED_USER_EMAIL
(kevin@clearspringcg.com from user-provided image) indicates the use of service
account impersonation, a good practice for fine-grained access control, where
the service account (identified by its key file at SERVICE_ACCOUNT_KEY_PATH) is
granted authority to act on behalf of this user for accessing resources like
Google Drive. Cloud DNS and Load Balancing: If deploying graphitti services
(MCP, REST) or the Streamlit application backend on GCE/GKE for high
availability, custom domain mapping, or SSL termination, Cloud DNS and Cloud
Load Balancing would be necessary.29 Secret Manager: For securely storing
sensitive credentials like API keys, database passwords, and the content of the
service account key file (rather than just its path in .env for production), GCP
Secret Manager is highly recommended. While graphitti itself primarily
highlights OpenAI integration in its main documentation 1, the
graphiti-core[google-genai] package specifically enables Gemini support.1 Thus,
graphitti's primary GCP integration point is its use of Vertex AI for LLM and
embedding tasks. Further integrations, such as using Pub/Sub for event-driven
ingestion into graphitti or Dataflow for large-scale preprocessing, would be
custom application-level developments around graphitti rather than built-in
features.A security consideration from the user-provided images is the Neo4j
AuraDB username neo4j. While this is a common default, for production systems,
it is strongly recommended to use dedicated, non-personal service accounts or
roles with least privilege for database access to improve security and
manageability.9. Consolidated Technical SpecificationsThis section consolidates
key technical details, including environment configurations and data flow
diagrams, to provide a unified reference.9.1. Comprehensive Environment
Variables and ConfigurationThe system relies on numerous environment variables
for configuring access to various services. These are primarily sourced from the
.env files and images provided across conversation turns.Table 3: Consolidated
Environment VariablesVariable NameDescriptionSource (.env Image/User
Image)Example Value (Masked/Generic)SUPABASE_URLURL of the Supabase
project.Image 1 (initial
prompt)https://odpykcmtcwmyfolsrgcu.supabase.coSUPABASE_KEYService role key for
Supabase API access.Image 1 (initial
prompt)eyJh...XVCJ9.eyJp...ImNnIl0.ey...Y3MSUPABASE_PROJECT_IDUnique identifier
for the Supabase project.Image 1 (initial
prompt)odpykcmtcwmyfolsrgcuSUPABASE_DATABASE_PASSWORDPassword for the Supabase
PostgreSQL database.Image 1 (initial
prompt)HlabaysirdtgycuSUPABASE_DATABASE_NAMEName of the Supabase PostgreSQL
database.Image 1 (initial prompt)postgresNEO4J_URIConnection URI for Neo4j
AuraDB.User-provided image (previous
turn)neo4j+s://037bf8a4.databases.neo4j.ioNEO4J_USERUsername for Neo4j
AuraDB.User-provided image (previous turn)neo4jNEO4J_PASSWORDPassword for Neo4j
AuraDB.User-provided image (previous
turn)o1ocsUT2c2Ye-3B2nkMHwppzYeK6Z3YBIxVM2LwZgkNEO4J_DATABASEName of the Neo4j
database.User-provided image (previous turn)neo4jAURA_INSTANCEIDInstance ID for
Neo4j AuraDB.User-provided image (previous
turn)037bf8a4AURA_INSTANCENAMEInstance Name for Neo4j AuraDB.User-provided image
(previous turn)Instance01GCP_PROJECT_IDGoogle Cloud Project ID for Vertex AI and
other GCP services.User-provided image (previous
turn)neo4j-deployment-new1GCP_LOCATIONGoogle Cloud region/location for Vertex AI
services.Image 1 (initial prompt) / Image 1 (user's previous
turn)us-central1EMBED_MODEL_LLMIdentifier for the embedding model (Gemini on
Vertex AI).Image 1 (initial
prompt)models/gemini-2.5-flashFALLBACK_LLM_MODELIdentifier for the
fallback LLM (Gemini on Vertex AI).Image 1 (initial
prompt)gemini-2.5-flashLLM_MODELIdentifier for the primary LLM
(Gemini on Vertex AI).Image 1 (initial
prompt)gemini-2.5-proANTHROPIC_API_KEYAPI Key for Anthropic models
(Optional, if used).Image 1 (initial prompt) / Image 2 (initial
prompt)sk-ant-api03-...YiwAAPERPLEXITY_API_KEYAPI Key for Perplexity models
(Optional, if used).Image 1 (initial prompt) / Image 2 (initial
prompt)pplx-...N3H4OPENAI_API_KEYAPI Key for OpenAI models (Optional, if used as
alternative/fallback).Image 1 (initial prompt) / Image 2 (initial
prompt)sk-proj-...GR2LKAGOOGLE_API_KEYGeneral Google API Key (may be used by
clients if ADC not primary).Image 1 (initial prompt) / Image 2 (initial
prompt)AIzaSyC...gNUKGOOGLE_CLOUD_PROJECTGoogle Cloud Project ID (alternative
name for GCP_PROJECT_ID).User-provided image (previous
turn)neo4j-deployment-new1GOOGLE_CLOUD_LOCATIONGoogle Cloud region/location
(alternative name for GCP_LOCATION).Image 1 (user's previous
turn)us-central1DRIVE_FOLDER_IDGoogle Drive Folder ID for input documents.Image
1 (initial prompt) / Image 2 (initial prompt) / User-provided image (previous
turn)1vbJ-5VnV_gTlegoW0bO0A26gR7rwJDajmIMPERSONATED_USER_EMAILEmail for service
account impersonation on GCP for Drive access.Image 1 (initial prompt) / Image 2
(initial prompt) / User-provided image (previous
turn)kevin@clearspringcg.comSERVICE_ACCOUNT_KEY_PATHFilesystem path to the GCP
service account JSON key file for Drive access.User-provided image (current
turn)C:\Users\kevin\repos\kev-graph-rag\src\service_account_key.jsonLLAMA_CLOUD_API_KEYAPI
Key for LlamaCloud (Optional, if LlamaParse or other services used).Image 2
(initial prompt)llx-YenT...BcDyLA consolidated and centrally managed approach to
these configurations, potentially using GCP Secret Manager for production
secrets, is crucial for system stability and security.9.2. Data Flow
DiagramsDiagram 2: Data Ingestion Flow (Source Documents -> graphitti -> Neo4j
AuraDB)Code snippetgraph LR A --> LDA(LlamaIndex GoogleDriveReader); B -->
LDI(LlamaIndex DirectoryReader); LDA -- LlamaIndex Documents --> P{Document
Preprocessing}; LDI -- LlamaIndex Documents --> P; P -- Processed Text/Data -->
C{graphitti Core Engine}; C -- Uses --> D[Gemini LLM via Vertex AI for
Extraction]; C -- Uses --> E[Gemini Embedding Model via Vertex AI]; D --
Extracted Entities/Relationships --> C; E -- Embeddings --> C; C -- Formatted
Graph Data (Nodes, Edges with Temporal Info & Embeddings) --> F; This diagram
illustrates how documents from sources like Google Drive are loaded by
LlamaIndex, then processed by graphitti leveraging Gemini models for
entity/relationship extraction and embedding, and finally populating the Neo4j
AuraDB knowledge graph with temporally-aware data.Diagram 3: Query Flow (User
via Streamlit -> LlamaIndex Orchestrator -> Hybrid Retrievers -> LLM ->
Streamlit)Code snippetgraph TD U[User] -- Query --> SO{Streamlit Backend}; SO --
Processed Query --> LO{LlamaIndex Orchestrator}; LO -- Graph Retrieval Request
--> NR; NR -- Cypher/Keyword/Vector Query --> NDB; NDB -- Graph Context
(Entities, Relations, Text) --> NR; NR -- Retrieved Graph Context --> LO; LO --
Vector Retrieval Request --> SR; SR -- Vector Query --> SDB; SDB -- Document
Chunks --> SR; SR -- Retrieved Vector Context --> LO; LO -- Combined Context +
Prompt --> LLM[Gemini LLM via Vertex AI]; LLM -- Generated Answer --> LO; LO --
Final Response + Sources --> SO; SO -- Display Answer & Sources --> U; This
diagram shows the path of a user query from the Streamlit interface, through
LlamaIndex which orchestrates hybrid retrieval from Neo4j and Supabase, to the
Gemini LLM for answer synthesis, and back to the user.9.3. API Endpoint
DefinitionsInternal APIs will exist between components: Streamlit Backend to
LlamaIndex Orchestrator: A Python API call to trigger the RAG pipeline.
LlamaIndex to Neo4j/Supabase: Handled by LlamaIndex data connectors using
database drivers/APIs. LlamaIndex to Vertex AI: HTTPS API calls to Vertex AI
endpoints for Gemini models. LlamaIndex to Google Drive API: HTTPS API calls
managed by the GoogleDriveReader. graphitti to Neo4j: graphitti uses the Neo4j
Python driver. graphitti to Vertex AI: HTTPS API calls for its internal
LLM/embedding needs. If the graphitti REST service or MCP server is deployed and
exposed, its API endpoints (e.g., for adding episodes, querying graph elements)
would be defined by graphitti's FastAPI application or MCP specification.1 For
this project, direct interaction with graphitti's servers by the user-facing
application is less likely; LlamaIndex will be the primary interface to the data
stores populated by graphitti.10. Future Considerations and EnhancementsWhile
the current PRD outlines a comprehensive Graph RAG system, several areas offer
potential for future enhancements and require ongoing attention.10.1.
Scalability, Performance Optimization, and Cost Management Scalability:

Neo4j AuraDB: Monitor performance and scale the AuraDB instance tier as data
volume and query complexity grow. AuraDB offers different tiers to accommodate
varying workloads. Supabase: Monitor PostgreSQL performance and consider scaling
options if the vector store becomes a bottleneck. GCP Services: Cloud Run and
GKE offer auto-scaling for stateless application components. Vertex AI endpoints
for Gemini models are managed services designed for scalability.

Performance Optimization:

graphitti Ingestion: Optimize batch sizes and LLM calls during graphitti's data
ingestion process. graphitti is designed for scalability with large datasets and
parallelizing LLM calls.1 LlamaIndex Pipelines: Profile and optimize LlamaIndex
retrieval and synthesis pipelines. This includes tuning retriever parameters
(e.g., similarity_top_k), prompt engineering, and response synthesizer choices.
Query Optimization: For Neo4j, ensure appropriate indexes are in place (beyond
what graphitti creates, if needed) and optimize Cypher queries generated by
TextToCypher or custom logic. Caching: Implement caching at various levels
(e.g., retrieved context, LLM responses for common queries, embedding results)
to reduce latency and cost.

Cost Management:

LLM Calls: Monitor token usage for Gemini models (extraction, embedding,
synthesis, agentic reasoning if implemented). Employ strategies like using
smaller/faster models (e.g., Flash versions) for less critical tasks, prompt
optimization to reduce token count, and response length limits. GCP Resource
Utilization: Regularly review GCP costs for AuraDB, Supabase (if hosted on GCP),
Vertex AI, GCS, and compute services. Utilize GCP's cost management tools.

The performance of graphitti's ingestion and LlamaIndex's retrieval from Neo4j
will be critical as the knowledge graph expands. While graphitti's hybrid
indexing aims for efficient access 1, large and complex graphs can still present
challenges for specific query patterns. Continuous performance monitoring and
optimization will be essential.10.2. System Evaluation and Monitoring Frameworks
RAG Quality Evaluation:

Implement metrics to assess the quality of the RAG system, such as:

Answer Relevance: How well the generated answer addresses the user's query.
Faithfulness/Attribution: Whether the answer is grounded in the retrieved
context and avoids hallucination. Context Recall/Precision: How effectively the
retrieval system fetches relevant context and avoids irrelevant information.

LlamaIndex provides evaluation modules that can be adapted for these purposes.9
Frameworks like RAGAs or custom evaluation suites can also be used.

System Monitoring:

Utilize GCP's Cloud Monitoring for system health, API latencies, error rates,
and resource utilization of components deployed on GCP. Monitor Neo4j AuraDB and
Supabase performance through their respective dashboards and logging. Log key
interactions and decisions within the LlamaIndex pipeline for debugging and
analysis.

10.3. Advanced graphitti Feature Explorationgraphitti offers several advanced
capabilities that could be explored in future iterations: Deeper Temporal
Queries: Leverage graphitti's bi-temporal model to answer historical questions,
analyze trends over time, or reconstruct the state of knowledge at specific
points in time.1 This is a core differentiator and could unlock significant
value beyond basic RAG. Community Detection: graphitti has capabilities related
to community detection within the graph. Exploring how these communities could
inform retrieval or provide higher-level insights might be beneficial. Custom
Graph Schemas: While graphitti can work with Pydantic models for custom
entities, further exploration of its support for more complex, developer-defined
node and edge classes could allow for even more tailored knowledge
representation.1 Conflict Resolution: Investigate graphitti's mechanisms for
handling conflicting information when ingesting new data, particularly how it
uses temporal metadata to update or invalidate outdated facts.4 10.4. Enhanced
Agentic CapabilitiesIf the initial RAG system proves successful, revisiting
Agentic RAG (as discussed in Section 6) with a focus on specific improvements:
Dynamic Tool Selection: Agents that can choose between graph queries, vector
searches, or even external APIs based on query analysis. Multi-Hop Reasoning:
Agents capable of performing sequences of queries (e.g., traversing multiple
relationships in the graph) to answer complex questions.
Self-Correction/Refinement: Agents that can evaluate the results of a retrieval
step and decide to retry with a modified query or strategy if the initial
context is insufficient. 11. ConclusionThis Product Requirements Document
details the technical design for a sophisticated Graph RAG system. By
integrating graphitti-core for dynamic knowledge graph creation in Neo4j AuraDB,
leveraging LlamaIndex for document loading (including from Google Drive
authenticated via a service account key) and hybrid retrieval from the graph and
a Supabase vector store, and utilizing Google's Gemini models via Vertex AI, the
system aims to provide accurate, context-aware answers through a Streamlit-based
chat interface.The emphasis on graphitti's temporal capabilities and custom
entity definitions provides a strong foundation for a KG that evolves with new
information. The hybrid retrieval strategy ensures that both structured,
interconnected knowledge and broad semantic context can be utilized. The
Streamlit UI will provide core chat functionality, with options for embedded
graph visualizations using libraries like neo4j-viz for immediate context, and
guidance for using powerful external tools like Neo4j Bloom for deeper,
code-free graph exploration by analysts. While Agentic RAG presents an avenue
for future enhancement, the initial focus will be on establishing a robust and
performant core RAG pipeline.Successful implementation will depend on careful
attention to model configuration (particularly embedding model alignment),
efficient data ingestion (including secure and reliable access to Google Drive
using the specified service account key path), robust retrieval strategies, and
sound GCP deployment using the confirmed neo4j-deployment-new1 project and
updated Neo4j credentials. The provided technical specifications and code
examples offer a starting point for development, with ongoing evaluation and
iteration being key to achieving the project's goals.
