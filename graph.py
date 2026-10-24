from dataclasses import dataclass, field
from typing import Any
import networkx as nx


@dataclass
class NodeMetrics:
    url: str
    in_degree: int
    out_degree: int
    pagerank: float
    betweenness: float
    community_id: int
    is_isolated: bool
    is_pendent: bool


@dataclass
class GraphSummary:
    total_nodes: int
    total_edges: int
    num_communities: int
    isolated_nodes: list[str]
    pendent_nodes: list[str]
    top_pagerank_nodes: list[tuple[str, float]]
    top_hubs: list[tuple[str, int]]  # Top out-degree
    node_metrics: dict[str, NodeMetrics] = field(default_factory=dict)


class WebGraphAnalyzer:
    def __init__(self, nodes: set[str], edges: list[tuple[str, str]]):
        self.graph = nx.DiGraph()

        valid_nodes = {str(node).strip() for node in (nodes or []) if isinstance(node, str) and node.strip()}

        # Add explicit nodes first (handles isolated pages)
        for node in valid_nodes:
            self.graph.add_node(node)

        # Add directed hyperlink edges
        for edge in edges or []:
            if not isinstance(edge, (tuple, list)) or len(edge) != 2:
                continue
            src, dst = edge
            src = str(src).strip() if src is not None else ""
            dst = str(dst).strip() if dst is not None else ""
            if src in valid_nodes and dst in valid_nodes:
                self.graph.add_edge(src, dst)

    def compute_analytics(self) -> GraphSummary:
        """Executes full suite of graph analytics algorithms."""
        num_nodes = self.graph.number_of_nodes()
        
        if num_nodes == 0:
            return GraphSummary(
                total_nodes=0,
                total_edges=0,
                num_communities=0,
                isolated_nodes=[],
                pendent_nodes=[],
                top_pagerank_nodes=[],
                top_hubs=[],
                node_metrics={}
            )

        # 1. PageRank & Betweenness Centrality
        try:
            pagerank = nx.pagerank(self.graph, alpha=0.85)
        except Exception:
            # Fallback if power iteration fails to converge
            pagerank = {node: 1.0 / num_nodes for node in self.graph.nodes()}

        try:
            betweenness = nx.betweenness_centrality(self.graph)
        except Exception:
            betweenness = {node: 0.0 for node in self.graph.nodes()}

        # 2. Community Detection via Louvain (requires undirected graph)
        undirected_graph = self.graph.to_undirected()
        try:
            communities = nx.community.louvain_communities(undirected_graph, seed=42)
            community_map = {}
            for comm_id, comm_nodes in enumerate(communities):
                for node in comm_nodes:
                    community_map[node] = comm_id
            num_communities = len(communities)
        except Exception:
            community_map = {node: 0 for node in self.graph.nodes()}
            num_communities = 1

        # 3. Classify Node Types & Collect Metrics
        node_metrics: dict[str, NodeMetrics] = {}
        isolated_nodes: list[str] = []
        pendent_nodes: list[str] = []

        for node in self.graph.nodes():
            in_deg = self.graph.in_degree(node)
            out_deg = self.graph.out_degree(node)
            tot_deg = in_deg + out_deg

            is_iso = (tot_deg == 0)
            is_pen = (tot_deg == 1)

            if is_iso:
                isolated_nodes.append(node)
            if is_pen:
                pendent_nodes.append(node)

            node_metrics[node] = NodeMetrics(
                url=node,
                in_degree=in_deg,
                out_degree=out_deg,
                pagerank=round(pagerank.get(node, 0.0), 5),
                betweenness=round(betweenness.get(node, 0.0), 5),
                community_id=community_map.get(node, 0),
                is_isolated=is_iso,
                is_pendent=is_pen,
            )

        # 4. Rankings
        sorted_pagerank = sorted(
            pagerank.items(), key=lambda item: item[1], reverse=True
        )[:5]
        
        sorted_hubs = sorted(
            self.graph.out_degree(), key=lambda item: item[1], reverse=True
        )[:5]

        return GraphSummary(
            total_nodes=num_nodes,
            total_edges=self.graph.number_of_edges(),
            num_communities=num_communities,
            isolated_nodes=isolated_nodes,
            pendent_nodes=pendent_nodes,
            top_pagerank_nodes=[(url, round(score, 5)) for url, score in sorted_pagerank],
            top_hubs=sorted_hubs,
            node_metrics=node_metrics,
        )

    def export_to_dict(self) -> dict[str, Any]:
        """Exports graph structure in standard node-link JSON format."""
        summary = self.compute_analytics()
        
        nodes_data = [
            {
                "id": node,
                "label": node,
                "in_degree": metrics.in_degree,
                "out_degree": metrics.out_degree,
                "pagerank": metrics.pagerank,
                "betweenness": metrics.betweenness,
                "community": metrics.community_id,
                "is_isolated": metrics.is_isolated,
                "is_pendent": metrics.is_pendent,
            }
            for node, metrics in summary.node_metrics.items()
        ]

        edges_data = [
            {"source": src, "target": dst}
            for src, dst in self.graph.edges()
        ]

        return {
            "summary": {
                "total_nodes": summary.total_nodes,
                "total_edges": summary.total_edges,
                "num_communities": summary.num_communities,
                "isolated_count": len(summary.isolated_nodes),
                "pendent_count": len(summary.pendent_nodes),
                "top_pagerank": summary.top_pagerank_nodes,
                "top_hubs": summary.top_hubs,
            },
            "graph": {
                "nodes": nodes_data,
                "edges": edges_data,
            }
        }