# Web Network Visualiser

> An asynchronous Python application that crawls web domains, models page hyperlink structures into directed graphs, computes graph theory analytics, and renders interactive force-directed visualisations.

---

## Technical Highlights

* **Concurrent Async Engine:** Built using `asyncio` and `httpx` with `asyncio.Semaphore` rate limiting to fetch pages concurrently without I/O blocking.
* **Defensive Security (SSRF Protection):** Resolves hostnames asynchronously via DNS to validate IP addresses against private networks (`10.0.0.0/8`, `192.168.0.0/16`, `127.0.0.0/8`), local loopbacks, and cloud metadata endpoints before fetching.
* **Robots.txt & Politeness:** Parses domain `robots.txt` rules using `urllib.robotparser` and enforces configurable concurrency caps and custom User-Agents.
* **Graph Theory Analytics (NetworkX):**
  * **PageRank:** Evaluates node importance based on incoming hyperlink structure.
  * **Betweenness Centrality:** Identifies bridge pages connecting disparate graph sections.
  * **Louvain Modularity:** Discovers thematic communities and page clusters via undirected projection.
  * **Topological Metrics:** Detects out-degree hubs, in-degree authorities, isolated nodes, and pendent (leaf) pages.
* **Interactive Visualization:** Generates force-directed network graphs dynamically using PyVis with community-based color encoding and PageRank-scaled node sizing.

---

## Architecture Overview

```text
[ Target URL ] ──► [ SSRF Security Guard ] ──► [ Async Crawler Engine ]
                                                         │
                                                         ▼
[ PyVis Visualiser ] ◄── [ FastAPI Web Server ] ◄── [ NetworkX Engine ]
```

---

## Project Structure

```text
web-network-visualiser/
├── async_crawler.py      # Async crawler engine with rate limiting & normalization
├── security.py           # SSRF validator & robots.txt compliance guard
├── graph.py              # NetworkX graph model & graph theory algorithms
├── main.py               # FastAPI application, REST endpoints, WebSockets & PyVis route
├── tests/
│   └── test_pipeline.py  # Pytest suite for SSRF, crawler, and graph metrics
├── Dockerfile            # Container configuration
├── docker-compose.yml    # Single-command environment orchestration
├── requirements.txt      # Project dependencies
└── README.md
```

---

## Getting Started

### Prerequisites
* Python 3.11+
* Docker & Docker Compose (Optional)

### Option 1: Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/web-network-visualiser.git
   cd web-network-visualiser
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the FastAPI server:**
   ```bash
   uvicorn main:app --reload
   ```

4. **Access the application:**
   * **Swagger API Documentation:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   * **Interactive Graph Visualizer:** [http://127.0.0.1:8000/visualize?url=https://docs.python.org/3/&max_pages=25](http://127.0.0.1:8000/visualize?url=https://docs.python.org/3/&max_pages=25)

---

### Option 2: Docker Containerization

Run the full stack with a single command:

```bash
docker-compose up --build
```

The application will be accessible at `http://localhost:8000`.

---

## Testing

Execute the unit test suite covering URL normalization, SSRF guard rules, and graph analytics calculations:

```bash
pytest -v
```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Health check endpoint |
| `POST` | `/api/crawl` | Triggers a crawl and returns full graph metrics in JSON |
| `WS` | `/ws/crawl` | WebSocket stream for live crawl progress and graph creation |
| `GET` | `/visualize` | Serves an interactive force-directed PyVis graph in HTML |
