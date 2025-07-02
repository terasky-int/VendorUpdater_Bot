"""
Human-in-the-middle debugging module for step-by-step validation
"""

import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime

def wait_for_user_input(step_name: str, input_data: Any, output_data: Any, email_id: str) -> bool:
    """
    Display step information and wait for user validation
    Returns True to continue, False to stop processing
    """
    print("\n" + "="*80)
    print(f"🔍 HUMAN DEBUG - Step: {step_name}")
    print(f"📧 Email ID: {email_id}")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    print("="*80)
    
    # Display input data
    print("\n📥 INPUT:")
    print("-" * 40)
    if isinstance(input_data, dict):
        for key, value in input_data.items():
            if isinstance(value, str) and len(value) > 200:
                print(f"{key}: {value[:200]}... (truncated)")
            else:
                print(f"{key}: {value}")
    else:
        print(str(input_data)[:500] + ("..." if len(str(input_data)) > 500 else ""))
    
    # Display output data
    print("\n📤 OUTPUT:")
    print("-" * 40)
    if isinstance(output_data, dict):
        for key, value in output_data.items():
            if isinstance(value, str) and len(value) > 200:
                print(f"{key}: {value[:200]}... (truncated)")
            elif isinstance(value, list) and len(value) > 5:
                print(f"{key}: [{', '.join(map(str, value[:5]))}...] ({len(value)} items)")
            else:
                print(f"{key}: {value}")
    elif isinstance(output_data, list):
        print(f"List with {len(output_data)} items:")
        for i, item in enumerate(output_data[:3]):
            print(f"  [{i}]: {str(item)[:100]}{'...' if len(str(item)) > 100 else ''}")
        if len(output_data) > 3:
            print(f"  ... and {len(output_data) - 3} more items")
    else:
        print(str(output_data)[:500] + ("..." if len(str(output_data)) > 500 else ""))
    
    print("\n" + "="*80)
    
    while True:
        choice = input("Continue? (y/n/s/q): ").lower().strip()
        if choice in ['y', 'yes', '']:
            return True
        elif choice in ['n', 'no']:
            print("❌ Skipping this email...")
            return False
        elif choice in ['s', 'save']:
            save_debug_data(step_name, input_data, output_data, email_id)
            print("💾 Debug data saved!")
            continue
        elif choice in ['q', 'quit']:
            print("🛑 Stopping pipeline...")
            exit(0)
        else:
            print("Please enter: y (yes), n (no), s (save), or q (quit)")

def save_debug_data(step_name: str, input_data: Any, output_data: Any, email_id: str):
    """Save debug data to file for later analysis"""
    import os
    
    debug_dir = "logs/debug_data"
    os.makedirs(debug_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{debug_dir}/{email_id}_{step_name}_{timestamp}.json"
    
    debug_data = {
        "timestamp": datetime.now().isoformat(),
        "email_id": email_id,
        "step_name": step_name,
        "input_data": serialize_for_json(input_data),
        "output_data": serialize_for_json(output_data)
    }
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(debug_data, f, indent=2, ensure_ascii=False)
        logging.info(f"Debug data saved to {filename}")
    except Exception as e:
        logging.error(f"Failed to save debug data: {e}")

def serialize_for_json(data: Any) -> Any:
    """Convert data to JSON-serializable format"""
    if isinstance(data, dict):
        return {k: serialize_for_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_for_json(item) for item in data]
    elif isinstance(data, (str, int, float, bool)) or data is None:
        return data
    else:
        return str(data)

def debug_step(step_name: str, email_id: str, config: Dict):
    """
    Decorator for debugging pipeline steps
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Check if human debugging is enabled
            if not config.get("debug", {}).get("human_in_the_middle", False):
                return func(*args, **kwargs)
            
            # Capture input
            input_data = {
                "args": args,
                "kwargs": kwargs
            }
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Show debug info and wait for user input
            continue_processing = wait_for_user_input(
                step_name=step_name,
                input_data=input_data,
                output_data=result,
                email_id=email_id
            )
            
            if not continue_processing:
                raise StopIteration(f"User chose to skip processing at step: {step_name}")
            
            return result
        return wrapper
    return decorator