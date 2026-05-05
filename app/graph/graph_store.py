import json
import logging
import os
from pathlib import Path
from typing import Any

import networkx as nx

from app.config import settings

logger = logging.getLogger(__name__)

class GraphStore:
    """Singleton managing the multi-modal evidence graph using NetworkX."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GraphStore, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.persist_path = Path(settings.GRAPH_PERSIST_PATH)
        self.graph = nx.DiGraph()
        self._load()

    def _load(self):
        """Loads the graph from JSON if it exists."""
        if self.persist_path.exists():
            try:
                with open(self.persist_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data, directed=True)
                logger.info(f"Graph loaded from {self.persist_path} with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges.")
            except Exception as e:
                logger.error(f"Failed to load graph from {self.persist_path}: {e}")
                self.graph = nx.DiGraph()
        else:
            logger.info("No existing graph found. Starting with empty graph.")

    def save(self):
        """Serializes the graph to JSON and saves to disk."""
        try:
            self.persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = nx.node_link_data(self.graph)
            with open(self.persist_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save graph to {self.persist_path}: {e}")

    def add_chunk_node(
        self,
        chunk_id: str,
        kb_id: str,
        modality: str,
        document_id: str,
        filename: str,
        text_preview: str,
        timestamp_start: float | None = None,
        timestamp_end: float | None = None,
        page_number: int | None = None,
    ):
        """Adds a chunk node to the graph."""
        self.graph.add_node(
            chunk_id,
            kb_id=kb_id,
            modality=modality,
            document_id=document_id,
            filename=filename,
            text_preview=text_preview,
            timestamp_start=timestamp_start,
            timestamp_end=timestamp_end,
            page_number=page_number,
        )
        logger.info(f"Added chunk node {chunk_id} to graph. Total nodes now: {self.graph.number_of_nodes()}")

    def add_link(self, source_chunk_id: str, target_chunk_id: str, link_type: str, strength: float, metadata: dict | None = None):
        """Adds a directed edge between two chunks. Avoids reciprocal duplication."""
        if source_chunk_id == target_chunk_id:
            return  # No self-loops

        if not self.graph.has_node(source_chunk_id) or not self.graph.has_node(target_chunk_id):
            logger.warning(f"Attempted to link non-existent nodes: {source_chunk_id} -> {target_chunk_id}")
            return

        # Prevent duplicate reciprocal edges for the same relationship type
        # E.g. A->B exists, we don't need B->A
        if self.graph.has_edge(source_chunk_id, target_chunk_id):
            return
        if self.graph.has_edge(target_chunk_id, source_chunk_id):
            return

        edge_attrs = {"link_type": link_type, "strength": strength}
        if metadata:
            edge_attrs.update(metadata)

        self.graph.add_edge(source_chunk_id, target_chunk_id, **edge_attrs)

    def get_neighbours(self, chunk_id: str, min_strength: float = 0.5) -> list[dict]:
        """Returns nodes directly connected to chunk_id (both in and out edges) with strength >= min_strength."""
        self._load()
        if not self.graph.has_node(chunk_id):
            return []

        neighbours = []
        # Undirected traversal for querying since we avoided reciprocal edges
        for u, v, data in self.graph.edges(chunk_id, data=True):
            target = v if u == chunk_id else u
            if data.get("strength", 0.0) >= min_strength:
                node_data = self.graph.nodes[target]
                neighbours.append({
                    "chunk_id": target,
                    "link_type": data.get("link_type", "unknown"),
                    "strength": data.get("strength", 0.0),
                    "modality": node_data.get("modality", "unknown"),
                    "text_preview": node_data.get("text_preview", ""),
                })

        for u, v, data in self.graph.in_edges(chunk_id, data=True):
            source = u
            if data.get("strength", 0.0) >= min_strength:
                node_data = self.graph.nodes[source]
                neighbours.append({
                    "chunk_id": source,
                    "link_type": data.get("link_type", "unknown"),
                    "strength": data.get("strength", 0.0),
                    "modality": node_data.get("modality", "unknown"),
                    "text_preview": node_data.get("text_preview", ""),
                })

        # Deduplicate just in case
        unique_neighbours = {n["chunk_id"]: n for n in neighbours}
        return list(unique_neighbours.values())

    def get_evidence_chain(self, chunk_id: str, depth: int = 2) -> dict:
        """Performs BFS to get a subgraph rooted at chunk_id up to `depth` hops."""
        self._load()
        if not self.graph.has_node(chunk_id):
            return {"root_chunk_id": chunk_id, "nodes": [], "edges": []}

        # Create an undirected view to find all connected evidence regardless of edge direction
        undirected_G = self.graph.to_undirected(as_view=True)
        subgraph_nodes = set(nx.single_source_shortest_path_length(undirected_G, chunk_id, cutoff=depth).keys())
        subgraph = self.graph.subgraph(subgraph_nodes)

        nodes = [{"id": n, **data} for n, data in subgraph.nodes(data=True)]
        edges = [{"source": u, "target": v, **data} for u, v, data in subgraph.edges(data=True)]

        return {"root_chunk_id": chunk_id, "nodes": nodes, "edges": edges}

    def delete_document_nodes(self, document_id: str):
        """Removes all nodes associated with a document_id."""
        self._load()
        nodes_to_remove = [n for n, data in self.graph.nodes(data=True) if data.get("document_id") == document_id]
        if nodes_to_remove:
            self.graph.remove_nodes_from(nodes_to_remove)
            logger.info(f"Deleted {len(nodes_to_remove)} nodes for document_id {document_id}")

    def get_kb_graph(self, kb_id: str) -> dict:
        """Returns all nodes and edges for a knowledge base."""
        self._load()
        kb_nodes = [n for n, data in self.graph.nodes(data=True) if data.get("kb_id") == kb_id]
        subgraph = self.graph.subgraph(kb_nodes)

        nodes = [{"id": n, **data} for n, data in subgraph.nodes(data=True)]
        edges = [{"source": u, "target": v, **data} for u, v, data in subgraph.edges(data=True)]

        return {"nodes": nodes, "links": edges}

# Global singleton
graph_store = GraphStore()
