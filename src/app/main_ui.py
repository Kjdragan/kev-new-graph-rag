# src/app/main_ui.py
import streamlit as st
import requests
import os

from src.app.components.graph_viz import display_graph

# Get backend URL from environment variable or use a default
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8001/api/v2")

def get_chat_response(prompt: str) -> str:
    """Sends prompt to backend and gets a response."""
    try:
        response = requests.post(f"{BACKEND_URL}/chat/invoke", json={"input": prompt})
        response.raise_for_status()  # Raise an exception for bad status codes
        return response.json().get("output", "Sorry, I couldn't get a response.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to backend: {e}")
        return "Error: Could not connect to the backend."

# --- UI Layout ---

st.set_page_config(layout="wide")
st.title("🧠 Hybrid RAG System: Chat & Knowledge Graph")

# Ingestion Expander
with st.expander("📁 Ingest New Documents"):
    uploaded_file = st.file_uploader("Choose a document to ingest", type=['txt', 'md', 'pdf'])
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
                    
                    # Refresh the page to reflect changes (e.g., in the graph)
                    st.rerun()

                except requests.exceptions.RequestException as e:
                    st.error(f"Error during ingestion: {e}")
                    # Try to get more details from response if available
                    try:
                        error_detail = e.response.json().get("detail", e.response.text)
                        st.error(f"Server error: {error_detail}")
                    except:
                        pass


# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Define columns for chat and graph visualization
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Chat with your Knowledge")
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Accept user input
    if prompt := st.chat_input("Ask a question about your documents..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)

        # Display assistant response in chat message container
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response_text = get_chat_response(prompt)
                st.markdown(response_text)
        # Add assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response_text})

with col2:
    st.header("Knowledge Graph Visualization")
    display_graph()

BACKEND_API_URL = "http://localhost:8001/api/v2/chat"

st.set_page_config(layout="wide", page_title="Kev's Hybrid RAG System")

def main():
    st.title("Hybrid RAG System")

    # Create a two-column layout
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Chat Interface")
        # Initialize chat history in session state if it doesn't exist
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages from history on app rerun
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Accept user input
        if user_query := st.chat_input("Ask me anything about your documents..."):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": user_query})
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(user_query)

            # Display assistant response in chat message container
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        # Call the backend API
                        response = requests.post(BACKEND_API_URL, json={"query": user_query})
                        response.raise_for_status()  # Raise an exception for bad status codes
                        
                        api_response = response.json()
                        assistant_response = api_response.get("response", "Sorry, something went wrong with the API response.")
                        
                    except requests.exceptions.RequestException as e:
                        assistant_response = f"Error: Could not connect to the backend. Please ensure it is running. Details: {e}"

                st.markdown(assistant_response)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_response})

    with col2:
        st.subheader("Knowledge Graph Visualization")
        # Display the sample graph
        display_live_graph()

if __name__ == "__main__":
    main()
