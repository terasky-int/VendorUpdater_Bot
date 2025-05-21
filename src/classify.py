import logging
import boto3
import json

def label_content(enriched_data, config):
    model_id = config['embedding']['model']
    client = boto3.client("bedrock-runtime")

    prompt = generate_prompt(enriched_data, config)

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 300,
        "temperature": 0.0,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        response = client.invoke_model(
            modelId=model_id,
            contentType="application/json",
            accept="application/json",
            body=json.dumps(body)
        )

        response_body = json.loads(response['body'].read())
        output = response_body["content"][0]["text"]
        labels = parse_labels_from_output(output)
        enriched_data["type"] = labels
        logging.info(f"Classified email: {labels}")
        return enriched_data

    except Exception as e:
        logging.error(f"Classification failed: {e}")
        enriched_data["type"] = []
        return enriched_data


def generate_prompt(data, config):
    example_labels = []
    for category in config['classification']['labels'].values():
        example_labels.extend(category)

    label_str = ", ".join(example_labels)
    text_sample = data['text'][:1000]  # Limit to first 1000 chars

    return (
        f"You are a classification model for vendor emails.\n"
        f"Based on this text, classify the email into one or more of the following types:\n"
        f"{label_str}.\n"
        f"Return a JSON list of matching labels.\n"
        f"\nEmail content:\n{text_sample}"
    )


def parse_labels_from_output(output):
    try:
        labels = json.loads(output)
        if isinstance(labels, list):
            return labels
        return [labels]
    except:
        return []