"""Email Sender — simulates composing and sending emails."""

from __future__ import annotations

import hashlib
from datetime import datetime

from registry.models import ToolParameter, ToolSchema, ToolVersion

SCHEMA = ToolSchema(
    name="email_sender",
    display_name="Email Sender",
    description=(
        "Composes and sends emails to specified recipients with subject, body, and "
        "optional attachments. Supports plain text and HTML content, CC/BCC fields, "
        "and priority levels. Essential for automated notifications, scheduled "
        "reports, customer communication, and workflow-triggered alerts."
    ),
    category="communication",
    tags=["email", "e-posta", "send", "gönder", "notification", "bildirim", "smtp"],
    parameters=[
        ToolParameter(name="to", type="string", description="Recipient email address"),
        ToolParameter(name="subject", type="string", description="Email subject line"),
        ToolParameter(name="body", type="string", description="Email body content"),
        ToolParameter(name="cc", type="string", description="CC recipients (comma-separated)", required=False),
        ToolParameter(name="priority", type="string", description="Priority: 'low', 'normal', 'high'", required=False),
    ],
    version=ToolVersion(major=1, minor=0, patch=0),
    examples=[
        "ahmet@example.com adresine 'Toplantı Özeti' konulu bir e-posta gönder.",
        "Send a high-priority email to the team about the deployment schedule.",
        "Müşteriye fatura bilgilerini içeren bir e-posta at.",
    ],
    callable_template="result = email_sender(to='{to}', subject='{subject}', body='{body}')",
)


def execute(params: dict) -> dict:
    """Simulate sending an email and return a mock confirmation."""
    to = params.get("to", "recipient@example.com")
    subject = params.get("subject", "No Subject")
    body = params.get("body", "")
    cc = params.get("cc", "")
    priority = params.get("priority", "normal")

    # Generate a deterministic message ID
    msg_hash = hashlib.md5(f"{to}{subject}{body}".encode()).hexdigest()[:12]  # noqa: S324
    message_id = f"<msg-{msg_hash}@mail.dynamic-agent.local>"

    return {
        "message_id": message_id,
        "to": to,
        "cc": cc or None,
        "subject": subject,
        "body_preview": body[:100] + ("..." if len(body) > 100 else ""),
        "priority": priority,
        "sent_at": datetime.now().isoformat(),
        "status": "sent",
        "success": True,
    }
