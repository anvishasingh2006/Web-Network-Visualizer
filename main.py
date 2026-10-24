import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from pyvis.network import Network

from async_crawler import AsyncCrawler
from graph import WebGraphAnalyzer

app = FastAPI(title="Web Network Visualiser")


class CrawlRequest(BaseModel):
    url: HttpUrl
    max_depth: int = 2
    max_pages: int = 25
    max_concurrency: int = 5


@app.get("/", response_class=HTMLResponse)
def serve_input_ui():
    """Serves an interactive web interface with an input box for URLs."""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Web Network Visualiser</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background-color: #1a1a1a;
                color: #ffffff;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .card {
                background: #2a2a2a;
                padding: 2.5rem;
                border-radius: 12px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.5);
                width: 100%;
                max-width: 500px;
                text-align: center;
            }
            h1 { margin-top: 0; color: #4CAF50; font-size: 1.8rem; }
            p { color: #aaa; margin-bottom: 1.5rem; font-size: 0.95rem; }
            .form-group {
                display: flex;
                flex-direction: column;
                gap: 12px;
                text-align: left;
            }
            label { font-size: 0.85rem; color: #ddd; font-weight: 600; }
            input[type="url"], input[type="number"] {
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #444;
                background: #1a1a1a;
                color: #fff;
                font-size: 1rem;
            }
            input:focus { outline: none; border-color: #4CAF50; }
            button {
                margin-top: 10px;
                padding: 12px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 1rem;
                font-weight: bold;
                cursor: pointer;
                transition: background 0.2s;
            }
            button:hover { background: #45a049; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Web Network Visualiser</h1>
            <p>Enter any website URL to crawl and visualize its hyperlink network graph.</p>
            <form action="/visualize" method="get" class="form-group">
                <label for="url">Website URL:</label>
                <input type="url" id="url" name="url" placeholder="https://docs.python.org/3/" required>
                
                <label for="max_pages">Max Pages to Crawl:</label>
                <input type="number" id="max_pages" name="max_pages" value="25" min="5" max="100">
                
                <button type="submit">Generate Network Graph</button>
            </form>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/visualize", response_class=HTMLResponse)
async def generate_interactive_graph(url: str, max_pages: int = 25):
    """
    Generates an interactive force-directed graph using PyVis and renders it in browser.
    """
    crawler = AsyncCrawler(start_url=url, max_depth=2, max_pages=max_pages)
    crawl_result = await crawler.crawl()
    analyzer = WebGraphAnalyzer(nodes=crawl_result.nodes, edges=crawl_result.edges)
    data = analyzer.export_to_dict()

    net = Network(height="750px", width="100%", directed=True, bgcolor="#1a1a1a", font_color="white")
    net.force_atlas_2based()

    colors = ["#e74c3c", "#3498db", "#2ecc71", "#f1c40f", "#9b59b6", "#e67e22"]

    for node in data["graph"]["nodes"]:
        comm_color = colors[node["community"] % len(colors)]
        node_size = max(10, int(node["pagerank"] * 500))
        label_text = node["id"].replace("https://", "").replace("http://", "")
        
        title_hover = (
    f"URL: {node['id']}\n"
    f"PageRank: {node['pagerank']:.4f}\n"
    f"In-Degree: {node['in_degree']}\n"
    f"Out-Degree: {node['out_degree']}"
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