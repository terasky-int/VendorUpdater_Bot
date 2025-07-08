# Vendor Updater Bot

An intelligent email ingestion and processing system that automatically harvests, processes, and indexes vendor emails for later retrieval and analysis.

## Overview

Vendor Updater Bot is the ingestion component of a two-part system that:
1. **Harvests emails** from IMAP servers or local files
2. **Processes and normalizes** email content
3. **Extracts metadata** and enriches with vendor information
4. **Classifies content** using AWS Bedrock LLMs
5. **Generates embeddings** for semantic search
6. **Indexes data** in ChromaDB for retrieval

The processed data is then consumed by the TeraskyRag system for intelligent querying.

## Features

- ✅ Email harvesting from IMAP servers (Gmail, Outlook, etc.)
- ✅ Local email file processing (.eml files)
- ✅ Intelligent text normalization and cleaning
- ✅ Metadata extraction and vendor identification
- ✅ Content classification using AWS Bedrock
- ✅ Vector embedding generation with Titan
- ✅ ChromaDB indexing for semantic search
- ✅ Email notification system for processing summaries
- ✅ Human-in-the-middle debugging for validation
- ✅ Docker deployment support
- ✅ Comprehensive monitoring and logging

## Quick Start

### Prerequisites

- Python 3.10+
- AWS account with Bedrock access
- Email account with IMAP access (for email harvesting)
- ChromaDB instance (local or remote)

### Installation

1. **Clone and setup:**
```bash
git clone <repository-url>
cd vendor_updater_bot
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

3. **Update configuration:**
```bash
# Edit config/config.yaml with your email and processing settings
```

### Running the Application

#### Process Local Email Files
```bash
python main.py --local --folder misc/tst_emls
```

#### Process IMAP Emails
```bash
python main.py
```

#### With Database Reset
```bash
python main.py --reset-db --local --folder misc/tst_emls
```

#### Docker Deployment
```bash
cd docker
docker-compose up -d
```

## Configuration

Key configuration sections in `config/config.yaml`:

### Email Settings
```yaml
email:
  imap_server: imap.gmail.com
  email_address: your_email@gmail.com
  email_password: ${EMAIL_PASS}
  folder: INBOX
  mark_as_read: True
```

### AWS Bedrock
```yaml
bedrock:
  region: eu-west-1
  embedding_model: amazon.titan-embed-text-v2:0
  classification_model: anthropic.claude-3-haiku-20240307-v1:0
```

### Vector Storage
```yaml
vector_store:
  use_remote: true
  remote_host: "your-chromadb-host"
  remote_port: 8000
  collection_name: "vendor_emails"
```

### Email Notifications
```yaml
notifications:
  enabled: true
  smtp_server: smtp.gmail.com
  smtp_port: 587
  sender_email: ${NOTIFICATION_EMAIL}
  recipients:
    - admin@company.com
```

## Processing Pipeline

The system follows a sequential pipeline architecture:

1. **Harvest** (`src/harvest.py`): Fetch emails from IMAP or local files
2. **Normalize** (`src/normalize.py`): Clean HTML, remove signatures, extract text
3. **Enrich** (`src/enrich.py`): Extract metadata, detect language, infer vendor
4. **Classify** (`src/classify.py`): Categorize content and identify products using LLMs
5. **Chunk** (`src/chunker.py`): Split text into manageable pieces
6. **Embed** (`src/embedder.py`): Generate vector embeddings using AWS Bedrock
7. **Index** (`src/indexer.py`): Store in ChromaDB with metadata

## Command Line Options

```bash
python main.py [OPTIONS]

Options:
  --local                 Use local .eml files instead of IMAP
  --folder PATH          Folder containing .eml files (with --local)
  --reset-db             Reset ChromaDB before processing
  --emptydatafolders     Clean data folders before processing
  --deletelog            Delete log file before starting
  --noevaluation         Skip evaluation step
  --cleanup              Clean up incorrect relationships
  --confidence LEVEL     Set confidence level (high/medium/low)
```

## Testing

Run basic functionality tests:
```bash
python tests/tools/test_basic_functionality.py
```

Test configuration:
```bash
python test_config.py
```

Test Docker build:
```bash
python test_docker.py
```

## Human-in-the-Middle Debugging

Enable step-by-step validation in `config/config.yaml`:
```yaml
debug:
  enabled: True
  human_in_the_middle: True
```

This allows you to inspect and validate each processing step manually.

## Email Notifications

The system can send summary emails after each run:

1. **Configure SMTP settings** in config.yaml
2. **Set notification email** in .env
3. **Enable notifications** in config.yaml

Example notification includes:
- Processing status and timing
- Number of emails processed
- Detailed table of processed emails with vendor/product/type
- Error information if processing failed

## Monitoring

The system provides comprehensive monitoring:

- **Logs**: Detailed processing logs in `logs/`
- **Metrics**: Performance metrics in `logs/metrics.jsonl`
- **Health Checks**: System component status monitoring
- **Alerts**: Critical issue alerting in `logs/alerts.jsonl`

## Data Output

Processed data is stored in:
- **ChromaDB**: Vector embeddings with metadata for semantic search
- **Raw emails**: Saved in `data/raw_emails/`
- **Clean text**: Processed text in `data/clean_text/`
- **Manifest**: Processing record in `manifest.jsonl`

## Integration with TeraskyRag

This system works in conjunction with TeraskyRag:

1. **vendor_updater_bot** processes and indexes emails
2. **TeraskyRag** provides intelligent querying and search capabilities
3. Both systems share the same ChromaDB instance
4. Data flows: Email → Processing → ChromaDB → TeraskyRag → User Queries

## Docker Deployment

### Standalone Container
```bash
cd docker
docker build -t vendor-updater-bot .
docker run -v ./data:/app/data vendor-updater-bot
```

### With Docker Compose
```bash
cd docker
# Edit docker-compose.yml with your configuration
docker-compose up -d
```

### Scheduled Processing
Use the included cron script for scheduled processing:
```bash
# Add to crontab for hourly processing
0 * * * * /path/to/vendor_updater_bot/docker/cron-job.sh
```

## Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure AWS credentials are properly configured
2. **Email Authentication**: Use app passwords for Gmail/Outlook
3. **ChromaDB Connection**: Verify remote ChromaDB host and port
4. **Memory Usage**: Monitor system resources during processing

### Debug Mode

Enable verbose logging:
```yaml
debug:
  enabled: True
  verbose_logging: True
  save_all_artifacts: True
```

## License

[Specify your license]

## Support

For issues and questions, please refer to the documentation or create an issue in the repository.