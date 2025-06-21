
import resend

from app.models.config import EmailConfig


def init_email(config: EmailConfig):
    resend.api_key = config.api_key
