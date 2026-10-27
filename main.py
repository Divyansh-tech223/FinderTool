import os
import requests
import time
import random
import json
from bs4 import BeautifulSoup
import ollama

# --- CONFIGURATION ---
OLLAMA_MODEL = "dolphin-2.9-llama3"
GOOGLE_CREDS_FILE = ".devcontainer/google_creds.json" # Place your Google JSON here
DOCUMENT_ID = "YOUR_GOOGLE_DOC_ID_HERE" 
# If using local Wi-Fi check, set this to your Ngrok/LAN IP:
LOCAL_CHECK_ENDPOINT = "http://localhost:8000/check" 

def scrape_youtube(query="fresh free proxy list 2026"):
    """Scrapes YouTube search results for text containing proxy links."""
    url = f"https://youtube.com/results?search_query={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Get all visible text, limiting context size for LLM efficiency
        return soup.get_text()[:4000]
    except Exception as e:
        print(f"Scrape Error: {e}")
        return ""

def extract_proxies(raw_text):
    """Uses Dolphin-2.9-Llama3 to extract only valid proxy links."""
    prompt = f"""
    Analyze the following raw text and extract ALL proxy links (SOCKS5, HTTP, VMess, V2Ray, Shadowsocks).
    Return ONLY the raw links, one per line. No markdown, no explanations, no quotes.
    
    Text:
    {raw_text}
    """
    try:
        # Connect to local Ollama instance running in the codespace
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{'role': 'user', 'content': prompt}])
        extracted = response['message']['content'].strip().split('\n')
        # Filter out empty lines
        return [p.strip() for p in extracted if p.strip()]
    except Exception as e:
        print(f"LLM Extraction Error: {e}")
        return []

def check_unblocked(proxies):
    """Checks if proxies are actually working/unblocked on the current network."""
    working = []
    for proxy in proxies:
        # Clean protocol prefix if missing for standard http/https check
        clean_proxy = proxy
        if not any(proxy.startswith(p) for p in ['http://', 'https://', 'socks5://']):
            clean_proxy = f"http://{proxy}"
            
        try:
            # Check against a reliable endpoint
            resp = requests.get("https://httpbin.org/ip", proxies={"http": clean_proxy, "https": clean_proxy}, timeout=5)
            if resp.status_code == 200:
                working.append(proxy)
                time.sleep(random.uniform(1, 3)) # Anti-ban delay
        except:
            pass
    return working

def update_google_doc(links):
    """Updates the specified Google Doc with the new list."""
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    
    try:
        creds = Credentials.from_service_account_file(GOOGLE_CREDS_FILE)
        service = build('docs', 'v1', credentials=creds)
        
        # Insert at the beginning
        request = {
            'insertText': {
                'location': {'index': 1},
                'text': "\n".join(links) + "\n---\n"
            }
        }
        service.documents().batchUpdate(documentId=DOCUMENT_ID, body={'requests': [request]}).execute()
        print(f"Updated Google Doc with {len(links)} proxies.")
    except Exception as e:
        print(f"Google Docs Error: {e}")

def main():
    print("🚀 Starting Proxy Automation...")
    
    # 1. Scrape
    print("1️⃣ Scraping YouTube...")
    raw_data = scrape_youtube()
    
    # 2. Extract with Local AI
    print("2️⃣ Extracting Proxies with Dolphin-2.9...")
    raw_proxies = extract_proxies(raw_data)
    print(f"   Found {len(raw_proxies)} potential proxies.")
    
    # 3. Check Unblocked Status
    print("3️⃣ Checking Unblocked Status...")
    working_proxies = check_unblocked(raw_proxies)
    print(f"   ✅ Working Proxies: {len(working_proxies)}")
    
    # 4. Update Docs
    if working_proxies:
        update_google_doc(working_proxies)
    else:
        print("No working proxies found.")
        
    # 5. Shutdown Codespace to save credits
    print("🛑 Shutting down Codespace...")
    os.system("gh codespace stop")

if __name__ == "__main__":
    main()
