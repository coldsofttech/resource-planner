from unittest.mock import ANY, MagicMock, patch

import pytest
from emailcore.mailer import EmailSender


def _make_sender(**kwargs) -> EmailSender:
    defaults = {"email_type": "console", "from_address": "sender@example.com"}
    defaults.update(kwargs)
    return EmailSender(**defaults)


def _make_smtp_sender(**kwargs) -> EmailSender:
    defaults = {
        "email_type": "smtp",
        "from_address": "sender@example.com",
        "smtp_host": "smtp.example.com",
        "smtp_port": 587,
        "smtp_enc_type": "none",
    }
    defaults.update(kwargs)
    return EmailSender(**defaults)


def _mock_msg() -> MagicMock:
    m = MagicMock()
    m.as_string.return_value = "raw message"
    return m


# ---------------------------------------------------------------------------
# __init__
# ---------------------------------------------------------------------------


class TestEmailSenderInit:
    def test_stores_email_type(self):
        assert _make_sender(email_type="console").email_type == "console"

    def test_stores_from_address(self):
        assert (
            _make_sender(from_address="alice@example.com").from_address
            == "alice@example.com"
        )

    def test_from_name_defaults_to_from_address(self):
        sender = _make_sender(from_address="alice@example.com")
        assert sender.from_name == "alice@example.com"

    def test_explicit_from_name_stored(self):
        sender = _make_sender(from_address="alice@example.com", from_name="Alice")
        assert sender.from_name == "Alice"

    def test_smtp_port_coerced_to_int(self):
        sender = _make_sender(smtp_port="465")
        assert sender.smtp_port == 465
        assert isinstance(sender.smtp_port, int)

    def test_smtp_enc_type_stored_as_lowercase(self):
        sender = _make_sender(smtp_enc_type="STARTTLS")
        assert sender.smtp_enc_type == "starttls"

    def test_default_smtp_port_is_587(self):
        assert _make_sender().smtp_port == 587

    def test_default_smtp_auth_is_disabled(self):
        assert _make_sender().smtp_auth_enabled is False


# ---------------------------------------------------------------------------
# send — dispatch and recipient building
# ---------------------------------------------------------------------------


class TestEmailSenderSendDispatch:
    def test_routes_console_email_type_to_send_console(self):
        sender = _make_sender(email_type="console")
        with patch.object(sender, "_send_console") as mock_console:
            sender.send(to="a@b.com", subject="s", body="b")
        mock_console.assert_called_once()

    def test_routes_smtp_email_type_to_send_smtp(self):
        sender = _make_smtp_sender()
        with (
            patch.object(sender, "_send_smtp") as mock_smtp,
            patch.object(sender, "_build_message", return_value=MagicMock()),
        ):
            sender.send(to="a@b.com", subject="s", body="b")
        mock_smtp.assert_called_once()

    def test_raises_value_error_for_unknown_email_type(self):
        sender = _make_sender(email_type="pigeon")
        with pytest.raises(ValueError, match="pigeon"):
            sender.send(to="a@b.com", subject="s", body="b")

    def test_wraps_string_to_in_list(self):
        sender = _make_sender(email_type="console")
        with patch.object(sender, "_send_console") as mock_console:
            sender.send(to="a@b.com", subject="s", body="b")
        assert mock_console.call_args.kwargs["recipients"] == ["a@b.com"]

    def test_passes_list_to_unchanged(self):
        sender = _make_sender(email_type="console")
        with patch.object(sender, "_send_console") as mock_console:
            sender.send(to=["a@b.com", "c@d.com"], subject="s", body="b")
        assert mock_console.call_args.kwargs["recipients"] == ["a@b.com", "c@d.com"]

    def test_wraps_string_cc_in_list(self):
        sender = _make_sender(email_type="console")
        with patch.object(sender, "_send_console") as mock_console:
            sender.send(to="a@b.com", subject="s", body="b", cc="cc@b.com")
        assert mock_console.call_args.kwargs["cc"] == ["cc@b.com"]

    def test_none_cc_becomes_empty_list(self):
        sender = _make_sender(email_type="console")
        with patch.object(sender, "_send_console") as mock_console:
            sender.send(to="a@b.com", subject="s", body="b", cc=None)
        assert mock_console.call_args.kwargs["cc"] == []

    def test_wraps_string_bcc_in_list(self):
        sender = _make_sender(email_type="console")
        with patch.object(sender, "_send_console") as mock_console:
            sender.send(to="a@b.com", subject="s", body="b", bcc="bcc@b.com")
        assert mock_console.call_args.kwargs["bcc"] == ["bcc@b.com"]

    def test_none_bcc_becomes_empty_list(self):
        sender = _make_sender(email_type="console")
        with patch.object(sender, "_send_console") as mock_console:
            sender.send(to="a@b.com", subject="s", body="b", bcc=None)
        assert mock_console.call_args.kwargs["bcc"] == []

    def test_smtp_recipients_include_to_cc_and_bcc(self):
        sender = _make_smtp_sender()
        with (
            patch.object(sender, "_send_smtp") as mock_smtp,
            patch.object(sender, "_build_message", return_value=MagicMock()),
        ):
            sender.send(
                to="a@b.com", subject="s", body="b", cc="cc@b.com", bcc="bcc@b.com"
            )
        recipients = mock_smtp.call_args.args[1]
        assert "a@b.com" in recipients
        assert "cc@b.com" in recipients
        assert "bcc@b.com" in recipients


# ---------------------------------------------------------------------------
# _from_header
# ---------------------------------------------------------------------------


class TestEmailSenderFromHeader:
    def test_returns_name_and_address_when_from_name_differs(self):
        sender = _make_sender(from_address="alice@example.com", from_name="Alice Smith")
        assert sender._from_header() == "Alice Smith <alice@example.com>"

    def test_returns_address_as_display_name_when_from_name_not_provided(self):
        # from_name defaults to from_address, so result is "addr <addr>"
        sender = _make_sender(from_address="alice@example.com")
        assert sender._from_header() == "alice@example.com <alice@example.com>"


# ---------------------------------------------------------------------------
# _build_message
# ---------------------------------------------------------------------------


class TestEmailSenderBuildMessage:
    def _build(self, **kwargs):
        sender = _make_sender(from_address="sender@example.com", from_name="Sender")
        defaults = {"to": ["a@b.com"], "subject": "Test Subject", "body": "Hello"}
        defaults.update(kwargs)
        return sender._build_message(**defaults)

    def test_subject_header_set_correctly(self):
        assert self._build(subject="My Subject")["Subject"] == "My Subject"

    def test_from_header_uses_from_header_method(self):
        sender = _make_sender(from_address="alice@example.com", from_name="Alice")
        msg = sender._build_message(to=["b@b.com"], subject="s", body="b")
        assert msg["From"] == "Alice <alice@example.com>"

    def test_to_header_is_comma_joined(self):
        msg = self._build(to=["a@b.com", "c@d.com"])
        assert msg["To"] == "a@b.com, c@d.com"

    def test_cc_header_set_when_cc_provided(self):
        msg = self._build(cc=["cc@b.com"])
        assert msg["Cc"] == "cc@b.com"

    def test_cc_header_absent_when_cc_not_provided(self):
        msg = self._build(cc=None)
        assert msg["Cc"] is None

    def test_plain_text_part_present_and_correct(self):
        msg = self._build(body="plain content")
        alt = msg.get_payload()[0]
        text_part = alt.get_payload()[0]
        assert text_part.get_content_type() == "text/plain"
        assert "plain content" in text_part.get_payload(decode=True).decode()

    def test_html_part_attached_when_html_body_provided(self):
        msg = self._build(html_body="<b>hello</b>")
        alt = msg.get_payload()[0]
        html_part = alt.get_payload()[1]
        assert html_part.get_content_type() == "text/html"
        assert "<b>hello</b>" in html_part.get_payload(decode=True).decode()

    def test_html_part_absent_when_html_body_is_empty(self):
        msg = self._build(html_body="")
        alt = msg.get_payload()[0]
        assert len(alt.get_payload()) == 1

    def test_attachment_filename_in_content_disposition(self):
        msg = self._build(attachments=[{"filename": "report.pdf", "data": b"data"}])
        attachment_part = msg.get_payload()[1]
        assert 'filename="report.pdf"' in attachment_part.get("Content-Disposition", "")

    def test_attachment_data_survives_base64_roundtrip(self):
        raw = b"binarydata"
        msg = self._build(attachments=[{"filename": "f.bin", "data": raw}])
        attachment_part = msg.get_payload()[1]
        assert attachment_part.get_payload(decode=True) == raw

    def test_no_attachment_parts_when_attachments_is_none(self):
        msg = self._build(attachments=None)
        assert len(msg.get_payload()) == 1

    def test_top_level_message_is_multipart_mixed(self):
        assert self._build().get_content_type() == "multipart/mixed"


# ---------------------------------------------------------------------------
# _send_console
# ---------------------------------------------------------------------------


class TestEmailSenderConsole:
    def _send(self, capsys, **kwargs):
        sender = _make_sender(from_address="sender@example.com", from_name="Sender")
        defaults = {
            "recipients": ["to@example.com"],
            "subject": "Hello",
            "body": "Body text",
        }
        defaults.update(kwargs)
        sender._send_console(**defaults)
        return capsys.readouterr().out

    def test_from_address_in_output(self, capsys):
        assert "sender@example.com" in self._send(capsys)

    def test_to_recipient_in_output(self, capsys):
        assert "to@example.com" in self._send(capsys)

    def test_subject_in_output(self, capsys):
        assert "My Subject" in self._send(capsys, subject="My Subject")

    def test_cc_printed_when_provided(self, capsys):
        assert "cc@example.com" in self._send(capsys, cc=["cc@example.com"])

    def test_cc_not_printed_when_absent(self, capsys):
        assert "Cc:" not in self._send(capsys, cc=None)

    def test_bcc_printed_when_provided(self, capsys):
        assert "bcc@example.com" in self._send(capsys, bcc=["bcc@example.com"])

    def test_bcc_not_printed_when_absent(self, capsys):
        assert "Bcc:" not in self._send(capsys, bcc=None)

    def test_body_lines_in_output(self, capsys):
        out = self._send(capsys, body="Line one\nLine two")
        assert "Line one" in out
        assert "Line two" in out

    def test_separator_lines_in_output(self, capsys):
        assert "---" in self._send(capsys)


# ---------------------------------------------------------------------------
# _send_smtp
# ---------------------------------------------------------------------------


class TestEmailSenderSmtp:
    def test_uses_smtp_ssl_for_ssl_enc_type(self):
        sender = _make_smtp_sender(
            smtp_enc_type="ssl", smtp_host="mail.example.com", smtp_port=465
        )
        with patch("emailcore.mailer.smtplib.SMTP_SSL") as mock_ssl:
            sender._send_smtp(_mock_msg(), ["a@b.com"])
        mock_ssl.assert_called_once_with("mail.example.com", 465, context=ANY)

    def test_uses_plain_smtp_for_none_enc_type(self):
        sender = _make_smtp_sender(
            smtp_enc_type="none", smtp_host="mail.example.com", smtp_port=25
        )
        with patch("emailcore.mailer.smtplib.SMTP") as mock_smtp_cls:
            sender._send_smtp(_mock_msg(), ["a@b.com"])
        mock_smtp_cls.assert_called_once_with("mail.example.com", 25)

    def test_starttls_sequence_called_for_starttls_enc_type(self):
        sender = _make_smtp_sender(smtp_enc_type="starttls")
        with patch("emailcore.mailer.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = mock_smtp_cls.return_value
            sender._send_smtp(_mock_msg(), ["a@b.com"])
        mock_smtp.ehlo.assert_called()
        mock_smtp.starttls.assert_called_once_with(context=ANY)

    def test_no_starttls_called_for_none_enc_type(self):
        sender = _make_smtp_sender(smtp_enc_type="none")
        with patch("emailcore.mailer.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = mock_smtp_cls.return_value
            sender._send_smtp(_mock_msg(), ["a@b.com"])
        mock_smtp.starttls.assert_not_called()

    def test_login_called_when_auth_enabled(self):
        sender = _make_smtp_sender(
            smtp_auth_enabled=True, smtp_username="user", smtp_password="pass"
        )
        with patch("emailcore.mailer.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = mock_smtp_cls.return_value
            sender._send_smtp(_mock_msg(), ["a@b.com"])
        mock_smtp.login.assert_called_once_with("user", "pass")

    def test_login_not_called_when_auth_disabled(self):
        sender = _make_smtp_sender(smtp_auth_enabled=False)
        with patch("emailcore.mailer.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = mock_smtp_cls.return_value
            sender._send_smtp(_mock_msg(), ["a@b.com"])
        mock_smtp.login.assert_not_called()

    def test_sendmail_called_with_correct_from_recipients_and_body(self):
        sender = _make_smtp_sender(from_address="sender@example.com")
        msg = _mock_msg()
        with patch("emailcore.mailer.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = mock_smtp_cls.return_value
            sender._send_smtp(msg, ["a@b.com", "b@c.com"])
        mock_smtp.sendmail.assert_called_once_with(
            "sender@example.com", ["a@b.com", "b@c.com"], "raw message"
        )

    def test_quit_called_after_successful_send(self):
        sender = _make_smtp_sender()
        with patch("emailcore.mailer.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = mock_smtp_cls.return_value
            sender._send_smtp(_mock_msg(), ["a@b.com"])
        mock_smtp.quit.assert_called_once()

    def test_quit_called_even_when_sendmail_raises(self):
        sender = _make_smtp_sender()
        with patch("emailcore.mailer.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = mock_smtp_cls.return_value
            mock_smtp.sendmail.side_effect = Exception("SMTP error")
            with pytest.raises(Exception, match="SMTP error"):
                sender._send_smtp(_mock_msg(), ["a@b.com"])
        mock_smtp.quit.assert_called_once()

    def test_quit_exception_is_swallowed(self):
        sender = _make_smtp_sender()
        with patch("emailcore.mailer.smtplib.SMTP") as mock_smtp_cls:
            mock_smtp = mock_smtp_cls.return_value
            mock_smtp.quit.side_effect = Exception("connection reset")
            sender._send_smtp(_mock_msg(), ["a@b.com"])  # must not raise
