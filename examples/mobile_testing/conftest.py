"""
Mobile Testing Fixtures.

Demonstrates fixture patterns for mobile test automation
including device management and platform-specific setup.
"""

import pytest
import os
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions


def pytest_addoption(parser):
    """Add command line options for mobile testing."""
    parser.addoption(
        "--platform",
        action="store",
        default="android",
        help="Mobile platform: android or ios"
    )
    parser.addoption(
        "--device",
        action="store",
        default="emulator",
        help="Device type: emulator, simulator, or real"
    )


@pytest.fixture(scope="session")
def platform(request):
    """Get target platform from command line."""
    return request.config.getoption("--platform")


@pytest.fixture(scope="session")
def appium_server():
    """Appium server URL."""
    return os.getenv("APPIUM_SERVER", "http://localhost:4723")


@pytest.fixture(scope="function")
def mobile_driver(request, platform, appium_server):
    """
    Create mobile driver based on platform.

    Handles both Android and iOS with appropriate capabilities.
    """
    if platform == "android":
        options = UiAutomator2Options()
        options.platform_name = "Android"
        options.device_name = os.getenv("ANDROID_DEVICE", "Pixel_6_API_33")
        options.platform_version = os.getenv("ANDROID_VERSION", "13.0")
        options.app = os.getenv("ANDROID_APP_PATH", "./apps/app-debug.apk")
        options.automation_name = "UiAutomator2"

        # Performance optimizations
        options.set_capability("skipServerInstallation", True)
        options.set_capability("noReset", False)
        options.set_capability("fullReset", False)

    elif platform == "ios":
        options = XCUITestOptions()
        options.platform_name = "iOS"
        options.device_name = os.getenv("IOS_DEVICE", "iPhone 14 Pro")
        options.platform_version = os.getenv("IOS_VERSION", "16.0")
        options.app = os.getenv("IOS_APP_PATH", "./apps/App.app")
        options.automation_name = "XCUITest"

        # iOS-specific
        options.set_capability("useNewWDA", False)

    else:
        raise ValueError(f"Unsupported platform: {platform}")

    driver = webdriver.Remote(appium_server, options=options)
    driver.implicitly_wait(10)

    yield driver

    # Cleanup
    driver.quit()


@pytest.fixture
def app_state(mobile_driver):
    """
    Fixture to manage app state between tests.

    Provides methods to reset or prepare app state.
    """
    class AppState:
        def __init__(self, driver):
            self.driver = driver

        def reset_app(self):
            """Reset app to initial state."""
            self.driver.reset()

        def clear_app_data(self):
            """Clear all app data."""
            self.driver.terminate_app(self.driver.current_package)
            self.driver.activate_app(self.driver.current_package)

        def background_app(self, seconds: int = 5):
            """Send app to background."""
            self.driver.background_app(seconds)

    return AppState(mobile_driver)
