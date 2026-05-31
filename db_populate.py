import os
import psycopg2
from psycopg2.extras import execute_values
from scraper import get_wiki_links

DB_CONFIG = {
    "dbname": "postgres",
    "user": "postgres",              
    "password": os.environ.get("DB_PASSWORD"),  
    "host": "localhost",
    "port": "5432"
}

def save_page_to_db(cursor, page_title):
    """Inserts a page title into the database if it doesn't exist and returns its page_id."""
    cursor.execute(
        """
        INSERT INTO public.pages (title) 
        VALUES (%s) 
        ON CONFLICT (title) DO NOTHING;
        """, 
        (page_title,)
    )
    cursor.execute("SELECT page_id FROM public.pages WHERE title = %s;", (page_title,))
    return cursor.fetchone()[0]

def populate_wiki_graph(source_id, source_title):
    """Scrapes a page, saves all its internal links, and marks it as scraped."""
    print(f"Scraping '{source_title}'...")
    target_links = get_wiki_links(source_title)
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    if not target_links:
        print(f"No links found or failed to fetch page for '{source_title}'.")
        try:
            cur.execute("UPDATE public.pages SET is_scraped = TRUE WHERE page_id = %s;", (source_id,))
            conn.commit()
        finally:
            cur.close()
            conn.close()
        return

    try:
        print(f"Adding {len(target_links)} target pages to 'pages' table...")
        for link in target_links:
            cur.execute(
                "INSERT INTO public.pages (title) VALUES (%s) ON CONFLICT (title) DO NOTHING;", 
                (link,)
            )
        
        cur.execute("SELECT title, page_id FROM public.pages;")
        title_to_id = dict(cur.fetchall())
        
        link_pairs = []
        for link in target_links:
            target_id = title_to_id.get(link)
            if target_id:
                link_pairs.append((source_id, target_id))
        
        print("Linking pages together in 'links_to' table...")
        insert_links_query = """
            INSERT INTO public.links_to (source_page_id, target_page_id) 
            VALUES %s 
            ON CONFLICT (source_page_id, target_page_id) DO NOTHING;
        """
        execute_values(cur, insert_links_query, link_pairs)
        
        cur.execute("UPDATE public.pages SET is_scraped = TRUE WHERE page_id = %s;", (source_id,))
        
        conn.commit()
        print(f"Successfully saved the graph for '{source_title}' into pgAdmin!")

    except Exception as e:
        conn.rollback()
        print(f"Database error occurred: {e}")
        
    finally:
        cur.close()
        conn.close()

def crawl_wikipedia(max_pages_to_scrape=5):
    """Finds unscraped pages in the database and crawls them sequentially using database IDs."""
    for i in range(max_pages_to_scrape):
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("SELECT page_id, title FROM public.pages WHERE is_scraped = FALSE LIMIT 1;")
        result = cur.fetchone()

        cur.close()
        conn.close()

        if result:
            source_id, next_page = result
            print(f"\n[Progress: {i+1}/{max_pages_to_scrape}]:")
            populate_wiki_graph(source_id, next_page)
        else:
            print("No more unscraped pages found. Crawling complete!")
            break

if __name__ == "__main__":
    crawl_wikipedia(max_pages_to_scrape=30)