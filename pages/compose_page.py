from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from pages.base_page import BasePage, by_testid
from pathlib import Path

class ComposePage(BasePage):
    TO = by_testid("composer:to")
    SUBJECT = by_testid("composer:subject")
    SEND = by_testid("composer:send-button")
    CLOSE = by_testid("composer:close-button")
    BODY_IFRAME = (By.CSS_SELECTOR, "iframe[data-testid='rooster-iframe']")
    BODY_EDITABLE = (By.CSS_SELECTOR, "[contenteditable='true']")
    SPOTLIGHT_CLOSE = by_testid("spotlight-inner-close-button")
    SAVED = (By.XPATH, "//*[@data-testid='composer-0']//*[contains(text(), 'Saved at')]")
    DELETE_DRAFT = by_testid("composer:delete-draft-button")
    CONFIRM_DELETE = (By.XPATH, "//button[normalize-space(.)='Delete']")
    COMPOSER = by_testid("composer-0")
    ATTACH_INPUT = by_testid("composer-attachments-button")
    NO_RECIPIENT_MODAL = by_testid("composer:modal:norecipients")
    NO_RECIPIENT_OK = (By.XPATH, "//*[@data-testid='composer:modal:norecipients']//button")
    INVALID_ADDRESS = (By.XPATH, "//*[contains(text(), 'not valid')]")

    def wait_until_open(self):
        self.visible(self.TO)
        if self.is_visible(self.SPOTLIGHT_CLOSE, timeout=2):
            self.click(self.SPOTLIGHT_CLOSE)
        return self

    def recipient_chip(self, address):
        local_part = address.split("@")[0]
        return (By.XPATH, f"//*[@data-testid='composer-0']//*[contains(text(), '{local_part}')]")

    def add_recipient_unchecked(self, address):
        field = self.visible(self.TO)
        field.click()
        field.send_keys(address)
        field.send_keys(Keys.ENTER)

    def set_recipient(self, address):
        self.add_recipient_unchecked(address)
        self.visible(self.recipient_chip(address))  # proves the recipient was accepted

    def click_send(self):
        self.click(self.SEND)

    def is_still_open(self, timeout=3):
        return self.is_visible(self.SEND, timeout=timeout)

    def set_subject(self, subject):
        self.type(self.SUBJECT, subject)

    def set_body(self, text):
        self.driver.execute_cdp_cmd("Page.bringToFront", {})
        iframe = self.visible(self.BODY_IFRAME)
        self.driver.switch_to.frame(iframe)
        try:
            body = self.wait.until(EC.visibility_of_element_located(self.BODY_EDITABLE))
            self.driver.execute_script("arguments[0].focus();", body)
            body.send_keys(text)
        finally:
            self.driver.switch_to.default_content()

    def send(self):
        self.click(self.SEND)
        self.wait.until(EC.invisibility_of_element_located(self.SEND))

    def compose_and_send(self, to, subject, body):
        self.wait_until_open()
        self.set_recipient(to)
        self.set_subject(subject)
        self.set_body(body)
        self.send()

    def wait_until_saved(self):
        self.visible(self.SAVED)

    def close(self):
        self.click(self.CLOSE)
        self.wait.until(lambda d: not d.find_elements(*self.COMPOSER))

    def subject_value(self):
        return self.visible(self.SUBJECT).get_attribute("value")

    def body_text(self):
        iframe = self.visible(self.BODY_IFRAME)
        self.driver.switch_to.frame(iframe)
        try:
            return self.wait.until(
                EC.visibility_of_element_located(self.BODY_EDITABLE)
            ).text
        finally:
            self.driver.switch_to.default_content()

    def delete_draft(self):
        self.click(self.DELETE_DRAFT)
        self.click(self.CONFIRM_DELETE)  # the confirmation is always shown, so it must be clicked
        self.wait.until(EC.invisibility_of_element_located(self.CONFIRM_DELETE))
        self.wait.until(lambda d: not d.find_elements(*self.COMPOSER))

    def attach_file(self, path):
        """Attach a file and wait until its name shows up in the composer."""
        self.find(self.ATTACH_INPUT).send_keys(str(path))
        self.wait_for(
            (
                By.XPATH,
                f"//*[@data-testid='composer-0']//*[contains(normalize-space(.), '{Path(path).stem}')]",
            ),
            timeout=30,
        )

    def dismiss_spotlight(self):
        """Close Proton's promotional pop-up if it is showing; it can sit on top of dialogs."""
        if self.is_visible(self.SPOTLIGHT_CLOSE, timeout=1):
            self.driver.execute_script(
                "arguments[0].click();", self.driver.find_element(*self.SPOTLIGHT_CLOSE)
            )

    def dismiss_no_recipient_dialog(self):
        self.dismiss_spotlight()
        button = self.visible(self.NO_RECIPIENT_OK)
        self.driver.execute_script("arguments[0].click();", button)
        self.wait.until(EC.invisibility_of_element_located(self.NO_RECIPIENT_MODAL))