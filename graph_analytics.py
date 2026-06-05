import os
import random
import psycopg2
from collections import deque

DB_CONFIG={
    "dbname": "postgres",
    "user": "postgres",              
    "password": os.environ.get("DB_PASSWORD"),  
    "host": "localhost",
    "port": "5432"
}

def load_graph_into_memory():
    """Connects to the DB and loads the entire graph layout into an adjacency list."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute("SELECT page_id, title FROM public.pages;")
    id_to_title=dict(cur.fetchall())

    cur.execute("SELECT source_page_id, target_page_id FROM public.links_to;")
    edges=cur.fetchall()

    graph={}
    for source, target in edges:
        if source not in graph:
            graph[source]=[]
        graph[source].append(target)

    cur.close()
    conn.close()
    return graph, id_to_title

def bfs_distance(graph, start_id, target_id):
    """A lightweight version of BFS that just returns the number of clicks (integer), or None."""
    if start_id == target_id:
        return 0
        
    queue = deque([(start_id, 0)])
    visited = {start_id}
    
    while queue:
        current_id, current_clicks = queue.popleft()
        
        if current_id == target_id:
            return current_clicks
            
        neighbors = graph.get(current_id, [])
        for neighbor_id in neighbors:
            if neighbor_id not in visited:
                visited.add(neighbor_id)
                queue.append((neighbor_id, current_clicks + 1))
                
    return None  # No path exists

def run_experiment(num_samples=100):
    """Picks smart random pairs of pages and analyzes path characteristics."""
    print("Initializing Database Connections...")
    graph, id_to_title = load_graph_into_memory()
    all_page_ids = list(id_to_title.keys())
    
    total_pages = len(all_page_ids)
    # Collect only the page IDs that we have actually scraped (exist as keys in our graph dict)
    scraped_page_ids = [pid for pid in all_page_ids if pid in graph]
    scraped_count = len(scraped_page_ids)
    
    print(f"\n=== DATABASE METRICS ===")
    print(f"Total discovered nodes (pages in DB): {total_pages}")
    print(f"Total processed source hubs (scraped pages): {scraped_count}")
    
    if scraped_count < 2:
        print("Not enough fully processed hub pages yet to run a targeted evaluation.")
        return

    successful_paths = 0
    failed_paths = 0
    click_counts = []
    
    print(f"\nRunning simulation on {num_samples} targeted random page pairs...")
    
    for i in range(num_samples):
        # STRATEGY: Start at a page we HAVE scraped, target any page we KNOW exists
        start_id = random.choice(scraped_page_ids)
        target_id = random.choice(scraped_page_ids)
        while start_id == target_id:
            target_id = random.choice(scraped_page_ids)
            
        clicks = bfs_distance(graph, start_id, target_id)
        
        if clicks is not None:
            successful_paths += 1
            click_counts.append(clicks)
        else:
            failed_paths += 1

    # Calculate metrics
    connectivity_rate = (successful_paths / num_samples) * 100
    avg_clicks = sum(click_counts) / len(click_counts) if click_counts else 0
    max_clicks = max(click_counts) if click_counts else 0
    min_clicks = min(click_counts) if click_counts else 0

    print("\n=========================================")
    print("       GRAPH TOPOLOGY EVALUATION         ")
    print("=========================================")
    print(f"Total Targeted Pairs Tested:    {num_samples}")
    print(f"Successful Connections Found:   {successful_paths}")
    print(f"Dead Ends / Unreachable Pairs:  {failed_paths}")
    print(f"Graph Connectivity Rate:        {connectivity_rate:.2f}%")
    
    if successful_paths > 0:
        print(f"Average Degrees of Separation:  {avg_clicks:.2f} clicks")
        print(f"Shortest Path Sample found:     {min_clicks} clicks")
        print(f"Graph Diameter (Max Sample):    {max_clicks} clicks")
    print("=========================================")

if __name__ == "__main__":
    run_experiment(num_samples=100)