def build_email_sender():
    """Build an EmailSender from the current email configuration.

    Reads email type, credentials, and SMTP settings from Configuration records.
    Safe to call only after setup is complete.
    """
    from emailcore import EmailSender

    from apps.configurations.selectors import Email as EmailConfig
    from apps.setup.constants import EmailType

    email_type = EmailConfig.get_email_type()
    kwargs: dict = {
        "email_type": email_type.value,
        "from_address": EmailConfig.get_email_from_address(),
        "from_name": EmailConfig.get_email_from_name(),
    }
    if email_type == EmailType.SMTP:
        kwargs.update(
            {
                "smtp_host": EmailConfig.get_smtp_host(),
                "smtp_port": EmailConfig.get_smtp_port(),
                "smtp_enc_type": EmailConfig.get_smtp_enc_type(),
                "smtp_auth_enabled": EmailConfig.is_smtp_auth_enabled(),
                "smtp_username": EmailConfig.get_smtp_username(),
                "smtp_password": EmailConfig.get_smtp_password(),
            }
        )
    return EmailSender(**kwargs)
