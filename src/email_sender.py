"""
Email sender for delivering daily arxiv digest via SMTP
"""

import smtplib
import time
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
        papers: List[Dict[str, Any]],
        unscored_papers: List[Dict[str, Any]] = None,
        failed_categories: List[str] = None
    ) -> bool:
        """
        Send the daily digest email.

        Args:
            papers: List of relevant papers to include
            unscored_papers: Papers that could not be evaluated
            failed_categories: Categories that failed to fetch

        Returns:
            True if successful, False otherwise
        """
        unscored_papers = unscored_papers or []
        failed_categories = failed_categories or []

        subject = self._create_subject(papers)
        body = self._create_body(
            papers, unscored_papers, failed_categories
        )

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
    
    def _create_warning_banner(
        self,
        failed_categories: List[str],
        unscored_papers: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Build a coverage-warning banner shown at the top of the digest.

        Surfaces incomplete coverage loudly so a partial run is never
        mistaken for a quiet day with nothing relevant.
        """
        if not failed_categories and not unscored_papers:
            return []

        lines = ["⚠️  COVERAGE WARNING", "─" * 70]
        if failed_categories:
            lines.append(
                "These categories could NOT be fetched this run "
                "(papers may be missing):"
            )
            for cat in failed_categories:
                lines.append(f"   • {cat}")
        if unscored_papers:
            lines.append(
                f"{len(unscored_papers)} paper(s) could not be scored "
                "and are listed at the bottom for manual review."
            )
        lines.extend(["─" * 70, ""])
        return lines

    def _create_unscored_section(
        self,
        unscored_papers: List[Dict[str, Any]]
    ) -> List[str]:
        """Build the 'could not evaluate' section."""
        if not unscored_papers:
            return []

        lines = [
            "",
            "=" * 70,
            f"⚠️  COULD NOT EVALUATE ({len(unscored_papers)} paper(s))",
            "These hit an error during scoring — review manually so a",
            "relevant paper is not missed.",
            "=" * 70,
        ]
        for i, paper in enumerate(unscored_papers, 1):
            error = paper.get('eval_error', 'Unknown error')
            lines.extend([
                "",
                f"{i}. {paper.get('title', 'No title')}",
                f"   📥 PDF: {paper.get('pdf_url', 'n/a')}",
                f"   ⚠️  {error}",
            ])
        lines.append("")
        return lines

    def _create_body(
        self,
        papers: List[Dict[str, Any]],
        unscored_papers: List[Dict[str, Any]] = None,
        failed_categories: List[str] = None
    ) -> str:
        """Create email body with paper details."""
        unscored_papers = unscored_papers or []
        failed_categories = failed_categories or []

        banner = self._create_warning_banner(
            failed_categories, unscored_papers
        )

        if not papers:
            body = ["ArXiv Daily Digest", ""]
            body.extend(banner)
            body.extend([
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
            ])
            body.extend(self._create_unscored_section(unscored_papers))
            body.extend([
                "",
                "---",
                "This digest was generated automatically.",
                "Powered by ArXiv Daily Digest"
            ])
            return "\n".join(body)

        # Calculate stats
        avg_score = sum(
            p.get('relevance_score', 0) for p in papers
        ) / len(papers)
        high_relevance = sum(
            1 for p in papers if p.get('relevance_score', 0) >= 8
        )
        
        lines = ["ARXIV DAILY DIGEST", "=" * 70, ""]
        lines.extend(banner)
        lines.extend([
            f"📊 Summary: {len(papers)} relevant paper(s) found",
            f"   Average relevance: {avg_score:.1f}/10",
            f"   High relevance (≥8): {high_relevance} paper(s)",
            "",
            "=" * 70,
            ""
        ])
        
        for i, paper in enumerate(papers, 1):
            score = paper.get('relevance_score', 0)
            reason = paper.get(
                'relevance_reason', 
                'No reason provided'
            )
            
            # Truncate long author lists
            authors = paper['authors']
            if len(authors) > 100:
                authors = authors[:100] + "..."
            
            # Flag replacements/cross-lists so a re-announced older
            # paper is not mistaken for a brand-new submission.
            tag = (
                "  [updated/cross-list]"
                if paper.get('status') == 'updated'
                else ""
            )

            lines.extend([
                "",
                f"PAPER #{i}{tag}",
                "─" * 70,
                "",
                f"📄 {paper['title']}",
                "",
                f"✍️  Authors: {authors}",
                f"📅 Published: {paper['published']}",
                "",
                f"⭐ RELEVANCE SCORE: {score}/10",
                f"💡 {reason}",
                "",
                f"📥 PDF: {paper['pdf_url']}",
                "",
                "📝 ABSTRACT:",
            ])
            
            # Add wrapped abstract with proper indentation
            abstract_lines = self._wrap_text(
                paper['abstract'], 
                67
            ).split('\n')
            for line in abstract_lines:
                lines.append(f"   {line.strip()}")
            
            lines.extend([
                "",
                "─" * 70,
                ""
            ])
        
        lines.extend(self._create_unscored_section(unscored_papers))

        lines.extend([
            "",
            "=" * 70,
            "📬 This digest was generated automatically",
            "🤖 Powered by ArXiv Daily Digest with AI evaluation",
            "=" * 70
        ])

        return "\n".join(lines)
    
    def _wrap_text(self, text: str, width: int) -> str:
        """Wrap text to specified width."""
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
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return '\n'.join(lines)
    
    def _send_email(
        self,
        subject: str,
        body: str,
        max_retries: int = 3
    ) -> bool:
        """
        Send the email via SMTP, retrying transient failures.

        Args:
            subject: Email subject
            body: Email body
            max_retries: Number of send attempts before giving up

        Returns:
            True if successful, False otherwise
        """
        # Create message
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = self.to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        base_delay = 2.0
        for attempt in range(max_retries):
            try:
                # Connect to SMTP server and send
                with smtplib.SMTP(
                    self.smtp_server,
                    self.smtp_port,
                    timeout=30
                ) as server:
                    server.starttls()
                    server.login(self.from_email, self.password)
                    server.send_message(msg)

                print(f"Email sent successfully to {self.to_email}")
                return True

            except smtplib.SMTPAuthenticationError as e:
                # Bad credentials won't fix themselves on retry.
                print(f"Failed to send email (auth error): {e}")
                return False
            except Exception as e:
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    print(
                        f"Email send attempt {attempt + 1} failed "
                        f"({e}); retrying in {delay:.0f}s..."
                    )
                    time.sleep(delay)
                    continue
                print(
                    f"Failed to send email after "
                    f"{max_retries} attempts: {e}"
                )
                return False

        return False

