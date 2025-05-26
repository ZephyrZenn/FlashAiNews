from email.mime.text import MIMEText
import markdown

from app.models.config import EmailConfig
from app.models.feed import FeedBrief
from app.config.email import get_server


def send_brief_email(brief: FeedBrief, group_name, config: EmailConfig):
    if not config:
        raise ValueError("Email configuration is required")
    html_content = markdown.markdown(brief.content)
    subject = f"{brief.title} - Daily Brief of {group_name} - {brief.pub_date.strftime('%Y-%m-%d')}"
    _send_email(get_server(), config.sender, config.receiver, subject, html_content)


def _send_email(smtp_server, from_addr, to_addr, subject, content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    smtp_server.sendmail(from_addr, to_addr, msg.as_string())
