import re
import json

def fix_json_content(content):
    """Fix malformed JSON from LLM responses"""
    if not isinstance(content, str):
        return content
    
    content = content.strip()
    
    # Extract JSON object from content that might have extra text
    json_match = re.search(r'\{.*?\}', content, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except:
            pass
    
    # Fallback
    return {"types": ["unknown"], "sentiment": "neutral", "urgency": "medium", "confidence": 0.0}

# Test the function
test_content = '{\n  "types": ["event", "webinar", "announcement"],\n  "sentiment": "positive",\n  "urgency": "medium",\n  "confidence": 0.9\n}\n\n]'

result = fix_json_content(test_content)
print(result)