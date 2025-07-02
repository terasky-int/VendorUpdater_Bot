# Vendor Updater Bot

## Overview
Vendor Updater Bot is an email ingestion and processing system that automatically harvests, processes, and indexes vendor emails for later retrieval and analysis.

## Core Features
- Email harvesting from IMAP servers
- Text normalization and cleaning
- Metadata extraction and enrichment
- Content classification using LLMs
- Text chunking and embedding generation
- Data storage in ChromaDB

## Getting Started

### Prerequisites
- Python 3.10+
- Docker (optional)
- AWS account with Bedrock access

### Installation

1. Clone the repository:
```bash
git clone https://github.com/your-org/vendor_updater_bot.git
cd vendor_updater_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your credentials
```

### Running the Application

#### Local Mode
Process emails from a local directory:
```bash
python main.py --local --folder data/emails
```

#### IMAP Mode
Process emails from an IMAP server:
```bash
python main.py
```

#### Docker
```bash
cd docker
docker build -t vendor-updater-bot:latest .
docker run -v ./data:/app/data vendor-updater-bot:latest
```

## Configuration
Configuration is stored in `config/config.yaml`. Key settings include:

- Email server connection details
- AWS Bedrock settings
- ChromaDB connection parameters
- Processing pipeline options

## Testing
Run the basic functionality tests:
```bash
python tests/tools/test_basic_functionality.py
```

## Architecture
The system follows a pipeline architecture:
1. **Harvest**: Fetch emails from IMAP or local files
2. **Normalize**: Clean and standardize text
3. **Enrich**: Extract metadata
4. **Classify**: Categorize content
5. **Chunk**: Split into manageable pieces
6. **Embed**: Generate vector embeddings
7. **Index**: Store in ChromaDB

## License
[Specify your license]