import re
import requests 

def get_wiki_links(page_title):
    url=f"https://en.wikipedia.org/wiki/{page_title}"
    headers={'User-Agent': 'WikipediaSpeedrunUniversityProject/1.0 (bgs376@alumni.ku.dk)'
    }

    try:
        response=requests.get(url, headers=headers, timeout=5)
        if response.status_code!=200:
            print(f"Failed to retrieve page: {page_title} (Status code: {response.status_code})")
            return []
        
        html_content=response.text

        # Regex pattern to find links in the main content of the Wikipedia page
        pattern = r'href="/wiki/([a-zA-Z0-9_\-%]+)"'

        raw_links=re.findall(pattern, html_content)

        valid_links=set()
        ignored_prefixes=('Main_Page', 'Portal:', 'Special:', 'Wikipedia:', 'Help:', 'File:', 'Talk:', 'Category:')

        for link in raw_links:
            link_clean=link.strip('/')
            if not link_clean.startswith(ignored_prefixes):
                valid_links.add(link_clean)

        return list(valid_links)
    
    except requests.RequestException as e:
        print(f"Error fetching page: {page_title} ({e})")
        return []
    
# Test Block
if __name__ == "__main__":
    test_page="Copenhagen"
    print(f"Links found on the Wikipedia page for '{test_page}':")
    links=get_wiki_links(test_page)
    
    print(f"Found {len(links)} valid unique internal links!")
    print("First 10 sample links found:")
    for l in links[:10]:
        print(f" - {l}")