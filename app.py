import os
import io
import csv

# pyrefly: ignore [missing-import]
from flask import Flask, render_template, request, jsonify, Response
from database import init_db, get_all_topics, get_topic_timeline
from pipeline import run_pipeline

app = Flask(__name__)


init_db()

@app.route("/")
def home():
    """Renders the ChronoLit AI timeline interface."""
    return render_template("index.html")

@app.route("/api/timeline", methods=["POST"])
def timeline_api():
    """Generates an AI-assisted chronological timeline for the requested topic."""
    data = request.get_json(silent=True) or {}
    topic = data.get("topic", "").strip()
    
    if not topic:
        return jsonify({"error": "Topic is required. Please enter a valid name or event."}), 400

    try:
        result = run_pipeline(topic)
        return jsonify(result)
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as exc:
        return jsonify({"error": f"Internal Processing Error: {str(exc)}"}), 500

@app.route("/api/history", methods=["GET"])
def history_api():
    """Returns past searched topics from the SQLite database."""
    try:
        topics = get_all_topics()
        return jsonify({"topics": topics})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/timeline/<int:topic_id>", methods=["GET"])
def get_timeline_by_id(topic_id: int):
    """Retrieves an existing saved timeline from SQLite."""
    try:
        data = get_topic_timeline(topic_id)
        if not data:
            return jsonify({"error": "Topic not found in database."}), 404
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/export/<int:topic_id>", methods=["GET"])
def export_timeline(topic_id: int):
    """Exports the timeline in CSV or JSON format."""
    format_type = request.args.get("format", "csv").lower()
    data = get_topic_timeline(topic_id)
    if not data:
        return jsonify({"error": "Timeline not found."}), 404

    if format_type == "json":
        return jsonify(data)

    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Topic", "Year", "Cluster_ID", "Event_Text", "Source_URL"])
    for e in data.get("events", []):
        writer.writerow([data["topic"], e["date"] or "Unknown", e["cluster"], e["text"], data["source"]])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=timeline_{data['topic'].replace(' ', '_')}.csv"}
    )

if __name__ == "__main__":
    
    app.run(host="127.0.0.1", port=5000, debug=True)
