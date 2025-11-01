"""
Email sender for delivering daily arxiv digest via SMTP
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any


class EmailSender:
    """Send arxiv digest emails via SMTP."""
    
    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        from_email: str,
        password: str,
        to_email: str
    ):
        """
        Initialize the email sender.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            from_email: Sender email address
            password: Email password or app password
            to_email: Recipient email address
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.from_email = from_email
        self.password = password
        self.to_email = to_email
    
    def send_digest(
        self, 
        papers: List[Dict[str, Any]]
    ) -> bool:
        """
        Send the daily digest email.
        
        Args:
            papers: List of relevant papers to include
            
        Returns:
            True if successful, False otherwise
        """
        subject = self._create_subject(papers)
        body = self._create_body(papers)
        
        return self._send_email(subject, body)
    
    def _create_subject(
        self, 
        papers: List[Dict[str, Any]]
    ) -> str:
        """Create email subject line."""
        date_str = datetime.now().strftime('%Y-%m-%d')
        count = len(papers)
        
        if count == 0:
            return f"ArXiv Digest: No matches - {date_str}"
        
        return (
            f"ArXiv Digest: {count} relevant "
            f"paper{'s' if count != 1 else ''} - {date_str}"
        )
    
    def _create_body(
        self, 
        papers: List[Dict[str, Any]]
    ) -> str:
        """Create email body with paper details."""
        if not papers:
            return "\n".join([
                "ArXiv Daily Digest",
                "",
                "=" * 70,
                "",
                "No papers matched your interests today.",
                "",
                "This means no papers from your selected arXiv",
                "categories scored above your relevance threshold.",
                "",
                "Suggestions:",
                "- Lower your threshold in config.yaml",
                "- Add more arXiv categories",
                "- Broaden your keyword filters",
                "- Update your research interests description",
                "",
                "=" * 70,
                "",
                "---",
                "This digest was generated automatically.",
                "Powered by ArXiv Daily Digest"
            ])
        
        lines = [
            "Here are today's relevant papers from arXiv:",
            "",
            "=" * 70,
            ""
        ]
        
        for i, paper in enumerate(papers, 1):
            score = paper.get('relevance_score', 0)
            reason = paper.get(
                'relevance_reason', 
                'No reason provided'
            )
            
            lines.extend([
                f"{i}. {paper['title']}",
                f"   Authors: {paper['authors']}",
                f"   Published: {paper['published']}",
                f"   Relevance: {score}/10 - {reason}",
                f"   URL: {paper['url']}",
                f"   PDF: {paper['pdf_url']}",
                "",
                "   Abstract:",
                f"   {self._wrap_text(paper['abstract'], 67)}",
                "",
                "-" * 70,
                ""
            ])
        
        lines.extend([
            "",
            "---",
            "This digest was generated automatically.",
            "Powered by ArXiv Daily Digest"
        ])
        
        return "\n".join(lines)
    
    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to specified width with indent."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= width:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append('   ' + ' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append('   ' + ' '.join(current_line))
        
        return '\n'.join(lines)
    
    def _send_email(self, subject: str, body: str) -> bool:
        """
        Send the email via SMTP.
        
        Args:
            subject: Email subject
            body: Email body
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server and send
            with smtplib.SMTP(
                self.smtp_server, 
                self.smtp_port
            ) as server:
                server.starttls()
                server.login(self.from_email, self.password)
                server.send_message(msg)
            
            print(f"Email sent successfully to {self.to_email}")
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

