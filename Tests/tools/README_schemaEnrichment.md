# Schema Enrichment Tool

Automatically enriches vendor Excel files with associated domains and aliases by analyzing existing email data.

## Features

- **Domain Extraction**: Analyzes sender email addresses to identify vendor domains
- **Alias Generation**: Uses multiple strategies to find vendor name variations:
  - Detected vendor variations from email processing
  - Company name variations from email content
  - Domain-based aliases
- **Smart Analysis**: Only processes vendors missing domain/alias data
- **Data-Driven**: Uses actual email data from ChromaDB for accurate results

## Usage

### 1. Create Sample Excel
```bash
cd Tests/tools
python create_sample_excel.py
```

### 2. Run Enrichment
```bash
python schemaEnrichment.py sample_vendors.xlsx
```

### 3. Custom Output
```bash
python schemaEnrichment.py input.xlsx --output enriched_vendors.xlsx
```

## Input Format

Excel file with columns:
- `id`: Unique identifier
- `name`: Vendor name
- `description`: Vendor description
- `associated_domains`: (empty - to be filled)
- `aliases`: (empty - to be filled)
- `source`: Data source identifier

## Output

Same Excel file with populated:
- `associated_domains`: Comma-separated list of email domains
- `aliases`: Comma-separated list of vendor name variations

## Example Output

```
HashiCorp:
  Domains: hashicorp.com,terraform.io
  Aliases: hashicorp,hashi,terraform

AWS:
  Domains: amazon.com,aws.com
  Aliases: amazon,amazonwebservices
```

## How It Works

1. **Data Collection**: Retrieves all email metadata from ChromaDB
2. **Vendor Matching**: Finds emails associated with each vendor
3. **Domain Analysis**: Extracts and ranks email domains by frequency
4. **Alias Detection**: Uses pattern matching and text analysis to find variations
5. **Excel Update**: Populates empty fields with discovered data

## Requirements

- Access to ChromaDB with processed emails
- pandas, openpyxl for Excel handling
- Existing VendorUpdater_Bot infrastructure