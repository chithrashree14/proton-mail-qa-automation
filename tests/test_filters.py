import uuid

import pytest

from config.settings import settings
from pages.compose_page import ComposePage
from pages.filters_page import FiltersPage
from pages.mailbox_page import MailboxPage


@pytest.mark.regression
@pytest.mark.p1
def test_filter_stars_matching_incoming_message(sender_driver):
    token = f"qafilt{uuid.uuid4().hex[:8]}"
    subject = f"QA-{token}-message"

    filters = FiltersPage(sender_driver)
    filters.delete_qa_filters()          # clear leftovers from earlier runs
    filters.load()

    try:
        filters.create_filter_that_stars(name=f"QA filter {token}", keyword=token)
        filters.back_to_mailbox()

        mailbox = MailboxPage(sender_driver).wait_until_loaded(timeout=60)
        mailbox.open_compose()
        ComposePage(sender_driver).compose_and_send(settings.sender.email, subject, "Filter test")
        mailbox.wait_for_message(subject, folder="inbox", timeout=60)

        # Nobody starred it. If the filter works, it must already be in Starred.
        mailbox.open_folder("starred")
        mailbox.wait_for_message(subject, folder="starred", timeout=60)
        assert mailbox.has_message(subject), "Filter did not star the matching message"

    finally:
        try:
            filters.delete_qa_filters()
        except Exception as exc:
            print(f"FILTER CLEANUP FAILED: {exc}")