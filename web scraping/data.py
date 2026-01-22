import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import json
import time
from collections import deque

BASE_URL = "https://apollodiagnostics.in"
visited = set()
data = []

headers = {
    "User-Agent": "Mozilla/5.0"
}

def clean_text(soup):
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    return text

def scrape_site_iterative(start_url):
    queue = deque([start_url])
    
    while queue:
        url = queue.popleft()
        
        if url in visited:
            continue
        visited.add(url)
        
        print(f"Scraping: {url}")

        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code != 200:
                print(f"Failed to fetch {url}: Status {res.status_code}")
                continue
        except Exception as e:
            print(f"Error requesting {url}: {e}")
            continue

        try:
            soup = BeautifulSoup(res.text, "html.parser")
            title = soup.title.text.strip() if soup.title else ""

            # 1. Extract Category & Sub-Category from breadcrumbs
            # Look for a p tag containing "Home >"
            breadcrumb_tag = soup.find(lambda tag: tag.name == "p" and "Home >" in tag.get_text())
            breadcrumb_text = breadcrumb_tag.get_text(separator="|", strip=True) if breadcrumb_tag else ""
            
            # Format usually: Home > Category > SubCategory
            # The separator might need adjustment based on how get_text handles the > symbol or HTML entities
            # In the raw HTML it was just text.
            parts = [p.strip() for p in breadcrumb_text.replace(">", "|").split("|") if p.strip()]
            
            category = "General"
            sub_category = ""
            
            if len(parts) > 1:
                category = parts[1]
            if len(parts) > 2:
                sub_category = parts[2]
            
            # 2. Extract Description (Overview)
            description = ""
            # Find "Overview" text
            overview_header = soup.find(string=lambda t: t and "Overview" in t)
            if overview_header:
                # Try to find the content following the Overview header.
                # Based on HTML, it might be in a subsequent div or sibling.
                # We'll traverse up to a container and look for the text explanation.
                overview_parent = overview_header.find_parent("div")
                if overview_parent:
                    # Look for the next siblings having text
                    sibling = overview_parent.find_next_sibling("div")
                    if sibling:
                        description = sibling.get_text(separator=" ", strip=True)
            
            # If no specific description found, or as a fallback for other pages
            if not description:
                # Try finding standard meta description
                meta_desc = soup.find("meta", attrs={"name": "description"})
                if meta_desc:
                    description = meta_desc.get("content", "").strip()

            # 3. Clean Text (keep it but maybe less verbose if we have specific fields)
            # user said "only text data", implied relevant info.
            # detailed_text = clean_text(soup) # Keeping this might be redundant if we just want the description.
            # Let's keep a cleaner version of text just in case.

            # 4. Extract Links for CRAWLING ONLY (not for saving)
            links = []
            for a in soup.find_all("a", href=True):
                link = urljoin(BASE_URL, a["href"])
                parsed = urlparse(link)
                # Same website only
                if parsed.netloc == urlparse(BASE_URL).netloc:
                    clean_link = parsed.scheme + "://" + parsed.netloc + parsed.path
                    links.append(clean_link)
            
            unique_links = list(set(links))

            # Only save if we found some meaningful data (e.g. valid category)
            # or simply save all pages visited but with cleaner structure.
            
            if title: # Ensure page loaded
                data.append({
                    "category": category,
                    "sub_category": sub_category,
                    "description": description,
                    "page_title": title,
                    "url": url
                    # "links": unique_links  <-- Removed as per request
                })

            # Add unvisited links to queue
            for l in unique_links:
                if l not in visited:
                    queue.append(l)
            
            time.sleep(1)   # polite crawling
            
            time.sleep(1)   # polite crawling
            
        except Exception as e:
            print(f"Error parsing {url}: {e}")

# start crawling
try:
    scrape_site_iterative(BASE_URL)
except KeyboardInterrupt:
    print("\n🛑 Scraping interrupted manually. Saving collected data...")

# save JSON
print(f"Saving {len(data)} pages to file...")
with open("apollo_diagnostics_text_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("✅ Scraping completed. Data saved in apollo_diagnostics_text_data.json")
