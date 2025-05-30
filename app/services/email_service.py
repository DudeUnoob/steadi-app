import os
import logging
from typing import Dict, List, Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, To, From, Subject, HtmlContent, PlainTextContent
from jinja2 import Environment, BaseLoader

logger = logging.getLogger(__name__)

class EmailService:
    """Service for sending emails via SendGrid"""
    
    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "alerts@steadi.app")
        self.from_name = os.getenv("FROM_NAME", "Steadi Inventory")
        
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = SendGridAPIClient(api_key=self.api_key)
    
    def send_stock_alert_email(
        self, 
        to_email: str, 
        user_name: str,
        alerts: List[Dict],
        alert_counts: Dict[str, int]
    ) -> bool:
        """Send stock alert email with multiple products"""
        if not self.client:
            logger.error("SendGrid client not initialized - missing API key")
            return False
        
        try:
            # Generate email content
            subject = self._generate_subject(alert_counts)
            html_content = self._generate_html_content(user_name, alerts, alert_counts)
            plain_content = self._generate_plain_content(user_name, alerts, alert_counts)
            
            # Create email
            message = Mail(
                from_email=From(self.from_email, self.from_name),
                to_emails=To(to_email),
                subject=Subject(subject),
                html_content=HtmlContent(html_content),
                plain_text_content=PlainTextContent(plain_content)
            )
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Stock alert email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email. Status: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending stock alert email: {str(e)}")
            return False
    
    def _generate_subject(self, alert_counts: Dict[str, int]) -> str:
        """Generate email subject based on alert counts"""
        red_count = alert_counts.get("red", 0)
        yellow_count = alert_counts.get("yellow", 0)
        
        if red_count > 0:
            return f"🚨 URGENT: {red_count} products need immediate reordering"
        elif yellow_count > 0:
            return f"⚠️ {yellow_count} products approaching reorder point"
        else:
            return "📊 Inventory Status Update"
    
    def _generate_html_content(
        self, 
        user_name: str, 
        alerts: List[Dict], 
        alert_counts: Dict[str, int]
    ) -> str:
        """Generate HTML email content"""
        
        red_alerts = [alert for alert in alerts if alert.get("alert_level") == "RED"]
        yellow_alerts = [alert for alert in alerts if alert.get("alert_level") == "YELLOW"]
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Stock Alert</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .alert-section {{ margin-bottom: 30px; }}
                .alert-urgent {{ border-left: 4px solid #dc3545; padding-left: 15px; }}
                .alert-warning {{ border-left: 4px solid #ffc107; padding-left: 15px; }}
                .product-item {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 6px; }}
                .product-sku {{ font-weight: bold; color: #495057; }}
                .product-name {{ color: #6c757d; }}
                .stock-info {{ margin-top: 8px; font-size: 14px; }}
                .urgent {{ color: #dc3545; font-weight: bold; }}
                .warning {{ color: #856404; font-weight: bold; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6; font-size: 12px; color: #6c757d; }}
                .btn {{ display: inline-block; padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>📦 Inventory Alert</h2>
                    <p>Hello {user_name},</p>
                    <p>Here's your inventory status update:</p>
                </div>
        """
        
        if red_alerts:
            html += f"""
                <div class="alert-section alert-urgent">
                    <h3>🚨 URGENT - Immediate Action Required ({len(red_alerts)} items)</h3>
                    <p>These products are at or below their reorder point and need immediate attention:</p>
            """
            
            for alert in red_alerts:
                html += f"""
                    <div class="product-item">
                        <div class="product-sku urgent">{alert.get('sku', 'N/A')}</div>
                        <div class="product-name">{alert.get('name', 'N/A')}</div>
                        <div class="stock-info">
                            <strong>On Hand:</strong> {alert.get('on_hand', 0)} | 
                            <strong>Reorder Point:</strong> {alert.get('reorder_point', 0)} | 
                            <strong>Days Left:</strong> ~{alert.get('days_of_stock', 0)} days<br>
                            <strong>Suggested Order:</strong> {alert.get('reorder_quantity', 0)} units
                            {f" | <strong>Supplier:</strong> {alert.get('supplier_name', 'Unknown')}" if alert.get('supplier_name') else ""}
                        </div>
                    </div>
                """
            
            html += "</div>"
        
        if yellow_alerts:
            html += f"""
                <div class="alert-section alert-warning">
                    <h3>⚠️ Warning - Monitor Closely ({len(yellow_alerts)} items)</h3>
                    <p>These products are approaching their reorder point:</p>
            """
            
            for alert in yellow_alerts:
                html += f"""
                    <div class="product-item">
                        <div class="product-sku warning">{alert.get('sku', 'N/A')}</div>
                        <div class="product-name">{alert.get('name', 'N/A')}</div>
                        <div class="stock-info">
                            <strong>On Hand:</strong> {alert.get('on_hand', 0)} | 
                            <strong>Reorder Point:</strong> {alert.get('reorder_point', 0)} | 
                            <strong>Days Left:</strong> ~{alert.get('days_of_stock', 0)} days<br>
                            <strong>Suggested Order:</strong> {alert.get('reorder_quantity', 0)} units
                            {f" | <strong>Supplier:</strong> {alert.get('supplier_name', 'Unknown')}" if alert.get('supplier_name') else ""}
                        </div>
                    </div>
                """
            
            html += "</div>"
        
        html += f"""
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{os.getenv('FRONTEND_URL', 'https://app.steadi.com')}/dashboard" class="btn">
                        View Dashboard
                    </a>
                </div>
                
                <div class="footer">
                    <p>This is an automated alert from Steadi Inventory Management.</p>
                    <p>To manage your notification preferences, visit your dashboard settings.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_plain_content(
        self, 
        user_name: str, 
        alerts: List[Dict], 
        alert_counts: Dict[str, int]
    ) -> str:
        """Generate plain text email content"""
        
        red_alerts = [alert for alert in alerts if alert.get("alert_level") == "RED"]
        yellow_alerts = [alert for alert in alerts if alert.get("alert_level") == "YELLOW"]
        
        content = f"""
INVENTORY ALERT

Hello {user_name},

Here's your inventory status update:
"""
        
        if red_alerts:
            content += f"""

🚨 URGENT - Immediate Action Required ({len(red_alerts)} items)
These products are at or below their reorder point:

"""
            for alert in red_alerts:
                content += f"""
• {alert.get('sku', 'N/A')} - {alert.get('name', 'N/A')}
  On Hand: {alert.get('on_hand', 0)} | Reorder Point: {alert.get('reorder_point', 0)}
  Days Left: ~{alert.get('days_of_stock', 0)} days
  Suggested Order: {alert.get('reorder_quantity', 0)} units
  Supplier: {alert.get('supplier_name', 'Unknown')}

"""
        
        if yellow_alerts:
            content += f"""

⚠️ Warning - Monitor Closely ({len(yellow_alerts)} items)
These products are approaching their reorder point:

"""
            for alert in yellow_alerts:
                content += f"""
• {alert.get('sku', 'N/A')} - {alert.get('name', 'N/A')}
  On Hand: {alert.get('on_hand', 0)} | Reorder Point: {alert.get('reorder_point', 0)}
  Days Left: ~{alert.get('days_of_stock', 0)} days
  Suggested Order: {alert.get('reorder_quantity', 0)} units
  Supplier: {alert.get('supplier_name', 'Unknown')}

"""
        
        content += f"""

View your full dashboard: {os.getenv('FRONTEND_URL', 'https://app.steadi.com')}/dashboard

---
This is an automated alert from Steadi Inventory Management.
To manage your notification preferences, visit your dashboard settings.
"""
        
        return content 