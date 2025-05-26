import json

def record_entry(email_id, chunks, classified_data, config):
    entry = {
        "email_id": email_id,
        "chunks": [chunk["chunk_id"] for chunk in chunks],
        "metadata": {
            "vendor": classified_data.get("vendor"),
            "product": classified_data.get("product"),
            "type": classified_data.get("type"),
            "date": classified_data.get("date"),
        }
    }

    manifest_path = config["storage"]["manifest_file"]
    with open(manifest_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")