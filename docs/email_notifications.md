# Email Notification System

## Overview

The email notification system sends summary emails after each pipeline run, providing details about processed emails, processing time, and any errors encountered.

## Configuration

### 1. Environment Variables

Add to your `.env` file:
```
NOTIFICATION_EMAIL=your_notification_email@gmail.com
NOTIFICATION_EMAIL_PASS=your_notification_email_password
```

### 2. Config File Settings

In `config/config.yaml`:
```yaml
notifications:
  enabled: true                    # Enable/disable notifications
  smtp_server: smtp.gmail.com      # SMTP server
  smtp_port: 587                   # SMTP port
  sender_email: ${NOTIFICATION_EMAIL}
  sender_password: ${NOTIFICATION_EMAIL_PASS}
  recipients:                      # List of email recipients
    - admin@company.com
    - team@company.com
```

## Testing

### 1. Test Notification System
```bash
python test_email_notifications.py
```

This sends two test emails:
- Success notification with sample data
- Failure notification with error message

### 2. Test with Pipeline
```bash
# Enable notifications in config first
python main.py --local --folder ./misc/tst_emls
```

### 3. Verify Email Content

Check that emails contain:
- ✅ Run status (SUCCESS/FAILED)
- ✅ Processing time and email count
- ✅ Table with vendor, product, type, subject for each email
- ✅ Error details (if failed)
- ✅ Timestamp

## Email Content

### Success Email
- **Subject**: `VendorUpdater Bot - SUCCESS - Pipeline Run Summary (YYYY-MM-DD HH:MM)`
- **Content**: HTML formatted with processing stats and email details table

### Failure Email
- **Subject**: `VendorUpdater Bot - FAILED - Pipeline Run Summary (YYYY-MM-DD HH:MM)`
- **Content**: Same as success but includes error message

## Troubleshooting

### Common Issues

1. **No emails received**
   - Check `notifications.enabled: true` in config
   - Verify SMTP credentials in `.env`
   - Check spam folder

2. **Authentication errors**
   - For Gmail: Use App Password, not regular password
   - Enable 2FA and generate App Password in Google Account settings

3. **SMTP connection errors**
   - Verify SMTP server and port settings
   - Check firewall/network restrictions

### Gmail Setup

1. Enable 2-Factor Authentication
2. Generate App Password:
   - Google Account → Security → App passwords
   - Select "Mail" and generate password
   - Use this password in `NOTIFICATION_EMAIL_PASS`

## Integration

The notification system is automatically integrated into the main pipeline:

1. **PipelineTracker** collects run details during execution
2. **Email details** are captured after classification step
3. **Notifications sent** in finally block (success or failure)
4. **Non-blocking** - notification failures won't crash pipeline

## Files

- `src/email_notifications.py` - Main notification functions
- `src/pipeline_tracker.py` - Run tracking and data collection
- `test_email_notifications.py` - Test script
- `config/config.yaml` - Configuration settings