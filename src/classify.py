import logging
import json
import boto3
import re

def classify_message_type(data,config):
    try:
        from graph_db_consolidated import get_email_types_from_neo4j
        
        # Initialize Bedrock client
        client = boto3.client("bedrock-runtime", region_name=config["bedrock"]["region"])
        model_id = config["bedrock"]["classification_model"]
        
        # Get labels from Neo4j instead of config
        all_labels = get_email_types_from_neo4j()
        if not all_labels:
            logging.warning("No email types found in Neo4j, using fallback")
            all_labels = ["announcement", "event", "webinar", "product update", "security", "vulnerability"]
            
        label_list = ", ".join(all_labels)
        # Enhanced prompt for comprehensive classification
        prompt = (
            "You are a classification model for vendor emails.\n"
            f"Classify the email and provide a JSON response with:\n"
            "{\n"
            "  \"types\": [\"type1\", \"type2\"],\n"
            "  \"sentiment\": \"positive|neutral|negative\",\n"
            "  \"urgency\": \"low|medium|high|critical\",\n"
            "  \"confidence\": 0.85\n"
            "}\n\n"
            f"Available types: {label_list}\n\n"
            "Instructions:\n"
            "- types: Select matching email types\n"
            "- sentiment: positive (announcements/features), negative (issues/vulnerabilities), neutral (informational)\n"
            "- urgency: critical (security alerts), high (breaking changes), medium (updates), low (marketing)\n"
            "- confidence: Rate classification confidence 0.0-1.0\n\n"
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

        # Final validation - now expecting dict with types, sentiment, urgency, confidence
        if isinstance(labels, dict) and "types" in labels:
            logging.info(f"✅ Enhanced classification: {labels}")
            return labels
        elif isinstance(labels, list) and all(isinstance(x, str) for x in labels):
            # Fallback for old format
            result = {"types": labels, "sentiment": "neutral", "urgency": "medium", "confidence": 0.5}
            logging.info(f"✅ Fallback classification: {result}")
            return result
        else:
            raise ValueError(f"Parsed labels are not valid: {labels}")

    except Exception as e:
        logging.error(f"❌ Classification failed: {str(e)}")
        return {"types": ["unknown"], "sentiment": "neutral", "urgency": "medium", "confidence": 0.0}
        
    

def extract_dates(data, config):
    import re
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
                
                # Extract JSON from content that might have extra text
                json_match = re.search(r'\{[^{}]*\}', content)
                if json_match:
                    json_str = json_match.group(0)
                    dates = json.loads(json_str)
                else:
                    dates = json.loads(content)
                logging.info(f"✅ Extracted dates: {dates}")
                return dates
            except Exception as e:
                logging.error(f"❌ Failed to parse dates JSON: {content}, error: {e}")
                # Try to extract dates with regex as fallback
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
        from graph_db_consolidated import get_vendor_products_from_neo4j
        
        # Initialize Bedrock client
        client = boto3.client("bedrock-runtime", region_name=config["bedrock"]["region"])
        model_id = config["bedrock"]["classification_model"]
        vendor = (data.get("vendor") or "unknown").lower()
        
        # Get vendor products from Neo4j instead of config
        vendor_products = get_vendor_products_from_neo4j(vendor)
        
        if vendor_products:
            product_list = ", ".join(vendor_products)
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
    
    # Handle enhanced classification format
    if isinstance(type_classification, dict):
        result = {
            "text": data.get("text"),
            "vendor": data.get("vendor"),
            "product": product_classification,
            "date": data.get("received_at"),
            "type": type_classification.get("types", ["unknown"]),
            "sentiment": type_classification.get("sentiment", "neutral"),
            "urgency": type_classification.get("urgency", "medium"),
            "confidence": type_classification.get("confidence", 0.5)
        }
    else:
        # Fallback for old format
        result = {
            "text": data.get("text"),
            "vendor": data.get("vendor"),
            "product": product_classification,
            "date": data.get("received_at"),
            "type": type_classification if isinstance(type_classification, list) else [type_classification],
            "sentiment": "neutral",
            "urgency": "medium",
            "confidence": 0.5
        }
    
    # Add extracted dates to the result
    result.update(extracted_dates)
    
    return result