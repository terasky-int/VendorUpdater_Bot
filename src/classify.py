import logging
import json
import boto3

def label_content(data, config):
    try:
        client = boto3.client("bedrock-runtime", region_name=config["bedrock"]["region"])
        model_id = config["bedrock"]["classification_model"]

        prompt = (
            "You are a classification model for vendor emails.\n"
            "Based on this text, classify the email into one or more of the following types:\n"
            "promo, event, webinar, announcement, vulnerability, patch, maintenance, support, product update, whitepaper.\n"
            "Return a JSON list of matching labels.\n\n"
            f"Email content:\n{data['text']}"
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 300,
            "temperature": 0.0,
            "messages": [{"role": "user", "content": prompt}]
        }

        response = client.invoke_model(
            modelId=model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json"
        )

        response_body = response["body"].read().decode()
        parsed = json.loads(response_body)

        # Assume Claude-like output:
        content = parsed["content"]
        labels = json.loads(content)  # Should be a JSON array

        if isinstance(labels, list) and all(isinstance(x, str) for x in labels):
            label_string = ", ".join(labels)
            logging.info(f"✅ Classified labels: {label_string}")
            return {
                "text": data["text"],
                "vendor": data.get("vendor", "unknown"),
                "product": data.get("product", "unknown"),
                "date": data.get("date", "1970-01-01"),
                "type": label_string
            }

        else:
            raise ValueError(f"Unexpected label format: {labels}")

    except Exception as e:
        logging.error(f"❌ Classification failed: {str(e)}")
        return {
            "text": data.get("text", ""),
            "vendor": data.get("vendor", "unknown"),
            "product": data.get("product", "unknown"),
            "date": data.get("date", "1970-01-01"),
            "type": "unknown"
        }
