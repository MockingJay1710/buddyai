# agent/modules/web_operations.py
import webbrowser
import urllib.parse

def open_url_in_browser(url: str):
    """Opens a given URL in the default web browser."""
    try:
        # Basic check for a common scheme, add http if missing for some inputs
        if not url.startswith(('http://', 'https://', 'file://')):
            url = 'http://' + url
        webbrowser.open_new_tab(url)
        return {"status": "success", "message": f"Attempted to open URL: {url}"}
    except Exception as e:
        return {"status": "error", "message": f"Failed to open URL '{url}': {e}"}

def search_web(query: str, engine: str = "google"):
    """
    Searches the web using a specified search engine (default: Google).
    Supported engines: "google", "duckduckgo", "bing".
    """
    base_urls = {
        "google": "https://www.google.com/search?q=",
        "duckduckgo": "https://duckduckgo.com/?q=",
        "bing": "https://www.bing.com/search?q="
    }
    try:
        if engine.lower() not in base_urls:
            return {"status": "error", "message": f"Unsupported search engine: {engine}. Supported: {list(base_urls.keys())}"}
        
        search_url = base_urls[engine.lower()] + urllib.parse.quote_plus(query)
        webbrowser.open_new_tab(search_url)
        return {"status": "success", "message": f"Searching for '{query}' on {engine}."}
    except Exception as e:
        return {"status": "error", "message": f"Failed to perform web search for '{query}': {e}"}

COMMANDS = {
    "web_open_url": open_url_in_browser,
    "web_search": search_web,
}