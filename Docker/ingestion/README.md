# Ingestion Pipeline Docker Deployment

Email ingestion and processing pipeline container.

## Quick Start

1. **Configure environment:**
   ```bash
   # Edit .env with your actual values
   nano .env
   ```

2. **Place email files:**
   ```bash
   # Copy .eml files to data/raw_emails/
   cp *.eml ../../data/raw_emails/
   ```

3. **Build and run:**
   ```bash
   docker-compose up -d
   ```

## Build Only
```bash
docker build -t ingestion-pipeline .
```

## Run Options

**Local email processing:**
```bash
docker-compose run ingestion python main.py --local --folder data/raw_emails
```

**IMAP email processing:**
```bash
docker-compose run ingestion python main.py
```

**With human debugging:**
```bash
docker-compose run ingestion python main.py --local --folder data/raw_emails
# (Enable human_in_the_middle in config.yaml)
```

## Data Persistence

- `data/` - Email files and processed data
- `logs/` - Processing logs
- `config/` - Configuration files

All data is persisted via Docker volumes.