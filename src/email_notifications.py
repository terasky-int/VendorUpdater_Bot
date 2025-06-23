"""
Email notification system for VendorUpdater_Bot
Sends summary emails after pipeline runs
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any

def send_pipeline_summary_email(config: dict, run_summary: Dict[str, Any]) -> bool:
    """
    Send email notification with pipeline run summary
    
    Args:
        config: Configuration dictionary containing notification settings
        run_summary: Dictionary containing pipeline run details
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # Check if notifications are enabled
        notifications_config = config.get("notifications", {})
        if not notifications_config.get("enabled", False):
            logging.info("Email notifications are disabled")
            return True
            
        # Extract notification settings
        smtp_server = notifications_config.get("smtp_server")
        smtp_port = notifications_config.get("smtp_port", 587)
        sender_email = notifications_config.get("sender_email")
        sender_password = notifications_config.get("sender_password")
        recipients = notifications_config.get("recipients", [])
        
        if not all([smtp_server, sender_email, sender_password, recipients]):
            logging.error("Missing required notification configuration")
            return False
            
        # Create email content
        status_prefix = "SUCCESS" if run_summary.get("success", False) else "FAILED"
        subject = f"VendorUpdater Bot - {status_prefix} - Pipeline Run Summary ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
        body = _create_email_body(run_summary)
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        logging.info(f"Pipeline summary email sent to {len(recipients)} recipients")
        return True
        
    except Exception as e:
        logging.error(f"Failed to send notification email: {e}")
        return False

def _create_email_body(run_summary: Dict[str, Any]) -> str:
    """Create HTML email body from run summary"""
    
    emails_processed = run_summary.get("emails_processed", 0)
    processing_time = run_summary.get("processing_time", 0)
    success = run_summary.get("success", False)
    error = run_summary.get("error")
    email_details = run_summary.get("email_details", [])
    
    # Status styling
    status_color = "#28a745" if success else "#dc3545"
    status_text = "SUCCESS" if success else "FAILED"
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; margin: 20px;">
        <h2 style="color: #333;">VendorUpdater Bot - Pipeline Run Summary</h2>
        
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3>Run Status: <span style="color: {status_color}; font-weight: bold;">{status_text}</span></h3>
            <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Emails Processed:</strong> {emails_processed}</p>
            <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>
            {f'<p><strong>Error:</strong> <span style="color: #dc3545;">{error}</span></p>' if error else ''}
        </div>
    """
    
    if email_details and emails_processed > 0:
        html_body += """
        <h3>Email Details</h3>
        <table style="border-collapse: collapse; width: 100%; margin: 20px 0;">
            <thead>
                <tr style="background-color: #e9ecef;">
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Vendor</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Product</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Type</th>
                    <th style="border: 1px solid #dee2e6; padding: 8px; text-align: left;">Subject</th>
                </tr>
            </thead>
            <tbody>
        """
        
        for email in email_details:
            vendor = email.get("vendor", "unknown")
            product = email.get("product", "unknown") 
            email_type = email.get("type", "unknown")
            subject = email.get("subject", "N/A")[:50] + ("..." if len(email.get("subject", "")) > 50 else "")
            
            html_body += f"""
                <tr>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{vendor}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{product}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{email_type}</td>
                    <td style="border: 1px solid #dee2e6; padding: 8px;">{subject}</td>
                </tr>
            """
        
        html_body += """
            </tbody>
        </table>
        """
    
    html_body += """
        <hr style="margin: 30px 0;">
        <p style="color: #6c757d; font-size: 12px;">
            This is an automated message from VendorUpdater Bot.<br>
            Generated at {timestamp}
        </p>
    </body>
    </html>
    """.format(timestamp=datetime.now().isoformat())
    
    return html_body

def create_run_summary(emails_processed: int, processing_time: float, success: bool, 
                      error: str = None, email_details: List[Dict] = None) -> Dict[str, Any]:
    """
    Create a run summary dictionary for email notifications
    
    Args:
        emails_processed: Number of emails processed
        processing_time: Total processing time in seconds
        success: Whether the run was successful
        error: Error message if any
        email_details: List of email metadata dictionaries
        
    Returns:
        Dict containing run summary
    """
    return {
        "emails_processed": emails_processed,
        "processing_time": processing_time,
        "success": success,
        "error": error,
        "email_details": email_details or [],
        "timestamp": datetime.now().isoformat()
    }