import re
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import dateparser
except ImportError:
    dateparser = None

YEAR_RE = re.compile(r"\b(1[0-9]{3}|20[0-9]{2})\b")

MONTH_YEAR_RE = re.compile(r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+(1[0-9]{3}|20[0-9]{2})\b", re.IGNORECASE)

def extract_date(sentence: str) -> Optional[datetime]:
    """
    Extracts explicit temporal markers, prioritizing exact date/year anchors.
    Falls back to dateparser for natural language dates.
    """
    
    m = YEAR_RE.search(sentence)
    if m:
        try:
            year = int(m.group(1))
            
            if dateparser:
                m_rich = MONTH_YEAR_RE.search(sentence)
                if m_rich:
                    dt = dateparser.parse(m_rich.group(0))
                    if dt:
                        return dt
            return datetime(year, 1, 1)
        except Exception:
            pass

    
    if dateparser:
        try:
            dt = dateparser.parse(
                sentence,
                settings={
                    "PREFER_DAY_OF_MONTH": "first",
                    "DATE_ORDER": "DMY",
                    "REQUIRE_PARTS": ["year"]
                }
            )
            return dt
        except Exception:
            return None

    return None

def make_event(sentence: str) -> Dict[str, Any]:
    """Wraps text and extracted date into an event structure."""
    return {
        "text": sentence,
        "date": extract_date(sentence)
    }

def sort_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sorts events chronologically.
    Events with verified temporal anchors come first in chronological order,
    followed by undated events.
    """
    dated = [e for e in events if e.get("date") is not None]
    undated = [e for e in events if e.get("date") is None]
    
    dated.sort(key=lambda x: x["date"])
    return dated + undated
