import smtplib
from typing import Optional

from app.exception import BizException
from app.models.config import EmailConfig

server: Optional[smtplib.SMTP] = None

def init_smtp(config: EmailConfig):
    global server
    if server:
        return
    smtp_server = config.smtp_server

    server = smtplib.SMTP(smtp_server)
    server.set_debuglevel(1)
    server.login(config.sender, config.password)

def get_server() -> smtplib.SMTP:
    if not server:
        raise BizException("STMP server not initialized")
    return server

def shutdown_smtp():
    global server
    if server:
        server.quit()
        server = None