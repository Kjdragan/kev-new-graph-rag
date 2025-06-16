import streamlit as st

st.set_page_config(layout="wide", page_title="Kev's Hybrid RAG System")

def main():
    st.title("Hybrid RAG System Chat Interface")

    # Placeholder for chat input
    user_query = st.chat_input("Ask me anything about your documents...")

    if user_query:
        st.write(f"You asked: {user_query}")
        # Here we will eventually call the backend API
        # For now, just a placeholder response
        with st.chat_message("assistant"):
            st.write(f"Echo: {user_query}")

if __name__ == "__main__":
    main()
