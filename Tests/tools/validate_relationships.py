"""
Tool to validate and fix vendor-product relationships in the graph database
"""

import sys
import os
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from graph_db_enhanced import (
    cleanup_incorrect_relationships,
    get_vendor_products_by_confidence,
    CONFIDENCE_HIGH,
    CONFIDENCE_MEDIUM,
    CONFIDENCE_LOW
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def show_vendor_products_by_confidence(vendor_name):
    """Show products for a vendor grouped by confidence level"""
    print(f"\nProducts for vendor '{vendor_name}':")
    
    # Get high confidence products
    high_confidence = get_vendor_products_by_confidence(vendor_name, CONFIDENCE_HIGH)
    if high_confidence:
        print("\nHIGH CONFIDENCE (validated by config):")
        for product in high_confidence:
            print(f"- {product['product']}")
    else:
        print("\nNo high confidence products found.")
    
    # Get medium confidence products
    medium_confidence = get_vendor_products_by_confidence(vendor_name, CONFIDENCE_MEDIUM)
    medium_only = [p for p in medium_confidence if p['confidence'] == CONFIDENCE_MEDIUM]
    if medium_only:
        print("\nMEDIUM CONFIDENCE (strong textual evidence):")
        for product in medium_only:
            print(f"- {product['product']}")
    else:
        print("\nNo medium confidence products found.")
    
    # Get low confidence products
    low_confidence = get_vendor_products_by_confidence(vendor_name, CONFIDENCE_LOW)
    low_only = [p for p in low_confidence if p['confidence'] == CONFIDENCE_LOW]
    if low_only:
        print("\nLOW CONFIDENCE (weak association):")
        for product in low_only:
            print(f"- {product['product']}")
    else:
        print("\nNo low confidence products found.")

def main():
    """Main function"""
    print("Vendor-Product Relationship Validation Tool")
    print("------------------------------------------")
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "cleanup":
            print("\nCleaning up incorrect relationships...")
            cleanup_incorrect_relationships()
            print("Done!")
            return
        else:
            vendor = sys.argv[1]
            show_vendor_products_by_confidence(vendor)
            return
    
    print("\nOptions:")
    print("1. Show products by confidence level for a vendor")
    print("2. Clean up incorrect relationships")
    print("3. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-3): ")
            
            if choice == "1":
                vendor = input("Enter vendor name: ")
                show_vendor_products_by_confidence(vendor)
            elif choice == "2":
                print("\nCleaning up incorrect relationships...")
                cleanup_incorrect_relationships()
                print("Done!")
            elif choice == "3":
                break
            else:
                print("Invalid choice. Please try again.")
        
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"\nError: {e}")

if __name__ == "__main__":
    main()