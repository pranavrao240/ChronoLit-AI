import re
from typing import List, Dict, Any

def relevance_score(sentence: str) -> int:
    """Calculates relevance score based on temporal anchors and milestone verbs."""
    score = 0
    if any(ch.isdigit() for ch in sentence):
        score += 2
        
    important_words = [
        "born", "died", "published", "founded",
        "appointed", "elected", "established",
        "war", "battle", "married", "graduated",
        "invented", "discovered", "awarded"
    ]
    s_lower = sentence.lower()
    score += sum(1 for word in important_words if word in s_lower)
    return score

def rank_candidates(sentences: List[str]) -> List[str]:
    """Ranks event candidates by relevance score."""
    return sorted(sentences, key=relevance_score, reverse=True)

def generate_summary(events: List[Dict[str, Any]], max_items: int = 10) -> List[str]:
    """
    Generates a concise chronological summary from the extracted events.
    Prioritizes dated, high-relevance milestones while preventing duplicates.
    """
    
    dated_events = [e for e in events if e.get("date") is not None]
    undated_events = [e for e in events if e.get("date") is None]
    
    
    dated_events.sort(key=lambda x: x["date"])
    
    
    selected = []
    seen_years = set()
    
    
    for event in dated_events:
        yr = event["date"].year
        
        if yr not in seen_years or len(selected) < max_items // 2:
            selected.append(event)
            seen_years.add(yr)
            if len(selected) >= max_items:
                break
                
    if len(selected) < max_items:
        for event in dated_events:
            if event not in selected:
                selected.append(event)
                if len(selected) >= max_items:
                    break
                    
    if len(selected) < max_items:
        for event in undated_events:
            selected.append(event)
            if len(selected) >= max_items:
                break

    lines = []
    for event in selected:
        txt = event["text"]
        
        if len(txt) > 220:
            txt = txt[:217] + "..."
        if event.get("date"):
            year = event["date"].year
            lines.append(f"{year}: {txt}")
        else:
            lines.append(f"Date unknown: {txt}")
            
    return lines
