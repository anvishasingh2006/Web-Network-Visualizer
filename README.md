Web Network Visualiser
An asynchronous Python web crawler and graph analytics engine that maps website hyperlink structures into interactive force-directed graph visualisations.
Overview
Web Network Visualiser is a lightweight web topology engine that crawls target domains, constructs directed link graphs, and calculates network analytics (PageRank, Louvain communities, and degree centrality). Built with FastAPI, NetworkX, and PyVis, it offers both REST/WebSocket APIs and an interactive visual canvas.
Features & Engineering Highlights
Concurrent Async Crawler: Non-blocking crawling via asyncio, httpx, and semaphore rate-limiting.
Defensive Security Guard: Asynchronous DNS hostname resolution to prevent SSRF by blocking private/internal IP ranges (10.0.0.0/8, 192.168.0.0/16, loopbacks).
Graph Theory Engine: Automated calculation of PageRank, Betweenness Centrality, Louvain modularity clustering, and topology detection (hubs, isolated, and pendent nodes).
Interactive Canvas: Force-directed network visualization in-browser with community color coding and PageRank-scaled node sizing.
Architecture Overview

[ Target URL ] --> [ SSRF Security Guard ] --> [ Async Crawler Engine ]
                                                         |
                                                         v
[ PyVis Visualiser ] <-- [ FastAPI Web Server ] <-- [ NetworkX Engine ]
Repository Structure

gv project/
├── .github/workflows/ci.yml
├── tests/test_pipeline.py
├── .gitignore
├── async_crawler.py
├── security.py
├── graph.py
├── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
Getting Started
Prerequisites
Python 3.11+
Docker & Docker Compose (Optional)
Local Setup
Install dependencies:


pip install -r requirements.txt
Run the server:


uvicorn main:app --reload
Access the application:
Visualiser: http://localhost:8000/visualize
API Docs: http://localhost:8000/docs
Docker Setup

docker-compose up --build
Testing
Run unit test suite:
pytest -v
API Summary
GET / : Service status health check
POST /api/crawl : Triggers crawl job and returns graph metrics JSON
WS /ws/crawl : Real-time WebSocket stream for crawl progress
GET /visualize : Generates interactive PyVis graph visualization