# Vendor-Product Relationship Validation

This document describes the enhanced relationship validation system for the VendorUpdater_Bot project, which addresses the issue of incorrect vendor-product associations in the graph database.

## Problem

The original implementation created relationships between vendors and products based solely on their co-occurrence in emails, leading to incorrect associations. For example, if a HashiCorp email mentioned Palo Alto products, those products would be incorrectly associated with HashiCorp.

## Solution

The enhanced system uses a tiered confidence approach:

1. **High Confidence**: Relationships validated against the config file
2. **Medium Confidence**: Relationships with strong textual evidence
3. **Low Confidence**: Relationships with weak textual evidence

## Implementation

### 1. Enhanced Graph Database Module (`graph_db_enhanced.py`)

- `validate_vendor_product()`: Validates relationships against the config file
- `analyze_text_for_relationships()`: Analyzes email text for relationship evidence
- `add_email_to_graph_enhanced()`: Creates relationships with confidence levels
- `cleanup_incorrect_relationships()`: Removes invalid relationships
- `get_vendor_products_by_confidence()`: Retrieves products by confidence level

### 2. Validation Tool (`Tests/tools/validate_relationships.py`)

- Shows products for a vendor grouped by confidence level
- Provides a command to clean up incorrect relationships
- Can be run as a standalone tool or integrated into the pipeline

## Usage

### Cleaning Up Existing Data

```
python -m Tests.tools.validate_relationships cleanup
```

This will:
1. Check all vendor-product relationships against the config file
2. Remove relationships that don't match any known vendor-product pairs

### Viewing Products by Confidence

```
python -m Tests.tools.validate_relationships hashicorp
```

This will show:
- HIGH CONFIDENCE: Products validated by the config file
- MEDIUM CONFIDENCE: Products with strong textual evidence
- LOW CONFIDENCE: Products with weak associations

### Integration

To use the enhanced system in the main application:

1. Replace `graph_db.py` with `graph_db_enhanced.py` or update the imports
2. Use `add_email_to_graph_enhanced()` instead of `add_email_to_graph()`
3. Use `get_vendor_products_by_confidence()` for product lookups

## Benefits

- **Data Quality**: Ensures relationships in the graph database are accurate
- **Confidence Levels**: Allows filtering by confidence when querying
- **Dynamic Discovery**: Still allows discovery of new relationships
- **Self-Improving**: Confidence increases as more evidence is gathered