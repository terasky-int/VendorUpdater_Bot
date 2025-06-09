"""
Simple utility to list vendor products from the configuration
"""

import sys
import os
import yaml
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def load_vendor_products():
    """Load vendor products from config file"""
    try:
        with open("config/config.yaml", "r") as f:
            config = yaml.safe_load(f)
        
        return config.get("product_classification", {}).get("vendors", {})
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return {}

def get_vendor_products(vendor_name):
    """Get products for a specific vendor"""
    vendor_products = load_vendor_products()
    
    # Case-insensitive vendor matching
    for vendor in vendor_products:
        if vendor_name.lower() in vendor.lower() or vendor.lower() in vendor_name.lower():
            return vendor, vendor_products[vendor]
    
    return None, []

def list_all_vendors():
    """List all vendors in the config"""
    vendor_products = load_vendor_products()
    return list(vendor_products.keys())

def main():
    """Main function"""
    print("Vendor Products Utility")
    print("Type 'exit' to quit\n")
    print("Commands:")
    print("- list vendors")
    print("- [vendor name] (to list products for that vendor)")
    
    while True:
        try:
            command = input("\nCommand: ")
            if command.lower() == "exit":
                break
            
            if command.lower() == "list vendors":
                vendors = list_all_vendors()
                print(f"\nAvailable vendors ({len(vendors)}):")
                for vendor in vendors:
                    print(f"- {vendor}")
            else:
                vendor, products = get_vendor_products(command)
                if vendor:
                    print(f"\n{vendor} products ({len(products)}):")
                    for product in products:
                        print(f"- {product}")
                else:
                    print(f"\nNo vendor found matching '{command}'")
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()