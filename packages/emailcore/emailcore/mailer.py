import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class EmailSender:
    """Unified email sender supporting console and SMTP backends.

    email_type="console"  — prints to stdout (dev/test only)
    email_type="smtp"     — delivers via SMTP with optional TLS and auth
    """

    def __init__(
        self,
        *,
        email_type: str,
        from_address: str,
        from_name: str = "",
        smtp_host: str = "",
        smtp_port: int = 587,
        smtp_enc_type: str = "none",
        smtp_auth_enabled: bool = False,
        smtp_username: str = "",
        smtp_password: str = "",
    ):
        self.email_type = email_type
        self.from_address = from_address
        self.from_name = from_name or from_address
        self.smtp_host = smtp_host
        self.smtp_port = int(smtp_port)
        self.smtp_enc_type = smtp_enc_type.lower()
        self.smtp_auth_enabled = smtp_auth_enabled
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def send(
        self,
        *,
        to: "str | list[str]",
        subject: str,
        body: str,
        html_body: str = "",
        cc: "str | list[str] | None" = None,
        bcc: "str | list[str] | None" = None,
        attachments: "list[dict] | None" = None,
    ) -> None:
        """Send an email.

        Args:
            to: Recipient address(es).
            subject: Email subject line.
            body: Plain-text body.
            html_body: Optional HTML body (sent as an alternative part).
            cc: Optional CC address(es).
            bcc: Optional BCC address(es).
            attachments: Optional list of dicts with keys:
                         ``filename`` (str) and ``data`` (bytes).
        """
        recipients = [to] if isinstance(to, str) else list(to)
        cc_list = ([cc] if isinstance(cc, str) else list(cc)) if cc else []
        bcc_list = ([bcc] if isinstance(bcc, str) else list(bcc)) if bcc else []

        if self.email_type == "console":
            self._send_console(
                recipients=recipients,
                subject=subject,
                body=body,
                cc=cc_list,
                bcc=bcc_list,
            )
        elif self.email_type == "smtp":
            msg = self._build_message(
                to=recipients,
                subject=subject,
                body=body,
                html_body=html_body,
                cc=cc_list,
                attachments=attachments,
            )
            self._send_smtp(msg, recipients + cc_list + bcc_list)
        else:
            raise ValueError(f"Unknown email_type: {self.email_type!r}")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _from_header(self) -> str:
        return (
            f"{self.from_name} <{self.from_address}>"
            if self.from_name
            else self.from_address
        )

    def _build_message(
        self,
        *,
        to: list,
        subject: str,
        body: str,
        html_body: str = "",
        cc: "list | None" = None,
        attachments=None,
    ) -> MIMEMultipart:
        msg = MIMEMultipart("mixed")
        msg["Subject"] = subject
        msg["From"] = self._from_header()
        msg["To"] = ", ".join(to)
        if cc:
            msg["Cc"] = ", ".join(cc)

        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(body, "plain", "utf-8"))
        if html_body:
            alt.attach(MIMEText(html_body, "html", "utf-8"))
        msg.attach(alt)

        for attachment in attachments or []:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment["data"])
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{attachment["filename"]}"',
            )
            msg.attach(part)

        return msg

    def _send_console(
        self,
        *,
        recipients: list,
        subject: str,
        body: str,
        cc: "list | None" = None,
        bcc: "list | None" = None,
    ) -> None:
        import sys

        sep = "-" * 60
        print(f"\n{sep}")
        print("  EMAIL  (console backend)")
        print(sep)
        print(f"  From:    {self._from_header()}")
        print(f"  To:      {', '.join(recipients)}")
        if cc:
            print(f"  Cc:      {', '.join(cc)}")
        if bcc:
            print(f"  Bcc:     {', '.join(bcc)}")
        print(f"  Subject: {subject}")
        print(sep)
        for line in body.splitlines():
            print(f"  {line}")
        print(f"{sep}\n")
        sys.stdout.flush()

    def _send_smtp(self, msg: MIMEMultipart, recipients: list) -> None:
        ctx = ssl.create_default_context()

        smtp: smtplib.SMTP
        if self.smtp_enc_type == "ssl":
            smtp = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, context=ctx)
        else:
            smtp = smtplib.SMTP(self.smtp_host, self.smtp_port)
            if self.smtp_enc_type == "starttls":
                smtp.ehlo()
                smtp.starttls(context=ctx)
                smtp.ehlo()

        try:
            if self.smtp_auth_enabled:
                smtp.login(self.smtp_username, self.smtp_password)
            smtp.sendmail(self.from_address, recipients, msg.as_string())
        finally:
            try:
                smtp.quit()
            except Exception:  # nosec B110
                pass
