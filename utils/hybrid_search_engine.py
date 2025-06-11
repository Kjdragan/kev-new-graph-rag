"""
HybridSearchEngine Module

This module implements a hybrid search approach that combines knowledge graph traversal
with vector similarity search for enhanced RAG capabilities. It uses:
- Neo4j for graph database operations
- Google Gemini Pro for entity extraction and response synthesis
- Vector embeddings for similarity search

The engine provides robust query capabilities with fallback mechanisms and
comprehensive error handling.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import traceback

# Add the parent directory to sys.path to enable imports from project modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Import required modules
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from neo4j import Driver, GraphDatabase
from google.generativeai import GenerativeModel

# Import utils for configuration
from utils.config import get_config


@dataclass
class SearchResponse:
    """Class representing a search response with metadata"""
    answer: str
    graph_results: List[Dict[str, Any]]
    vector_results: List[Dict[str, Any]]
    query: str
    sources: List[Dict[str, Any]]
    error: Optional[str] = None


class HybridSearchEngine:
    """
    HybridSearchEngine combines knowledge graph querying with vector similarity search
    to provide comprehensive RAG capabilities.
    
    This engine:
    1. Extracts entities and relationships from user queries using Gemini function calling
    2. Queries Neo4j knowledge graph using structured information
    3. Falls back to vector similarity search when needed
    4. Synthesizes responses using all available information
    """
    
    def __init__(
        self,
        neo4j_driver: Driver,
        embedding_model: Any,
        llm: GenerativeModel,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the HybridSearchEngine.
        
        Args:
            neo4j_driver: Neo4j driver instance
            embedding_model: Model used for generating vector embeddings
            llm: Gemini Pro model for entity extraction and response synthesis
            config: Configuration parameters
        """
        self.neo4j_driver = neo4j_driver
        self.embedding_model = embedding_model
        self.llm = llm
        
        # Load config or use default values
        self.config = config or {}
        self.thinking_budget = self.config.get("thinking_budget", 1024)
        self.vector_top_k = self.config.get("vector_top_k", 3)
        self.similarity_threshold = self.config.get("similarity_threshold", 0.6)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
    
    def query(self, query_text: str) -> Union[SearchResponse, str]:
        """
        Process a user query through the hybrid search pipeline.
        
        Args:
            query_text: The natural language query from the user
            
        Returns:
            Either a SearchResponse object with full metadata or a string answer
        """
        self.logger.info(f"Processing query: {query_text}")
        graph_results = []
        vector_results = []
        error = None
        
        # 1. Try graph-based approach with entity extraction
        try:
            # Extract entities and relationships
            structured_info = self._extract_query_structure(query_text)
            self.logger.info(f"Extracted structure: {structured_info}")
            
            # Query the knowledge graph
            if structured_info and structured_info.get("entities"):
                graph_results = self._query_knowledge_graph(structured_info)
                self.logger.info(f"Graph search returned {len(graph_results)} results")
        except Exception as e:
            error = str(e)
            self.logger.error(f"Error in graph-based search: {e}")
            self.logger.debug(traceback.format_exc())
        
        # 2. Always perform vector search (as backup or complement)
        try:
            vector_results = self._vector_search(query_text)
            self.logger.info(f"Vector search returned {len(vector_results)} results")
        except Exception as e:
            if not graph_results:  # Only log as error if we have no graph results
                error = f"{error}; Vector search error: {str(e)}" if error else str(e)
                self.logger.error(f"Error in vector search: {e}")
                self.logger.debug(traceback.format_exc())
            else:
                self.logger.warning(f"Vector search failed but graph results available: {e}")
        
        # 3. Synthesize response using all available information
        answer = self._synthesize_response(query_text, graph_results, vector_results)
        
        # 4. Create sources list for citation
        sources = self._extract_sources(graph_results, vector_results)
        
        # Create and return search response
        response = SearchResponse(
            answer=answer,
            query=query_text,
            graph_results=graph_results,
            vector_results=vector_results,
            sources=sources,
            error=error
        )
        
        return response
    
    def _extract_query_structure(self, query_text: str) -> Dict[str, Any]:
        """
        Extract entities and relationships from the query using Gemini function calling.
        
        Args:
            query_text: The natural language query
            
        Returns:
            Dictionary with entities and relationships
        """
        # Define schema for structured extraction
        schema = {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "description": "List of entities extracted from the query",
                    "items": {
                        "type": "object",
                        "properties": {
                            "entity": {
                                "type": "string",
                                "description": "The entity name (person, organization, concept, etc.)"
                            },
                            "type": {
                                "type": "string",
                                "description": "The entity type (e.g. Person, Organization, Location, Concept)"
                            }
                        },
                        "required": ["entity"]
                    }
                },
                "relationships": {
                    "type": "array",
                    "description": "List of potential relationships between entities (e.g. 'employment', 'located_in')",
                    "items": {"type": "string"}
                }
            },
            "required": ["entities"]
        }
        
        # System prompt for entity extraction
        system_prompt = f"""
        Extract the key entities and their potential relationships from the following query.
        Only extract actual entities, not general concepts or verbs unless they're specifically
        being asked about as a concept. For relationships, identify the type of connection
        the user is asking about between entities (e.g., employment, location, creation, etc.)
        
        Think carefully about what entities would need to be queried in a knowledge graph.
        
        Thinking budget: {self.thinking_budget} tokens
        """
        
        # Use Gemini function calling with the correct format
        # For Gemini, we combine system and user prompts
        combined_prompt = f"{system_prompt}\n\nQuery: {query_text}"
        
        response = self.llm.generate_content(
            combined_prompt,
            generation_config={"response_schema": schema}
            # tools=self.tools  # Temporarily commented out to isolate TypeError
        )
        
        # Extract the structured information from function call
        try:
            if hasattr(response, "candidates") and response.candidates:
                # Check if we have a function call
                if hasattr(response.candidates[0].content, "function_call"):
                    function_args = response.candidates[0].content.function_call.args
                    return {
                        "entities": function_args.get("entities", []),
                        "relationships": function_args.get("relationships", [])
                    }
                # Check for parts with text
                elif hasattr(response.candidates[0].content, "parts"):
                    parts = response.candidates[0].content.parts
                    if parts and hasattr(parts[0], "text"):
                        # Try to parse JSON from text
                        try:
                            result = json.loads(parts[0].text)
                            return {
                                "entities": result.get("entities", []),
                                "relationships": result.get("relationships", [])
                            }
                        except json.JSONDecodeError:
                            self.logger.warning("Failed to parse response parts as JSON")
            
            # Fallback to response.text if available
            if hasattr(response, "text") and response.text:
                try:
                    result = json.loads(response.text)
                    return {
                        "entities": result.get("entities", []),
                        "relationships": result.get("relationships", [])
                    }
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse response text as JSON")
            
            # Fallback for older API versions or unexpected structure
            self.logger.warning("Could not extract structured information from response")
            return {"entities": [], "relationships": []}
        except Exception as e:
            self.logger.error(f"Error extracting structured information: {e}")
            return {"entities": [], "relationships": []}
    
    def _query_knowledge_graph(self, structured_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query the Neo4j knowledge graph using the structured information.
        
        Args:
            structured_info: Dictionary with entities and relationships
            
        Returns:
            List of graph query results
        """
        entities = structured_info.get("entities", [])
        relationships = structured_info.get("relationships", [])
        
        if not entities:
            return []
        
        # Build Cypher query based on extracted entities and relationships
        entity_conditions = []
        for entity in entities:
            entity_name = entity.get("entity", "").replace("'", "\\'")  # Escape quotes
            entity_type = entity.get("type", "")
            
            # Create flexible match condition
            if entity_type and entity_type != "Activity":  # Skip Activity type
                entity_conditions.append(f"(n:Entity WHERE n.name CONTAINS '{entity_name}' OR n.entity_type CONTAINS '{entity_type}')")
            else:
                entity_conditions.append(f"(n:Entity WHERE n.name CONTAINS '{entity_name}')")
        
        # Default query just finds related entities
        cypher_query = f"""
        MATCH path = (n1:Entity)-[r]-(n2:Entity)
        WHERE ANY(n IN nodes(path) WHERE {" OR ".join(entity_conditions)})
        RETURN n1, r, n2
        LIMIT 10
        """
        
        # If we have relationships, make the query more specific
        if relationships and len(entities) > 1:
            rel_conditions = " OR ".join([f"type(r) CONTAINS '{rel.upper()}'" for rel in relationships])
            cypher_query = f"""
            MATCH (n1:Entity)-[r]->(n2:Entity)
            WHERE 
              ({" OR ".join([f"n1.name CONTAINS '{e.get('entity', '')}'" for e in entities])})
              AND ({" OR ".join([f"n2.name CONTAINS '{e.get('entity', '')}'" for e in entities])})
              AND ({rel_conditions})
            RETURN n1, r, n2
            LIMIT 10
            """
        
        # Execute the query
        with self.neo4j_driver.session() as session:
            result = session.run(cypher_query).data()
            
            # Process the results to clean up the response
            processed_results = []
            for record in result:
                processed_record = {}
                
                # Process n1 node
                if "n1" in record:
                    n1 = record["n1"]
                    processed_record["source"] = {
                        "name": n1.get("name", ""),
                        "type": n1.get("entity_type", ""),
                        "props": {k: v for k, v in n1.items() if k not in ["name", "entity_type"]}
                    }
                
                # Process relationship
                if "r" in record:
                    r = record["r"]
                    processed_record["relationship"] = {
                        "type": type(r).__name__,
                        "props": {k: v for k, v in dict(r).items()}
                    }
                
                # Process n2 node
                if "n2" in record:
                    n2 = record["n2"]
                    processed_record["target"] = {
                        "name": n2.get("name", ""),
                        "type": n2.get("entity_type", ""),
                        "props": {k: v for k, v in n2.items() if k not in ["name", "entity_type"]}
                    }
                
                processed_results.append(processed_record)
            
            return processed_results
    
    def _vector_search(self, query_text: str) -> List[Dict[str, Any]]:
        """
        Perform vector similarity search by fetching embeddings from :Document nodes
        and computing similarity in Python.
        
        Args:
            query_text: The natural language query
            
        Returns:
            List of vector search results with similarity scores
        """
        self.logger.debug(f"Performing Python-side vector search for: {query_text}")
        
        query_embedding = self.embedding_model.embed_query(query_text)  # Use embed_query for specific query task type
        if not query_embedding or not isinstance(query_embedding, list) or not all(isinstance(x, (int, float)) for x in query_embedding):
            self.logger.error(f"Invalid query embedding: {query_embedding}")
            return []

        query_embedding_np = np.array([query_embedding])

        # Fetch :Document nodes and their embeddings
        fetch_embeddings_query = """
        MATCH (d:Document)
        WHERE d.embedding IS NOT NULL AND d.id IS NOT NULL AND d.content IS NOT NULL
        RETURN d.id AS doc_id, d.content AS content_text, d.embedding AS embedding
        """
        
        all_results_with_similarity = []
        
        try:
            with self.neo4j_driver.session() as session:
                records = session.run(fetch_embeddings_query).data()
            
            if not records:
                self.logger.info("No :Document nodes with embeddings, id, and content found.")
                return []

            self.logger.debug(f"Retrieved {len(records)} :Document nodes with embeddings.")

            db_embeddings_list = []
            doc_details_list = []

            for record in records:
                db_emb = record.get("embedding")
                doc_id = record.get("doc_id")
                content_text = record.get("content_text")

                if isinstance(db_emb, list) and all(isinstance(x, (int, float)) for x in db_emb) and doc_id and content_text:
                    db_embeddings_list.append(db_emb)
                    doc_details_list.append({
                        "doc_id": doc_id,
                        "content_text": content_text
                    })
                else:
                    self.logger.warning(f"Skipping document ID '{doc_id}' due to missing data or invalid embedding format.")
            
            if not db_embeddings_list:
                self.logger.info("No valid embeddings found after validation.")
                return []

            db_embeddings_np = np.array(db_embeddings_list)

            if query_embedding_np.shape[1] != db_embeddings_np.shape[1]:
                self.logger.error(f"Query embedding dim ({query_embedding_np.shape[1]}) != DB embedding dim ({db_embeddings_np.shape[1]}).")
                return []
                
            similarities = cosine_similarity(query_embedding_np, db_embeddings_np)[0]

            for i, score in enumerate(similarities):
                if score >= self.similarity_threshold:
                    # Map to expected output format: name, type, text, score
                    all_results_with_similarity.append({
                        "name": doc_details_list[i]["doc_id"], # Use doc_id as name
                        "type": "Document",                   # Set type as Document
                        "text": doc_details_list[i]["content_text"], # Use content as text
                        "score": float(score)
                    })
            
            all_results_with_similarity.sort(key=lambda x: x["score"], reverse=True)
            
            final_results = all_results_with_similarity[:self.vector_top_k]
            self.logger.info(f"Vector search (Python-side for :Document) found {len(final_results)} results.")
            return final_results

        except Exception as e:
            self.logger.error(f"Error during Python-side vector search for :Document nodes: {e}")
            self.logger.debug(traceback.format_exc())
            return []
    
    def _synthesize_response(
        self, 
        query_text: str,
        graph_results: List[Dict[str, Any]], 
        vector_results: List[Dict[str, Any]]
    ) -> str:
        """
        Synthesize a response using both graph and vector search results.
        
        Args:
            query_text: The original query
            graph_results: Results from knowledge graph query
            vector_results: Results from vector similarity search
            
        Returns:
            Synthesized answer string
        """
        # Handle the case where we have no results
        if not graph_results and not vector_results:
            return "I don't have enough information to answer this question accurately."
        
        # Format graph results for the prompt
        graph_context = "No relevant graph relationships found."
        if graph_results:
            graph_items = []
            for result in graph_results:
                source = result.get("source", {}).get("name", "")
                relationship = result.get("relationship", {}).get("type", "")
                target = result.get("target", {}).get("name", "")
                if source and relationship and target:
                    graph_items.append(f"- {source} {relationship} {target}")
            
            if graph_items:
                graph_context = "Knowledge Graph Relationships:\n" + "\n".join(graph_items)
        
        # Format vector results for the prompt
        vector_context = "No relevant text content found."
        if vector_results:
            vector_items = []
            for result in vector_results:
                name = result.get("name", "")
                text = result.get("text", "")
                score = result.get("score", 0.0)
                if name and text:
                    vector_items.append(f"- {name}: {text} (similarity: {score:.2f})")
            
            if vector_items:
                vector_context = "Relevant Text Content:\n" + "\n".join(vector_items)
        
        # System prompt for synthesis
        system_prompt = f"""
        Generate a comprehensive answer to the user's query based on the knowledge graph
        relationships and text content provided. Combine structural knowledge from the graph
        with contextual information from the text.
        
        Only include information that is directly relevant to answering the question.
        If there's insufficient information to answer confidently, acknowledge the limitations.
        
        Thinking budget: {self.thinking_budget} tokens
        """
        
        # Create user prompt with context
        user_prompt = f"""
        Question: {query_text}
        
        Available Information:
        
        {graph_context}
        
        {vector_context}
        """
        
        # Generate the response
        response = self.llm.generate_content(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        
        if hasattr(response, "text"):
            return response.text.strip()
        elif hasattr(response, "candidates") and response.candidates:
            return response.candidates[0].content.parts[0].text.strip()
        else:
            return "Unable to generate a response based on the available information."
    
    def _extract_sources(
        self,
        graph_results: List[Dict[str, Any]],
        vector_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract source information from results for citations.
        
        Args:
            graph_results: Results from knowledge graph query
            vector_results: Results from vector similarity search
            
        Returns:
            List of source information dictionaries
        """
        sources = []
        
        # Extract graph sources
        for idx, result in enumerate(graph_results):
            source_name = result.get("source", {}).get("name", "")
            target_name = result.get("target", {}).get("name", "")
            rel_type = result.get("relationship", {}).get("type", "")
            
            if source_name and target_name and rel_type:
                sources.append({
                    "id": f"g{idx}",
                    "type": "graph",
                    "content": f"{source_name} {rel_type} {target_name}"
                })
        
        # Extract vector sources
        for idx, result in enumerate(vector_results):
            name = result.get("name", "")
            text = result.get("text", "")
            score = result.get("score", 0.0)
            
            if name and text:
                sources.append({
                    "id": f"v{idx}",
                    "type": "vector",
                    "content": text[:200] + ("..." if len(text) > 200 else ""),
                    "name": name,
                    "score": score
                })
        
        return sources
