"""
Pipeline run tracking for email notifications
"""
from typing import List, Dict, Any
from datetime import datetime

class PipelineTracker:
    """Track pipeline run details for notifications"""
    
    def __init__(self):
        self.start_time = None
        self.emails_processed = 0
        self.email_details = []
        self.error = None
        
    def start_run(self):
        """Start tracking a pipeline run"""
        self.start_time = datetime.now().timestamp()
        self.emails_processed = 0
        self.email_details = []
        self.error = None
        
    def add_processed_email(self, email_obj, classified_data: Dict[str, Any]):
        """Add details of a processed email"""
        self.emails_processed += 1
        
        # Extract subject from email object
        subject = getattr(email_obj, 'get', lambda x, default='': default)('Subject', 'N/A')
        if hasattr(subject, 'strip'):
            subject = subject.strip()
            
        self.email_details.append({
            "vendor": classified_data.get("vendor", "unknown"),
            "product": classified_data.get("product", "unknown"), 
            "type": classified_data.get("type", "unknown"),
            "subject": str(subject)
        })
        
    def set_error(self, error_msg: str):
        """Set error message for failed runs"""
        self.error = error_msg
        
    def get_summary(self) -> Dict[str, Any]:
        """Get run summary for notifications"""
        processing_time = (datetime.now().timestamp() - self.start_time) if self.start_time else 0
        
        return {
            "emails_processed": self.emails_processed,
            "processing_time": processing_time,
            "success": self.error is None,
            "error": self.error,
            "email_details": self.email_details,
            "timestamp": datetime.now().isoformat()
        }