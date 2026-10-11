import asyncio
from async_crawler import AsyncCrawler
from graph import WebGraphAnalyzer


async def main():
    target = "https://docs.python.org/3/"
    print(f"1. Crawling {target} ...")
    
    crawler = AsyncCrawler(start_url=target, max_depth=2, max_pages=15)
    crawl_result = await crawler.crawl()
    
    print(f"2. Analyzing graph network...")
    analyzer = WebGraphAnalyzer(nodes=crawl_result.nodes, edges=crawl_result.edges)
    output = analyzer.export_to_dict()

    summary = output["summary"]
    print("\n================ GRAPH ANALYTICS REPORT ================")
    print(f"Total Pages (Nodes) : {summary['total_nodes']}")
    print(f"Total Links (Edges) : {summary['total_edges']}")
    print(f"Clusters (Louvain)  : {summary['num_communities']}")
    print(f"Isolated Pages      : {summary['isolated_count']}")
    print(f"Pendent Pages       : {summary['pendent_count']}")
    
    print("\n--- Top 3 Important Pages (PageRank) ---")
    for url, score in summary['top_pagerank'][:3]:
        print(f" [{score:.4f}] {url}")
        
    print("\n--- Top 3 Hub Pages (Out-Degree) ---")
    for url, deg in summary['top_hubs'][:3]:
        print(f" [{deg} links] {url}")
    print("========================================================")

if __name__ == "__main__":
    asyncio.run(main())