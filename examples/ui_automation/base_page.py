"""Base page object"""

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class BasePage:

    def __init__(self, driver: WebDriver, timeout: int = 10):
        self.driver = driver
        self.timeout = timeout
        self.wait = WebDriverWait(driver, timeout)

    def find_element(self, locator: tuple) -> WebElement:
        return self.wait.until(EC.presence_of_element_located(locator))

    def find_elements(self, locator: tuple) -> list[WebElement]:
        return self.wait.until(EC.presence_of_all_elements_located(locator))

    def click(self, locator: tuple) -> None:
        element = self.wait.until(EC.element_to_be_clickable(locator))
        element.click()

    def type_text(self, locator: tuple, text: str, clear: bool = True) -> None:
        element = self.find_element(locator)
        if clear:
            element.clear()
        element.send_keys(text)

    def get_text(self, locator: tuple) -> str:
        return self.find_element(locator).text

    def is_visible(self, locator: tuple, timeout: int = None) -> bool:
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            wait.until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def wait_for_url_contains(self, partial_url: str) -> bool:
        return self.wait.until(EC.url_contains(partial_url))

    # TODO: move this to a utils module
    def take_screenshot(self, name: str) -> str:
        filepath = f"screenshots/{name}.png"
        self.driver.save_screenshot(filepath)
        return filepath
