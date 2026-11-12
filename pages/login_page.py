from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from config.settings import settings
from pages.base_page import BasePage

LOGIN_PAGE_TIMEOUT = 40


class LoginPage(BasePage):
    USERNAME = (By.ID, "username")
    PASSWORD = (By.ID, "password")
    SUBMIT = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR = (
        By.XPATH,
        "//*[contains(text(), 'password is not correct') or contains(text(), 'Incorrect login credentials')]",
    )

    def load(self):
        """Open the login page. Proton's login app sometimes hangs on a loading splash,
        so allow a long first wait and reload once before failing."""
        self.open(settings.login_url)
        long_wait = WebDriverWait(self.driver, LOGIN_PAGE_TIMEOUT)
        try:
            long_wait.until(EC.visibility_of_element_located(self.USERNAME))
        except TimeoutException:
            self.driver.refresh()
            long_wait.until(EC.visibility_of_element_located(self.USERNAME))
        return self

    def login(self, username, password):
        self.type(self.USERNAME, username)
        self.click(self.SUBMIT)
        self.type(self.PASSWORD, password)
        self.click(self.SUBMIT)

    def error_message(self):
        return self.text_of(self.ERROR)