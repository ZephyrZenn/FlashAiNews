import markdown
import resend

from app.models.config import EmailConfig
from app.models.feed import FeedBrief


def send_brief_email(brief: FeedBrief, group_name, config: EmailConfig):
    if not config:
        raise ValueError("Email configuration is required")
    html_content = markdown.markdown(brief.content)
    subject = f"{brief.title} - Daily Brief of {group_name} - {brief.pub_date.strftime('%Y-%m-%d')}"
    _send_email(config.sender, config.receiver, subject, html_content)


def _send_email(from_addr, to_addr, subject, content):
    r = resend.Emails.send({
        "from": from_addr,
        "to": to_addr,
        "subject": subject,
        "html": content,
    })
    
