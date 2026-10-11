import asyncio
import time
from async_crawler import AsyncCrawler

async def run_test():
    target = "https://docs.python.org/3/"
    print(f"Starting crawl for: {target}")
    
    crawler = AsyncCrawler(
        start_url=target,
        max_depth=2,
        max_pages=20,
        max_concurrency=5
    )
    
    start_time = time.perf_counter()
    result = await crawler.crawl()
    elapsed = time.perf_counter() - start_time
    
    print(f"\n--- Crawl Complete in {elapsed:.2f}s ---")
    print(f"Discovered Nodes (Pages): {len(result.nodes)}")
    print(f"Discovered Edges (Links): {len(result.edges)}")
    print(f"Errors Encountered: {len(result.errors)}")
    
    # Print sample edges
    print("\nSample Edges (Directed Hyperlinks):")
    for src, dst in result.edges[:5]:
        print(f"  {src}\n   └─► {dst}")

if __name__ == "__main__":
    asyncio.run(run_test())