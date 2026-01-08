import pytest
import os
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions


@dataclass
class TestUser:
    username: str
    password: str
    display_name: str


@pytest.fixture(scope="session")
def config():
    return {
        "base_url": os.getenv("BASE_URL", "http://localhost:8080"),
        "implicit_wait": int(os.getenv("IMPLICIT_WAIT", "10")),
        "headless": os.getenv("HEADLESS", "true").lower() == "true",
    }


@pytest.fixture(params=["chrome", "firefox"])
def browser(request, config):
    browser_name = request.param

    if browser_name == "chrome":
        options = ChromeOptions()
        if config["headless"]:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(options=options)

    elif browser_name == "firefox":
        options = FirefoxOptions()
        if config["headless"]:
            options.add_argument("--headless")
        driver = webdriver.Firefox(options=options)

    else:
        raise ValueError(f"Unsupported browser: {browser_name}")

    driver.implicitly_wait(config["implicit_wait"])
    driver.maximize_window()

    yield driver

    driver.quit()


@pytest.fixture
def test_user():
    return TestUser(
        username=os.getenv("TEST_USER_EMAIL", ""),
        password=os.getenv("TEST_USER_PASSWORD", ""),
        display_name=os.getenv("TEST_USER_NAME", "Test User")
    )


@pytest.fixture
def authenticated_user(browser, test_user):
    """already logged in browser session"""
    from login_page import LoginPage

    login_page = LoginPage(browser)
    login_page.navigate()
    login_page.login(test_user.username, test_user.password)

    yield browser


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """capture screenshot on failure"""
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        driver = item.funcargs.get("browser")
        if driver:
            screenshot_path = f"screenshots/{item.name}.png"
            driver.save_screenshot(screenshot_path)
            print(f"\nScreenshot: {screenshot_path}")
