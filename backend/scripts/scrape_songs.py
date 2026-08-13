import os
import sys
import csv
import httpx
from bs4 import BeautifulSoup
import time
import re
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
URLS_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "urls_to_scrape.txt")
OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "..", "data", "sample_songs_v2.csv")

def extract_links(html: str, pattern: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("a"):
        href = a.get("href")
        if href and pattern in href and href.startswith("http"):
            links.append(href)
        elif href and pattern in href and href.startswith("/"):
            links.append("https://www.tamil2lyrics.com" + href)
    return list(set(links))

def fetch_html(url: str) -> str:
    print(f"Fetching: {url}")
    try:
        response = httpx.get(url, headers={'User-Agent': 'Mozilla/5.0'}, follow_redirects=True, timeout=10.0)
        response.raise_for_status()
        time.sleep(1) # Be polite
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""

def process_movie_page(url: str) -> list[str]:
    html = fetch_html(url)
    if not html: return []
    # Song links usually have /lyrics/ in them
    links = extract_links(html, "/lyrics/")
    song_links = [link for link in links if re.match(r'^https://www\.tamil2lyrics\.com/lyrics/[^/]+/$', link)]
    return song_links

def scrape_song(url: str) -> dict:
    html = fetch_html(url)
    if not html: return None
    soup = BeautifulSoup(html, "html.parser")
    
    # Very basic fallback extractions
    title = soup.title.string.split("Lyrics")[0].strip() if soup.title else "Unknown Title"
    title = title.replace("Song", "").strip()
    
    movie = ""
    year = ""
    singers = ""
    lyricist = ""
    composer = ""
    
    # Try to find metadata table or list. tamil2lyrics usually has it in a div or p
    # Or in the title, e.g. "Ponniyin Selvan - Part 1"
    # Just setting movie from title or leaving blank to be refined later
    if "-" in title:
        parts = title.split("-")
        movie = parts[-1].strip()
        title = parts[0].strip()
        
    # Extract English lyrics (tanglish). tamil2lyrics usually puts Tamil and English in <p> tags
    lyrics = ""
    ps = soup.find_all('p')
    english_ps = []
    for p in ps:
        text = p.get_text(separator='\n', strip=True)
        # Skip disclaimer text
        if "Disclaimer" in text or "All rights reserved" in text or "tamil2lyrics" in text.lower():
            continue
        
        # Check if the text contains mostly English characters and is long enough
        if re.search(r'[a-zA-Z]{5,}', text) and len(text) > 20:
            english_ps.append(text)
            
    # Sometimes it has duplicate paragraphs (Tamil then English then Tamil).
    # We just grab all English-looking paragraphs.
    lyrics = "\n".join(english_ps)
        
    # Clean up lyrics
    lines = lyrics.split('\n')
    cleaned_lines = [l.strip() for l in lines if l.strip()]
    lyrics = "\n".join(cleaned_lines)
    lyrics = re.sub(r'[\r\n]+', '\n', lyrics)
    lyrics = lyrics.strip()
    
    if not lyrics:
        print(f"  Warning: No Tanglish lyrics found for {title}")
        return None
        
    return {
        "title": title,
        "movie": movie,
        "year": year,
        "singers": singers,
        "lyricist": lyricist,
        "composer": composer,
        "mood": "",
        "themes": "",
        "lyrics": lyrics,
        "source_url": url
    }

def main():
    if not os.path.exists(URLS_FILE):
        print(f"Please create {URLS_FILE} and add URLs.")
        return
        
    with open(URLS_FILE, 'r', encoding='utf-8') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        
    print(f"Loaded {len(urls)} starting URLs.")
    
    song_urls = set()
    for url in urls:
        if "/movies/" in url:
            print(f"Processing Movie Page: {url}", flush=True)
            songs = process_movie_page(url)
            song_urls.update(songs)
        elif "/lyrics/" in url:
            print(f"Direct Song URL: {url}", flush=True)
            song_urls.add(url)
            
    print(f"Found {len(song_urls)} unique song URLs to scrape.")
    
    # Read existing IDs to auto-increment
    existing_ids = []
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, 'r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('id') and row['id'].isdigit():
                    existing_ids.append(int(row['id']))
    
    next_id = max(existing_ids) + 1 if existing_ids else 1
    
    # Append to CSV
    fieldnames = ['id', 'title', 'movie', 'year', 'singers', 'lyricist', 'composer', 'mood', 'themes', 'lyrics', 'source_url']
    
    with open(OUTPUT_CSV, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # If file is empty, write header
        if next_id == 1:
            writer.writeheader()
            
        success_count = 0
        for i, url in enumerate(song_urls):
            print(f"[{i+1}/{len(song_urls)}] Scraping Song: {url}")
            song_data = scrape_song(url)
            if song_data:
                song_data['id'] = next_id
                writer.writerow(song_data)
                csvfile.flush()
                next_id += 1
                success_count += 1
                
        print(f"Successfully scraped and appended {success_count} songs to {OUTPUT_CSV}.")

if __name__ == "__main__":
    main()
