# Human-in-the-Middle Debugging Guide

## Overview

The human-in-the-middle debugging feature allows you to step through the email processing pipeline and validate each step's input and output manually. This helps build trust in the data categorization process.

## Configuration

Enable human debugging in your `config/config.yaml`:

```yaml
debug:
  enabled: True
  human_in_the_middle: True  # Set to True to enable step-by-step debugging
```

## Usage

1. **Enable debugging** in the config file
2. **Run the pipeline** normally: `python main.py --local --folder misc/tst_emls`
3. **Review each step** as the pipeline pauses for your input

## Debug Interface

When debugging is enabled, the pipeline will pause at each major step and show:

- **Step name** and email ID
- **Input data** (what goes into the step)
- **Output data** (what comes out of the step)
- **User prompt** for validation

## User Options

At each step, you can choose:

- **y/yes/Enter**: Continue to next step
- **n/no**: Skip this email and move to the next one
- **s/save**: Save debug data to file and continue
- **q/quit**: Stop the entire pipeline

## Processing Steps

The pipeline will pause at these key steps:

1. **save_raw_email**: Email saved to disk
2. **normalize_email**: HTML cleaned, text extracted
3. **extract_metadata**: Sender, date, language detected
4. **classify_content**: Vendor, products, type classified
5. **chunk_text**: Text split into chunks
6. **generate_embeddings**: Vector embeddings created
7. **index_local**: Data indexed in ChromaDB
8. **store_neo4j**: Relationships stored in graph database

## Debug Data Storage

When you choose 's' (save), debug data is stored in:
- `logs/debug_data/{email_id}_{step_name}_{timestamp}.json`

This allows you to review the data later and identify patterns or issues.

## Example Session

```
================================================================================
🔍 HUMAN DEBUG - Step: classify_content
📧 Email ID: abc123-def456
⏰ Time: 14:30:15
================================================================================

📥 INPUT:
----------------------------------------
text: Breaking up the "Terralith" 🧱— strategies for better Terraform configurations...
vendor: hashicorp
language: en

📤 OUTPUT:
----------------------------------------
vendor: hashicorp
product: ['terraform', 'vault']
type: ['webinar', 'event', 'announcement']
confidence: 0.92

================================================================================
Continue? (y/n/s/q): y
```

## Tips

- Use this feature when you want to validate that emails are being categorized correctly
- Save interesting cases with 's' for later analysis
- Focus on emails where you suspect classification might be wrong
- Use 'n' to skip emails that are clearly spam or irrelevant

## Troubleshooting

- If the interface doesn't appear, check that `human_in_the_middle: True` in config
- Debug data files are saved to `logs/debug_data/` directory
- Use `q` to cleanly exit if you need to stop the process