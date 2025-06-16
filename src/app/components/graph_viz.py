# src/app/components/graph_viz.py
# Component for Neo4j graph visualization using streamlit-agraph

import streamlit as st
from streamlit_agraph import agraph, Node, Edge, Config

def display_pyvis_graph(graph_data: dict):
    """Renders a graph from a dictionary of nodes and edges."""
    try:
        nodes_data = graph_data.get("nodes", [])
        edges_data = graph_data.get("edges", [])

        if not nodes_data:
            st.warning("No graph data to display for this query.")
            return

        # Create Node and Edge objects for agraph
        # Ensure node 'id' is a string, as required by some versions of agraph
        nodes = [Node(id=str(n['id']), label=n.get('label', n['id']), size=25) for n in nodes_data]
        
        # The backend returns edge keys like 'source_node_uuid' and 'target_node_uuid'
        edges = [Edge(source=str(e['source_node_uuid']), 
                      target=str(e['target_node_uuid']), 
                      label=e.get('label', '')) for e in edges_data]

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

    except Exception as e:
        st.error(f"An unexpected error occurred while rendering the graph: {e}")


