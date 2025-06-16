# src/app/main_ui.py
import sys
import os

# Add the project root to the Python path to resolve 'src' module imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import streamlit as st
import requests
import os

import logging
from src.app.components.graph_viz import display_pyvis_graph

# --- Logging Configuration ---
log_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file_path = os.path.join(log_dir, 'frontend.log')

# Use a basicConfig to set up the root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler(sys.stdout)  # Also log to console
    ]
)

logger = logging.getLogger(__name__)
logger.info("Frontend UI logging configured.")
# --- End Logging Configuration ---

# Get backend URL from environment variable or use a default
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001/api/v2")

def get_chat_response(prompt: str) -> dict:
    """Sends prompt to backend and gets a structured response."""
    try:
        response = requests.post(f"{BACKEND_URL}/chat", json={"query": prompt})
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error connecting to backend for chat: {e}", exc_info=True)
        st.error(f"Error connecting to backend: {e}")
        return {}


# --- UI Layout ---

st.set_page_config(layout="wide")
st.title("🧠 Hybrid RAG System: Chat & Knowledge Graph")

# Ingestion Expander
with st.expander("📁 Ingest New Documents"):
    # Initialize the key for the file_uploader if it doesn't exist
    if 'uploaded_file_key' not in st.session_state:
        st.session_state['uploaded_file_key'] = '0'
    # Use the key for the file_uploader
    uploaded_file = st.file_uploader("Choose a document to ingest", type=['txt', 'md', 'pdf'], key=st.session_state['uploaded_file_key'])
    if uploaded_file is not None:
        if st.button(f"Ingest {uploaded_file.name}"):
            files = {'file': (uploaded_file.name, uploaded_file, uploaded_file.type)}
            with st.spinner(f"Ingesting {uploaded_file.name}..."):
                try:
                    ingest_url = f"{BACKEND_URL}/ingest/document"
                    response = requests.post(ingest_url, files=files)
                    response.raise_for_status()
                    
                    st.success(f"Successfully ingested {uploaded_file.name}!")
                    st.info(f"Response from server: {response.json().get('message')}")
                    
                    # Clear the file uploader by re-assigning and rerunning
                    # Note: Streamlit's file_uploader state management can be tricky.
                    # If this doesn't work as expected, we might need to use a session_state key.
                    uploaded_file = None 
                    st.session_state['uploaded_file_key'] = str(int(st.session_state.get('uploaded_file_key', 0)) + 1) # Force re-render by changing key
                    st.rerun()

                except requests.exceptions.RequestException as e:
                    logger.error(f"Error during document ingestion request: {e}", exc_info=True)
                    st.error(f"Error during ingestion: {e}")
                    # Try to get more details from response if available
                    try:
                        error_detail = e.response.json().get("detail", e.response.text)
                        st.error(f"Server error: {error_detail}")
                    except:
                        pass

    st.markdown("---") # Separator

    st.subheader("Ingest from Google Drive")
    # Use session state for the folder ID to allow resetting
    if 'gdrive_folder_id' not in st.session_state:
        st.session_state['gdrive_folder_id'] = ''
    gdrive_folder_id = st.text_input("Google Drive Folder ID", value=st.session_state['gdrive_folder_id'], key='gdrive_folder_id_input')
    if gdrive_folder_id:
        if st.button("Ingest from Google Drive"):
            with st.spinner(f"Ingesting from Google Drive folder: {gdrive_folder_id}..."):
                try:
                    ingest_gdrive_url = f"{BACKEND_URL}/ingest/gdrive"
                    response = requests.post(ingest_gdrive_url, json={"folder_id": gdrive_folder_id})
                    response.raise_for_status()

                    # Show clear success notification with details
                    server_message = response.json().get('message')
                    files_processed = response.json().get('files_processed', 'N/A')
                    total_nodes = response.json().get('total_nodes_ingested', 'N/A')
                    total_edges = response.json().get('total_edges_ingested', 'N/A')
                    st.success(f"Google Drive ingestion complete! {server_message}")
                    st.info(f"Files processed: {files_processed} | Nodes ingested: {total_nodes} | Edges ingested: {total_edges}")

                    # Reset the folder ID input for a cleaner UX
                    st.session_state['gdrive_folder_id'] = ''
                    st.rerun()

                except requests.exceptions.RequestException as e:
                    logger.error(f"Error during GDrive ingestion request: {e}", exc_info=True)
                    logger.error(f"Request exception details: {e.request.url} {e.request.method} {e.request.body} {e.request.headers}")
                    st.error(f"Error during GDrive ingestion: {e}")
                    try:
                        error_detail = e.response.json().get("detail", e.response.text)
                        st.error(f"Server error: {error_detail}")
                    except:
                        pass

    st.markdown("---") # Separator

    st.subheader("Ingest from YouTube")
    # Use session state for the YouTube URL to allow resetting
    if 'youtube_url' not in st.session_state:
        st.session_state['youtube_url'] = ''
    youtube_url = st.text_input("YouTube Video URL", value=st.session_state['youtube_url'], key='youtube_url_input')
    if youtube_url:
        if st.button("Ingest Transcript from YouTube"):
            with st.spinner(f"Ingesting transcript from YouTube..."):
                try:
                    ingest_youtube_url = f"{BACKEND_URL}/ingest/youtube"
                    response = requests.post(ingest_youtube_url, json={"youtube_url": youtube_url})
                    response.raise_for_status()

                    # Show clear success notification with details from the summary
                    summary = response.json().get('summary', {})
                    st.success(f"YouTube transcript ingestion complete!")
                    st.info(
                        f"Chunks Created: {summary.get('total_chunks_created', 'N/A')} | "
                        f"Chroma Docs: {summary.get('ingested_chroma_count', 'N/A')} | "
                        f"Neo4j Nodes: {summary.get('ingested_neo4j_nodes', 'N/A')} | "
                        f"Neo4j Edges: {summary.get('ingested_neo4j_edges', 'N/A')}"
                    )

                    # Reset the URL input for a cleaner UX
                    st.session_state['youtube_url'] = ''
                    st.rerun()

                except requests.exceptions.RequestException as e:
                    logger.error(f"Error during YouTube ingestion request: {e}", exc_info=True)
                    st.error(f"Error during YouTube ingestion: {e}")
                    try:
                        error_detail = e.response.json().get("detail", e.response.text)
                        st.error(f"Server error: {error_detail}")
                    except:
                        pass

# --- Chat and Results --- #

# Initialize chat history and search results
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_query_results" not in st.session_state:
    st.session_state.last_query_results = None

# Display chat messages from history
st.header("Chat with your Knowledge")
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Ask a question about your documents..."):
    # Add user message to history and display it
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Get response from backend
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            results = get_chat_response(prompt)
            st.session_state.last_query_results = results
            
            chroma_results = results.get('chroma_context', {})
            graph_results = results.get('graph_context', {})
            num_docs = len(chroma_results.get('documents', [[]])[0])
            num_nodes = graph_results.get('num_nodes', 0)

            response_text = f"I found {num_docs} relevant documents from the vector store and {num_nodes} related entities in the knowledge graph. See the tabs below for details."
            st.markdown(response_text)
    
    # Add assistant summary to history
    st.session_state.messages.append({"role": "assistant", "content": response_text})

# --- Results Visualization --- #

if st.session_state.last_query_results:
    results = st.session_state.last_query_results
    chroma_context = results.get('chroma_context', {})
    graph_context = results.get('graph_context', {})

    tab1, tab2 = st.tabs(["Vector Store Context (ChromaDB)", "Knowledge Graph Context (Neo4j)"])

    with tab1:
        st.subheader("Top Retrieved Documents from ChromaDB")
        docs = chroma_context.get('documents', [[]])[0]
        metadatas = chroma_context.get('metadatas', [[]])[0]
        distances = chroma_context.get('distances', [[]])[0]

        if docs:
            for i, (doc, meta, dist) in enumerate(zip(docs, metadatas, distances)):
                with st.expander(f"Result {i+1} | Distance: {dist:.4f} | Source: {meta.get('source_document_id', 'N/A')}"):
                    st.text_area("Content", value=doc, height=200, disabled=True, key=f"chroma_doc_{i}")
                    st.json(meta) # Display all metadata
        else:
            st.info("No documents were retrieved from the vector store for this query.")

    with tab2:
        st.subheader("Query-Specific Knowledge Graph")
        if graph_context and graph_context.get('nodes'):
            display_pyvis_graph(graph_context)
        else:
            st.info("No graph context was found for this query.")
