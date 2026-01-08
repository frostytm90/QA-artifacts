"""
Flutter App Testing - Appium with Flutter Finder.

Demonstrates my approach to testing Flutter applications
using appium-flutter-finder for widget-based element location.
"""

import pytest
import os
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium_flutter_finder.flutter_finder import FlutterFinder, FlutterElement


# Load credentials from environment - never hardcode
TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "")
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "")


class FlutterDriver:
    """Extended driver for Flutter app testing."""

    def __init__(self, driver: webdriver.Remote):
        self.driver = driver
        self.finder = FlutterFinder(driver)

    def find_by_key(self, key: str) -> FlutterElement:
        """Find Flutter widget by ValueKey."""
        return self.finder.by_value_key(key)

    def find_by_text(self, text: str) -> FlutterElement:
        """Find Flutter widget by text content."""
        return self.finder.by_text(text)

    def find_by_type(self, widget_type: str) -> FlutterElement:
        """Find Flutter widget by type (e.g., 'TextField')."""
        return self.finder.by_type(widget_type)

    def find_by_semantics_label(self, label: str) -> FlutterElement:
        """Find Flutter widget by semantics label."""
        return self.finder.by_semantics_label(label)

    def tap(self, element: FlutterElement) -> None:
        """Tap on a Flutter element."""
        element.click()

    def enter_text(self, element: FlutterElement, text: str) -> None:
        """Enter text into a Flutter TextField."""
        element.send_keys(text)

    def scroll_until_visible(
        self,
        scroll_view_key: str,
        target_key: str,
        max_scrolls: int = 10
    ) -> FlutterElement:
        """Scroll within a Flutter ScrollView until target is visible."""
        scroll_view = self.find_by_key(scroll_view_key)

        for _ in range(max_scrolls):
            try:
                target = self.find_by_key(target_key)
                if target.is_displayed():
                    return target
            except Exception:
                pass

            # Scroll down
            self.finder.scroll(scroll_view, delta_x=0, delta_y=-300)

        raise Exception(f"Element {target_key} not found after scrolling")


class TestFlutterLogin:
    """Test suite for Flutter app login functionality."""

    @pytest.fixture
    def flutter_driver(self, mobile_driver):
        """Provide Flutter-enabled driver."""
        return FlutterDriver(mobile_driver)

    def test_login_with_valid_credentials(self, flutter_driver):
        """Test successful login in Flutter app."""
        # Find widgets by ValueKey (set in Flutter code)
        username_field = flutter_driver.find_by_key("username_input")
        password_field = flutter_driver.find_by_key("password_input")
        login_button = flutter_driver.find_by_key("login_button")

        # Perform login - credentials loaded from environment
        flutter_driver.enter_text(username_field, TEST_USER_EMAIL)
        flutter_driver.enter_text(password_field, TEST_USER_PASSWORD)
        flutter_driver.tap(login_button)

        # Verify navigation to home screen
        home_title = flutter_driver.find_by_key("home_screen_title")
        assert home_title.text == "Welcome"

    def test_login_validation_error(self, flutter_driver):
        """Test validation error display."""
        login_button = flutter_driver.find_by_key("login_button")

        # Submit empty form
        flutter_driver.tap(login_button)

        # Verify error message
        error_text = flutter_driver.find_by_key("error_message")
        assert "required" in error_text.text.lower()

    def test_scroll_to_terms_link(self, flutter_driver):
        """Test scrolling to find an element."""
        terms_link = flutter_driver.scroll_until_visible(
            scroll_view_key="login_scroll_view",
            target_key="terms_and_conditions_link"
        )

        flutter_driver.tap(terms_link)

        # Verify navigation
        terms_title = flutter_driver.find_by_key("terms_page_title")
        assert terms_title.is_displayed()
