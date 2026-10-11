import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from pyvis.network import Network

from async_crawler import AsyncCrawler
from graph import WebGraphAnalyzer

app = FastAPI(title="Web Network Visualiser API")


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_depth: int = 2
    max_pages: int = 25
    max_concurrency: int = 5


@app.get("/")
def read_root():
    return {"message": "Web Network Visualiser Backend is active."}


@app.post("/api/crawl")
async def run_crawl_api(req: CrawlRequest):
    """Triggers a complete crawl and returns graph analytics JSON."""
    crawler = AsyncCrawler(
        start_url=str(req.url),
        max_depth=req.max_depth,
        max_pages=req.max_pages,
        max_concurrency=req.max_concurrency
    )
    crawl_result = await crawler.crawl()
    analyzer = WebGraphAnalyzer(nodes=crawl_result.nodes, edges=crawl_result.edges)
    return analyzer.export_to_dict()


@app.websocket("/ws/crawl")
async def websocket_crawl(websocket: WebSocket):
    """
    Streams live crawl progress over WebSocket.
    Client sends JSON payload: {"url": "...", "max_depth": 2, "max_pages": 30}
    """
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        params = json.loads(data)
        
        target_url = params.get("url")
        max_depth = params.get("max_depth", 2)
        max_pages = params.get("max_pages", 25)

        crawler = AsyncCrawler(start_url=target_url, max_depth=max_depth, max_pages=max_pages)
        
        # Stream initial connection ACK
        await websocket.send_json({"type": "status", "message": f"Starting crawl on {target_url}"})

        # Run crawl
        crawl_result = await crawler.crawl()

        # Send discovered graph elements
        for node in crawl_result.nodes:
            await websocket.send_json({"type": "node", "data": node})
            await asyncio.sleep(0.01)  # Throttle slightly for smooth frontend animation

        for src, dst in crawl_result.edges:
            await websocket.send_json({"type": "edge", "data": {"source": src, "target": dst}})
            await asyncio.sleep(0.005)

        # Compute and send final graph metrics
        analyzer = WebGraphAnalyzer(nodes=crawl_result.nodes, edges=crawl_result.edges)
        analytics = analyzer.export_to_dict()
        
        await websocket.send_json({"type": "complete", "summary": analytics["summary"]})

    except WebSocketDisconnect:
        print("WebSocket client disconnected.")
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


@app.get("/visualize", response_class=HTMLResponse)
async def generate_interactive_graph(url: str = "https://docs.python.org/3/", max_pages: int = 30):
    """
    Generates an interactive HTML force-directed graph using PyVis and serves it directly.
    """
    crawler = AsyncCrawler(start_url=url, max_depth=2, max_pages=max_pages)
    crawl_result = await crawler.crawl()
    analyzer = WebGraphAnalyzer(nodes=crawl_result.nodes, edges=crawl_result.edges)
    data = analyzer.export_to_dict()

    net = Network(height="750px", width="100%", directed=True, bgcolor="#222222", font_color="white")
    net.force_atlas_2based()

    # Color mapping per Louvain community
    colors = ["#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6", "#e67e22"]

    for node in data["graph"]["nodes"]:
        comm_color = colors[node["community"] % len(colors)]
        # Node size proportional to PageRank
        node_size = max(10, int(node["pagerank"] * 500))
        
        label_text = node["id"].replace("https://", "").replace("http://", "")
        title_hover = (
            f"<b>URL:</b> {node['id']}<br>"
            f"<b>PageRank:</b> {node['pagerank']}<br>"
            f"<b>In-Degree:</b> {node['in_degree']}<br>"
            f"<b>Out-Degree:</b> {node['out_degree']}"
        )

        net.add_node(
            node["id"],
            label=label_text,
            title=title_hover,
            color=comm_color,
            size=node_size
        )

    for edge in data["graph"]["edges"]:
        net.add_edge(edge["source"], edge["target"])

    html_content = net.generate_html()
    return HTMLResponse(content=html_content)