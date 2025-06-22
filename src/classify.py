import logging
import json
import boto3
import re

def classify_message_type(data,config):
    try:
        # Initialize Bedrock client
        client = boto3.client("bedrock-runtime", region_name=config["bedrock"]["region"])
        model_id = config["bedrock"]["classification_model"]
        label_categories = config["type_classification"]["labels"]
        all_labels = [label for group in label_categories.values() for label in group]
        label_list = ", ".join(all_labels)
        # Prompt asking for clean JSON list only
        prompt = (
            "You are a classification model for vendor emails.\n"
            f"Classify the email into one or more of the following types:\n{label_list}.\n"
            "Return only a valid JSON list of matching labels, with no explanation or extra text.\n\n"
            f"Email content:\n{data['text']}"
        )

        # Send request to Claude via Bedrock
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

        # Claude response: list of dicts with 'text'
        if isinstance(parsed, list) and parsed and "text" in parsed[0]:
            raw_text = parsed[0]["text"]
            logging.debug(f"LLM raw content: {repr(raw_text)}")

            try:
                labels = json.loads(raw_text)  # <- THIS is now the only decoding needed
            except Exception as e:
                logging.error(f"❌ Failed to decode JSON from text: {e}")
                labels = []

        elif isinstance(parsed, dict) and "content" in parsed:
            content = parsed['content'][0]["text"]
            logging.debug(f"LLM raw content: {repr(content)}")
            try:
                # Fix malformed JSON by removing trailing brackets and extra whitespace
                if isinstance(content, str):
                    # Clean up common LLM JSON formatting issues
                    content = content.strip()
                    # Remove any trailing brackets after the JSON array
                    if content.endswith(']') and content.count('[') < content.count(']'):
                        content = content[:content.rindex(']')+1]
                    labels = json.loads(content)
                else:
                    labels = content
            except Exception as e:
                logging.error(f"❌ Failed to decode fallback content: {e}")
                # Try more aggressive JSON repair if standard parsing fails
                try:
                    # Extract what looks like a JSON array using regex
                    match = re.search(r'\[(.*?)\]', content)
                    if match:
                        array_content = match.group(0)
                        labels = json.loads(array_content)
                    else:
                        labels = []
                except:
                    labels = []

        else:
            raise ValueError(f"Unsupported response format: {parsed}")

        # Final validation
        if isinstance(labels, list) and all(isinstance(x, str) for x in labels):
            label_string = ", ".join(labels)
            logging.info(f"✅ Classified labels: {label_string}")
            return labels
        else:
            raise ValueError(f"Parsed labels are not valid: {labels}")

    except Exception as e:
        logging.error(f"❌ Classification failed: {str(e)}")
        return "unknown"
        
    

def extract_dates(data, config):
    try:
        client = boto3.client("bedrock-runtime", region_name=config["bedrock"]["region"])
        model_id = config["bedrock"]["classification_model"]
        
        prompt = (
            "Extract important dates from this email. Look for:\n"
            "- Event dates (conferences, webinars, workshops, hands-on labs)\n"
            "- Registration deadlines\n"
            "- Expiration dates for offers\n"
            "- Early bird deadlines\n"
            "- Session dates and times\n\n"
            "Convert all dates to YYYY-MM-DD format. Return only valid JSON:\n"
            '{"event_date": "YYYY-MM-DD", "registration_deadline": "YYYY-MM-DD", "expiration_date": "YYYY-MM-DD"}\n'
            "Use null for dates not found.\n\n"
            f"Email content:\n{data['text'][:2000]}"
        )

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 200,
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

        if isinstance(parsed, dict) and "content" in parsed:
            content = parsed['content'][0]["text"]
            logging.debug(f"Raw date extraction content: {content}")
            try:
                # Clean up the content before parsing
                content = content.strip()
                if content.startswith('```json'):
                    content = content.replace('```json', '').replace('```', '').strip()
                dates = json.loads(content)
                logging.info(f"✅ Extracted dates: {dates}")
                return dates
            except Exception as e:
                logging.error(f"❌ Failed to parse dates JSON: {content}, error: {e}")
                # Try to extract dates with regex as fallback
                import re
                date_pattern = r'\b(\d{4}-\d{2}-\d{2})\b'
                found_dates = re.findall(date_pattern, content)
                if found_dates:
                    return {"event_date": found_dates[0], "registration_deadline": None, "expiration_date": None}
                return {"event_date": None, "registration_deadline": None, "expiration_date": None}
        
        return {"event_date": None, "registration_deadline": None, "expiration_date": None}

    except Exception as e:
        logging.error(f"❌ Date extraction failed: {str(e)}")
        return {"event_date": None, "registration_deadline": None, "expiration_date": None}

def classify_message_products(data,config):
    try:
        # Initialize Bedrock client
        client = boto3.client("bedrock-runtime", region_name=config["bedrock"]["region"])
        model_id = config["bedrock"]["classification_model"]
        vendor = (data.get("vendor") or "unknown").lower()
        vendor_products = config["product_classification"]["vendors"].get(vendor, [])
        product_list = ", ".join(vendor_products)
        # Prompt asking for clean JSON list only
        if vendor_products:
            hint_text = f"Try to identify product names discussed in this email. These might include (but are not limited to):\n{product_list}"
        else:
            hint_text = "Try to identify product names discussed in this email."

        prompt = (
            "You are an AI email analyst helping categorize content.\n"
            f"The vendor mentioned is: {vendor}.\n"
            f"{hint_text}\n"
            "Return only a valid JSON list of product names mentioned in the email. No explanation, no extra formatting.\n\n"
            f"Email content:\n{data['text']}"
        )

        # Send request to Claude via Bedrock
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

        # Claude response: list of dicts with 'text'
        if isinstance(parsed, list) and parsed and "text" in parsed[0]:
            raw_text = parsed[0]["text"]
            logging.debug(f"LLM raw content: {repr(raw_text)}")

            try:
                labels = json.loads(raw_text)  # <- THIS is now the only decoding needed
            except Exception as e:
                logging.error(f"❌ Failed to decode JSON from text: {e}")
                labels = []

        elif isinstance(parsed, dict) and "content" in parsed:
            content = parsed['content'][0]["text"]
            logging.debug(f"LLM raw content: {repr(content)}")
            try:
                # Fix malformed JSON by removing trailing brackets and extra whitespace
                if isinstance(content, str):
                    # Clean up common LLM JSON formatting issues
                    content = content.strip()
                    # Remove any trailing brackets after the JSON array
                    if content.endswith(']') and content.count('[') < content.count(']'):
                        content = content[:content.rindex(']')+1]
                    labels = json.loads(content)
                else:
                    labels = content
            except Exception as e:
                logging.error(f"❌ Failed to decode fallback content: {e}")
                # Try more aggressive JSON repair if standard parsing fails
                try:
                    # Extract what looks like a JSON array using regex
                    match = re.search(r'\[(.*?)\]', content)
                    if match:
                        array_content = match.group(0)
                        labels = json.loads(array_content)
                    else:
                        labels = []
                except:
                    labels = []

        else:
            raise ValueError(f"Unsupported response format: {parsed}")

        # Final validation
        if isinstance(labels, list) and all(isinstance(x, str) for x in labels):
            label_string = ", ".join(labels)
            logging.info(f"✅ Classified labels: {label_string}")
            return labels
        else:
            raise ValueError(f"Parsed labels are not valid: {labels}")

    except Exception as e:
        logging.error(f"❌ Classification failed: {str(e)}")
        return "unknown"

def label_content(data, config):
    type_classification = classify_message_type(data, config)
    product_classification = classify_message_products(data, config)
    extracted_dates = extract_dates(data, config)
    
    result = {
        "text": data.get("text"),
        "vendor": data.get("vendor"),
        "product": product_classification,
        "date": data.get("received_at"),
        "type": type_classification
    }
    
    # Add extracted dates to the result
    result.update(extracted_dates)
    
    return result