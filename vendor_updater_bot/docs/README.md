# Vendor Updater Bot Documentation

This directory contains documentation for the vendor_updater_bot email processing system.

## System Overview

The vendor_updater_bot is an intelligent email ingestion system that:

1. **Harvests emails** from IMAP servers or local files
2. **Processes and normalizes** content (removes HTML, signatures, etc.)
3. **Extracts metadata** (sender, date, language, vendor)
4. **Classifies content** using AWS Bedrock LLMs (type, products)
5. **Generates embeddings** using AWS Bedrock Titan
6. **Indexes data** in ChromaDB for semantic search

## Key Components

### Email Processing Pipeline
- `src/harvest.py` - Email collection from IMAP/local files
- `src/normalize.py` - Text cleaning and normalization
- `src/enrich.py` - Metadata extraction and vendor identification
- `src/classify.py` - Content classification using LLMs
- `src/chunker.py` - Text segmentation for embedding
- `src/embedder.py` - Vector embedding generation
- `src/indexer.py` - ChromaDB storage and indexing

### Supporting Features
- `src/email_notifications.py` - Processing summary emails
- `src/human_debug.py` - Step-by-step validation interface
- `src/monitoring.py` - System health and performance tracking
- `src/pipeline_tracker.py` - Run statistics and reporting

## Configuration

### Email Settings
Configure IMAP access for email harvesting:
```yaml
email:
  imap_server: imap.gmail.com
  email_address: your_email@gmail.com
  email_password: ${EMAIL_PASS}
  folder: INBOX
  mark_as_read: True
```

### Processing Settings
Control text processing and classification:
```yaml
data_processing:
  chunk_size_tokens: 512
  chunk_overlap: 20
  language_support: [en, he]

type_classification:
  labels:
    marketing: [promo, event, webinar]
    security: [vulnerability, patch]
    technical: [support, update]
```

### Vendor and Product Classification
Define known vendor-product relationships:
```yaml
product_classification:
  vendors:
    hashicorp: [vault, terraform, consul]
    palo alto: [prisma cloud, cortex xdr]
```

## Usage Examples

### Basic Processing
```bash
# Process local email files
python main.py --local --folder misc/tst_emls

# Process IMAP emails
python main.py

# Reset database and process
python main.py --reset-db --local --folder misc/tst_emls
```

### Debug Mode
Enable human-in-the-middle debugging:
```yaml
debug:
  enabled: True
  human_in_the_middle: True
```

### Email Notifications
Configure processing summaries:
```yaml
notifications:
  enabled: true
  smtp_server: smtp.gmail.com
  recipients: [admin@company.com]
```

## Output Data

The system produces:
- **ChromaDB**: Vector embeddings with metadata for search
- **Raw emails**: Saved in `data/raw_emails/`
- **Clean text**: Processed content in `data/clean_text/`
- **Logs**: Processing details in `logs/`
- **Manifest**: Processing record in `manifest.jsonl`

## Integration

Works with TeraskyRag for intelligent querying:
1. vendor_updater_bot processes and indexes emails
2. TeraskyRag provides search and analysis capabilities
3. Both systems share ChromaDB for data exchange