# src/backend/routers/graph.py
# FastAPI router for graph-related endpoints, using Graphiti-native search.

from fastapi import APIRouter, HTTPException
from src.graph_querying.graphiti_native_search import GraphitiNativeSearcher

router = APIRouter()

@router.get("/graph/full_graph")
async def get_full_graph():
    """
    Fetches a sample of the graph using Graphiti's native search capabilities.
    This is more scalable and aligned with the project architecture than raw Cypher.
    """
    try:
        async with GraphitiNativeSearcher() as searcher:
            # Use a generic query to fetch a representative sample of the graph.
            # The advanced_search_with_recipe returns both nodes and edges.
            graph_data = await searcher.advanced_search_with_recipe(
                query="*",  # A generic query to get a broad set of results
                recipe_name="combined_hybrid",
                num_results=25  # Limit results for performance and clarity
            )

            # The frontend expects a specific format for nodes and edges.
            # We need to transform the data from GraphitiNativeSearcher.
            formatted_nodes = [
                {"id": node['uuid'], "label": node.get('name', node['uuid'])}
                for node in graph_data.get('nodes', [])
            ]
            
            formatted_edges = [
                {"source": edge['source_node_uuid'], "target": edge['target_node_uuid'], "label": edge.get('fact', '')}
                for edge in graph_data.get('edges', [])
            ]

            return {"nodes": formatted_nodes, "edges": formatted_edges}

    except Exception as e:
        # In a real app, log the exception details for debugging.
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while fetching the graph: {e}")
