# Test Email Files

This directory contains sample .eml files for testing the email processing pipeline.

## Usage

Process these test emails with:

```bash
python main.py --local --folder misc/tst_emls
```

## Files

The test emails include various vendor communications:
- HashiCorp product announcements
- Security updates and patches
- Webinar invitations
- Product certifications
- Technical updates

These files are used to test:
- Email parsing and normalization
- Vendor identification
- Content classification
- Product extraction
- Metadata enrichment

## Adding New Test Files

To add new test emails:
1. Save emails as .eml files in this directory
2. Ensure they represent different vendors and content types
3. Test the pipeline with the new files