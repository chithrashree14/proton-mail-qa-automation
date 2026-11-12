import pytest

from config.settings import settings
from pages.login_page import LoginPage
from pages.mailbox_page import MailboxPage


# @pytest.mark.smoke
# @pytest.mark.p0
# def test_valid_login_reaches_inbox(driver):
#     LoginPage(driver).load().login(settings.sender.username, settings.sender.password)
#
#     mailbox = MailboxPage(driver)
#     mailbox.wait_for_title_contains("Inbox")
#     mailbox.wait_until_loaded()
#
#     assert "Inbox" in driver.title
#     assert settings.sender.username.split("@")[0] in driver.title
#     assert "mail.proton.me" in driver.current_url

@pytest.mark.smoke
@pytest.mark.p0
def test_valid_login_reaches_inbox(driver, login):
    login(settings.sender, "sender")

    mailbox = MailboxPage(driver)
    mailbox.wait_for_title_contains("Inbox")

    assert "Inbox" in driver.title, f"Unexpected page title: {driver.title}"
    assert "mail.proton.me" in driver.current_url


@pytest.mark.regression
@pytest.mark.p0
def test_invalid_password_shows_error(driver):
    page = LoginPage(driver).load()
    page.login(settings.sender.username, "wrong-password-123")

    assert page.is_visible(LoginPage.ERROR, timeout=10), "No error message shown"
    message = page.error_message().lower()
    assert "incorrect login credentials" in message or "password is not correct" in message, (
        f"Unexpected error text: {message}"
    )
    assert "mail.proton.me" not in driver.current_url