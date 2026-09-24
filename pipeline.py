"""
pipeline.py - ChronoLit AI End-to-End Orchestrator

Integrates:
1. Source Collection (Wikipedia API)
2. Text Cleaning & Sentence Boundary Detection
3. Event Candidate Filtering (Action Verbs & Temporal Markers)
4. Date Extraction & Chronological Sorting
5. Unsupervised Semantic Clustering (Sentence Transformers + DBSCAN, with TF-IDF fallback)
6. Summary Generation
7. SQLite Persistence
"""

import logging
from typing import Dict, Any, List

from source_collector import get_wikipedia_text, get_wikipedia_url
from nlp_processor import split_sentences, event_candidates
from timeline import make_event, sort_events
from summarizer import generate_summary, rank_candidates
from database import save_topic, save_events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ChronoLitPipeline")

# Lazy-loaded embedding model to avoid startup slowdowns
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            # pyrefly: ignore [missing-import]
            from sentence_transformers import SentenceTransformer
            logger.info("Loading SentenceTransformer 'all-MiniLM-L6-v2'...")
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.warning(f"Could not load SentenceTransformer: {e}. Will use TF-IDF fallback.")
            _embedding_model = False
    return _embedding_model

def cluster_events(events: List[Dict[str, Any]]) -> List[int]:
    """
    Groups semantically related events using unsupervised clustering.
    Uses DBSCAN with cosine distance on embeddings.
    Falls back gracefully to TF-IDF clustering if sentence-transformers is unavailable.
    """
    texts = [e["text"] for e in events]
    n_samples = len(texts)
    if n_samples < 2:
        return [0] * n_samples

    model = get_embedding_model()
    
    # 1. Try Sentence Transformers + DBSCAN
    if model:
        try:
            from sklearn.cluster import DBSCAN
            vectors = model.encode(texts, normalize_embeddings=True)
            clustering = DBSCAN(eps=0.38, min_samples=2, metric="cosine")
            labels = clustering.fit_predict(vectors)
            return labels.tolist()
        except Exception as e:
            logger.warning(f"SentenceTransformer clustering failed: {e}. Falling back to TF-IDF.")

    # 2. Fallback: TF-IDF + DBSCAN or Mini-KMeans
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import DBSCAN
        vectorizer = TfidfVectorizer(max_features=500, stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(texts)
        clustering = DBSCAN(eps=0.65, min_samples=2, metric="cosine")
        labels = clustering.fit_predict(tfidf_matrix.toarray())
        return labels.tolist()
    except Exception as e:
        logger.warning(f"Fallback clustering failed: {e}. Assigning cluster 0.")
        return [0] * n_samples

def run_pipeline(topic: str, max_events: int = 35) -> Dict[str, Any]:
    """
    Executes the full ChronoLit extraction, clustering, ordering, and storage pipeline.
    """
    if not topic or not topic.strip():
        raise ValueError("Topic cannot be empty.")
    
    cleaned_topic = topic.strip()
    logger.info(f"Starting ChronoLit extraction for topic: '{cleaned_topic}'")

    # Step 1: Collect text & source URL
    text = get_wikipedia_text(cleaned_topic)
    url = get_wikipedia_url(cleaned_topic)

    # Step 2: NLP Sentence splitting & Event Candidate Filtering
    sentences = split_sentences(text)
    if not sentences:
        raise ValueError(f"No textual sentences could be extracted for '{cleaned_topic}'.")

    candidates = event_candidates(sentences)
    if not candidates:
        # If strict filtering returned nothing, rank all sentences
        candidates = rank_candidates(sentences)[:max_events]
    elif len(candidates) > max_events * 2:
        # Prioritize top candidate sentences
        candidates = rank_candidates(candidates)[:max_events * 2]

    # Step 3: Date extraction & Event representation
    events = [make_event(s) for s in candidates]

    # Step 4: Semantic Clustering
    labels = cluster_events(events)
    for event, label in zip(events, labels):
        event["cluster"] = int(label)

    # Step 5: Chronological Sorting
    sorted_events = sort_events(events)

    # Limit to requested volume for crisp timeline rendering
    timeline_subset = sorted_events[:max_events]

    # Step 6: Database Persistence
    topic_id = save_topic(cleaned_topic, url)
    save_events(topic_id, timeline_subset)

    # Step 7: Summary generation
    summary_lines = generate_summary(timeline_subset, max_items=10)

    # Format JSON-ready output
    formatted_events = []
    cluster_counts = {}
    for e in timeline_subset:
        c_id = e.get("cluster", -1)
        cluster_counts[c_id] = cluster_counts.get(c_id, 0) + 1
        
        formatted_events.append({
            "date": e["date"].year if e.get("date") else None,
            "full_date": e["date"].strftime("%B %d, %Y") if (e.get("date") and e["date"].month != 1 and e["date"].day != 1) else None,
            "text": e["text"],
            "cluster": c_id
        })

    return {
        "topic_id": topic_id,
        "topic": cleaned_topic,
        "source": url,
        "summary": summary_lines,
        "total_extracted": len(formatted_events),
        "cluster_stats": cluster_counts,
        "events": formatted_events
    }
