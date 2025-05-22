import logging
import json
import boto3
import re

def label_content(data, config):
    try:
        # Initialize Bedrock client
        client = boto3.client("bedrock-runtime", region_name=config["bedrock"]["region"])
        model_id = config["bedrock"]["classification_model"]

        # Create prompt for classification
        prompt = (
            "You are a classification model for vendor emails.\n"
            "Classify the email into one or more of the following types:\n"
            "promo, event, webinar, announcement, vulnerability, patch, maintenance, support, product update, whitepaper.\n"
            "Return a JSON list of matching labels.\n\n"
            f"Email content:\n{data['text']}"
        )

        # Prepare request for Claude via Bedrock
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

        labels = []

        # Claude-style response: [{"type": "text", "text": "..."}]
        if isinstance(parsed, list) and parsed and isinstance(parsed[0], dict) and "text" in parsed[0]:
            raw_text = parsed[0]["text"]
            logging.debug(f"LLM raw content: {repr(raw_text)}")

            # Extract JSON-like label list from the text
            match = re.search(r"\[\s*\".*?\"\s*(?:,\s*\".*?\"\s*)*\]", raw_text, re.DOTALL)
            if match:
                labels = json.loads(match.group(0))
            else:
                raise ValueError(f"Could not extract label list from: {raw_text}")

        # Alt response: direct dict with a 'content' key
        elif isinstance(parsed, dict) and "content" in parsed:
            content = parsed["content"]
            logging.debug(f"LLM raw content: {repr(content)}")
            if isinstance(content, str):
                labels = json.loads(content)
            elif isinstance(content, list):
                labels = content
            else:
                raise ValueError(f"Unexpected format in 'content': {type(content)}")

        else:
            raise ValueError(f"Unsupported response format: {type(parsed)}")

        # Validate and return classification
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
            raise ValueError(f"Parsed labels are not valid: {labels}")

    except Exception as e:
        logging.error(f"❌ Classification failed: {str(e)}")
        return {
            "text": data.get("text", ""),
            "vendor": data.get("vendor", "unknown"),
            "product": data.get("product", "unknown"),
            "date": data.get("date", "1970-01-01"),
            "type": "unknown"
        }

# def label_content(data, config):
#     try:
#         client = boto3.client("bedrock-runtime", region_name=config["bedrock"]["region"])
#         model_id = config["bedrock"]["classification_model"]

#         prompt = (
#             "You are a classification model for vendor emails.\n"
#             "Based on this text, classify the email into one or more of the following types:\n"
#             "promo, event, webinar, announcement, vulnerability, patch, maintenance, support, product update, whitepaper.\n"
#             "Return a JSON list of matching labels.\n\n"
#             f"Email content:\n{data['text']}"
#         )

#         body = {
#             "anthropic_version": "bedrock-2023-05-31",
#             "max_tokens": 300,
#             "temperature": 0.0,
#             "messages": [{"role": "user", "content": prompt}]
#         }

#         response = client.invoke_model(
#             modelId=model_id,
#             body=json.dumps(body),
#             contentType="application/json",
#             accept="application/json"
#         )

#         response_body = response["body"].read().decode()
#         parsed = json.loads(response_body)
    
#         # Handle Claude-style response
#         if isinstance(parsed, list) and "text" in parsed[0]:
#             raw_text = parsed[0]["text"]
#             logging.debug(f"Claude response text: {repr(raw_text)}")

#             # Extract JSON array from within the text using regex
#             import re
#             match = re.search(r"\[\s*\".*?\"\s*(?:,\s*\".*?\"\s*)*\]", raw_text, re.DOTALL)
#             if match:
#                 labels = json.loads(match.group(0))
#             else:
#                 raise ValueError(f"Could not extract labels from: {raw_text}")

#         elif isinstance(parsed, dict) and "content" in parsed:
#             content = parsed["content"]
#             if isinstance(content, list):
#                 labels = content
#             elif isinstance(content, str):
#                 labels = json.loads(content)
#             else:
#                 raise ValueError(f"Unexpected content format: {type(content)}")
#             # Log the raw content for debugging    
#             logging.debug(f"LLM raw content: {repr(content)}")

#         else:
#             raise ValueError(f"Unexpected top-level format: {type(parsed)}")

        

#         if isinstance(labels, list) and all(isinstance(x, str) for x in labels):
#             label_string = ", ".join(labels)
#             logging.info(f"✅ Classified labels: {label_string}")
#             return {
#                 "text": data["text"],
#                 "vendor": data.get("vendor", "unknown"),
#                 "product": data.get("product", "unknown"),
#                 "date": data.get("date", "1970-01-01"),
#                 "type": label_string
#             }

#         else:
#             raise ValueError(f"Unexpected label format: {labels}")

#     except Exception as e:
#         logging.error(f"❌ Classification failed: {str(e)}")
#         return {
#             "text": data.get("text", ""),
#             "vendor": data.get("vendor", "unknown"),
#             "product": data.get("product", "unknown"),
#             "date": data.get("date", "1970-01-01"),
#             "type": "unknown"
#         }
