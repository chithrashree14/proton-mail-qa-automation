import uuid

import pytest

from config.settings import settings
from pages.compose_page import ComposePage
from pages.mailbox_page import MailboxPage


@pytest.mark.regression
@pytest.mark.p1
@pytest.mark.two_account
def test_email_with_attachment_arrives_with_attachment(receiver_driver, sender_driver, tmp_path):
    attachment = tmp_path / "qa-attach.txt"
    attachment.write_text("attachment content")
    subject = f"QA-ATTACH-{uuid.uuid4().hex[:8]}"

    sender_driver.execute_cdp_cmd("Page.bringToFront", {})
    sender = MailboxPage(sender_driver)
    sender.open_compose()

    compose = ComposePage(sender_driver).wait_until_open()
    compose.attach_file(attachment)
    compose.set_recipient(settings.receiver.email)
    compose.set_subject(subject)
    compose.set_body("Message with attachment")
    compose.wait_until_saved()
    compose.send()

    receiver = MailboxPage(receiver_driver)
    receiver.wait_for_message(subject, folder="inbox", timeout=60)
    assert receiver.has_attachment_icon(subject), "Received message shows no attachment icon"