from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from base_page import BasePage


class LoginPage(BasePage):

    # locators
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    REMEMBER_ME_CHECKBOX = (By.ID, "remember-me")

    URL = "/login"

    def __init__(self, driver: WebDriver):
        super().__init__(driver)

    def navigate(self) -> "LoginPage":
        self.driver.get(f"{self.base_url}{self.URL}")
        return self

    def enter_username(self, username: str) -> "LoginPage":
        self.type_text(self.USERNAME_INPUT, username)
        return self

    def enter_password(self, password: str) -> "LoginPage":
        self.type_text(self.PASSWORD_INPUT, password)
        return self

    def click_login(self) -> None:
        self.click(self.LOGIN_BUTTON)

    def check_remember_me(self) -> "LoginPage":
        self.click(self.REMEMBER_ME_CHECKBOX)
        return self

    def login(self, username: str, password: str) -> None:
        """do the whole login flow"""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()

    def get_error_message(self) -> str:
        return self.get_text(self.ERROR_MESSAGE)

    def is_error_displayed(self) -> bool:
        return self.is_visible(self.ERROR_MESSAGE, timeout=3)

    def is_login_page(self) -> bool:
        return self.is_visible(self.LOGIN_BUTTON)
