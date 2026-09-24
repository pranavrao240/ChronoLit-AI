import re
from typing import List


_nlp = None
try:
    # pyrefly: ignore [missing-import]
    import spacy
    try:
        _nlp = spacy.load("en_core_web_sm")
    except Exception:
        
        try:
            _nlp = spacy.blank("en")
            _nlp.add_pipe("sentencizer")
        except Exception:
            _nlp = None
except ImportError:
    _nlp = None

def clean_text(text: str) -> str:
    """Removes irregular whitespace, citation artifacts, and cleans text."""
    text = re.sub(r"\[\d+\]", "", text)  
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def split_sentences(text: str) -> List[str]:
    """
    Splits text into coherent sentences.
    Filters out fragments shorter than 35 characters.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []
        
    sentences = []
    if _nlp is not None:
        try:
            doc = _nlp(cleaned[:100000])  
            sentences = [s.text.strip() for s in doc.sents]
        except Exception:
            sentences = []
            
    if not sentences:
        
        raw_sents = re.split(r'(?<=[.!?])\s+(?=[A-Z0-9"\'])', cleaned)
        sentences = [s.strip() for s in raw_sents]
        
    return [s for s in sentences if len(s) >= 35]

def looks_like_event(sentence: str) -> bool:
    """
    Evaluates whether a sentence contains temporal anchors or action verbs
    indicative of biographical, historical, or literary milestones.
    """
    event_words = [
        "born", "died", "founded", "started", "ended",
        "married", "published", "released", "appointed",
        "elected", "war", "battle", "joined", "became",
        "established", "created", "moved", "graduated",
        "awarded", "invented", "discovered", "signed",
        "crowned", "reigned", "captured", "defeated",
        "assassinated", "resigned", "passed away"
    ]
    s = sentence.lower()
    has_year = bool(re.search(r"\b(1[0-9]{3}|20[0-9]{2})\b", sentence))
    return has_year or any(w in s for w in event_words)

def event_candidates(sentences: List[str]) -> List[str]:
    """Filters sentence collection down to likely historical/literary events."""
    return [s for s in sentences if looks_like_event(s)]
