import os
import requests
import time
import random
from bs4 import BeautifulSoup
import ollama

# --- CONFIGURATION ---
OLLAMA_MODEL = "dolphin-2.9-llama3"
GOOGLE_CREDS_FILE = ".devcontainer/google_creds.json" 
DOCUMENT_ID = "YOUR_GOOGLE_DOC_ID_HERE" # Replace with your actual Document ID

# PASTE YOUR APPS SCRIPT WEB APP URL HERE (From Step 1)
APPS_SCRIPT_URL = "PASTE_YOUR_WEB_APP_URL_HERE" 

def scrape_youtube(query="fresh free proxy list 2026"):
    """Scrapes YouTube search results for text containing proxy links."""
    url = f"https://youtube.com/results?search_query={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
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
        response = ollama.chat(model=OLLAMA_MODEL, messages=[{'role': 'user', 'content': prompt}])
        extracted = response['message']['content'].strip().split('\n')
        return [p.strip() for p in extracted if p.strip()]
    except Exception as e:
        print(f"LLM Extraction Error: {e}")
        return []

def check_unblocked(proxies):
    """Checks if proxies are actually working/unblocked on the current network."""
    working = []
    for proxy in proxies:
        clean_proxy = proxy
        if not any(proxy.startswith(p) for p in ['http://', 'https://', 'socks5://']):
            clean_proxy = f"http://{proxy}"
            
        try:
            resp = requests.get("https://httpbin.org/ip", proxies={"http": clean_proxy, "https": clean_proxy}, timeout=5)
            if resp.status_code == 200:
                working.append(proxy)
                time.sleep(random.uniform(1, 3)) # Anti-ban delay
        except:
            pass
    return working

def update_google_doc(links):
    """Sends links to your Google Apps Script bridge."""
    data = {"links": "\n".join(links)}
    try:
        response = requests.post(APPS_SCRIPT_URL, data=data)
        if response.text == "Success":
            print(f"✅ Updated Google Doc with {len(links)} proxies via Bridge!")
        else:
            print(f"❌ Bridge Error: {response.text}")
    except Exception as e:
        print(f"Bridge Connection Error: {e}")

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
    
    # 4. Update Docs via Bridge
    if working_proxies:
        update_google_doc(working_proxies)
    else:
        print("No working proxies found.")
        
    # 5. Shutdown Codespace to save credits
    print("🛑 Shutting down Codespace...")
    os.system("gh codespace stop")

if __name__ == "__main__":
    main()
