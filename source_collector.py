import requests

# pyrefly: ignore [missing-import]
from bs4 import BeautifulSoup

WIKI_API = "https://en.wikipedia.org/w/api.php"

def get_wikipedia_text(topic: str) -> str:
    """
    Retrieves full-text content of a Wikipedia page using the mediawiki API.
    Cleans tags, scripts, styles, tables, and superscripts.
    """
    params = {
        "action": "parse",
        "page": topic,
        "prop": "text",
        "format": "json",
        "redirects": 1
    }
    response = requests.get(
        WIKI_API,
        params=params,
        timeout=15,
        headers={"User-Agent": "ChronoLitAI/1.0 (Educational Academic Project; contact@chronolit.edu)"}
    )
    response.raise_for_status()
    data = response.json()
    
    if "error" in data:
        search_params = {
            "action": "query",
            "list": "search",
            "srsearch": topic,
            "format": "json"
        }
        search_resp = requests.get(
            WIKI_API,
            params=search_params,
            timeout=15,
            headers={"User-Agent": "ChronoLitAI/1.0"}
        )
        search_data = search_resp.json()
        search_results = search_data.get("query", {}).get("search", [])
        if search_results:
            best_title = search_results[0]["title"]
            params["page"] = best_title
            retry_resp = requests.get(WIKI_API, params=params, timeout=15, headers={"User-Agent": "ChronoLitAI/1.0"})
            data = retry_resp.json()
            if "error" in data:
                raise ValueError(f"Wikipedia page not found for '{topic}'.")
        else:
            raise ValueError(f"Wikipedia page not found for '{topic}'.")
            
    html = data["parse"]["text"]["*"]
    soup = BeautifulSoup(html, "html.parser")
    
    for tag in soup(["script", "style", "table", "sup", "noscript", "header", "footer", "nav"]):
        tag.decompose()
        
    text = soup.get_text(" ", strip=True)
    return text

def get_wikipedia_url(topic: str) -> str:
    """Returns canonical Wikipedia URL for topic."""
    return "https://en.wikipedia.org/wiki/" + topic.strip().replace(" ", "_")
