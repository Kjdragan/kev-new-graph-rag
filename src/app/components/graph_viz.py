# src/app/components/graph_viz.py
# Component for Neo4j graph visualization using streamlit-agraph

import streamlit as st
import requests
from streamlit_agraph import agraph, Node, Edge, Config

# Configuration for the backend API
BACKEND_GRAPH_API_URL = "http://localhost:8001/api/v2/graph/full_graph"

def display_live_graph():
    """Fetches graph data from the backend and displays it."""
    with st.spinner("Loading Knowledge Graph..."):
        try:
            response = requests.get(BACKEND_GRAPH_API_URL)
            response.raise_for_status()
            graph_data = response.json()
            
            nodes_data = graph_data.get("nodes", [])
            edges_data = graph_data.get("edges", [])

            if not nodes_data:
                st.warning("No data found in the knowledge graph.")
                return

            # Create Node and Edge objects for agraph
            nodes = [Node(id=n['id'], label=n.get('label', n['id']), size=25) for n in nodes_data]
            edges = [Edge(source=e['source'], target=e['target'], label=e.get('label', '')) for e in edges_data]

            # Configuration for the graph visualization
            config = Config(width=750,
                            height=600,
                            directed=True,
                            physics=True,
                            hierarchical=False,
                            # **Improved Features**
                            nodeHighlightBehavior=True, 
                            highlightColor="#F7A7A6",
                            collapsible=True,
                            node={'labelProperty':'label'},
                            link={'labelProperty': 'label', 'renderLabel': True}
                            )

            agraph(nodes=nodes, edges=edges, config=config)

        except requests.exceptions.RequestException as e:
            st.error(f"Error: Could not connect to the backend to fetch graph data. Please ensure it is running. Details: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred while rendering the graph: {e}")


