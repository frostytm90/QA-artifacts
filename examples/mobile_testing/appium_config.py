"""
Appium Configuration - Mobile test framework setup.

Demonstrates the Appium framework configuration I set up
for iOS and Android testing.
"""

from dataclasses import dataclass
from typing import Optional
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions


@dataclass
class DeviceConfig:
    """Device configuration for mobile testing."""
    platform_name: str
    device_name: str
    platform_version: str
    app_path: str
    automation_name: str
    udid: Optional[str] = None


class AppiumDriver:
    """Factory for creating Appium driver instances."""

    APPIUM_SERVER = "http://localhost:4723"

    # Predefined device configurations
    ANDROID_EMULATOR = DeviceConfig(
        platform_name="Android",
        device_name="Pixel_6_API_33",
        platform_version="13.0",
        app_path="./apps/app-debug.apk",
        automation_name="UiAutomator2"
    )

    IOS_SIMULATOR = DeviceConfig(
        platform_name="iOS",
        device_name="iPhone 14 Pro",
        platform_version="16.0",
        app_path="./apps/App.app",
        automation_name="XCUITest"
    )

    @classmethod
    def create_android_driver(
        cls,
        config: DeviceConfig = None
    ) -> webdriver.Remote:
        """Create Android Appium driver."""
        config = config or cls.ANDROID_EMULATOR

        options = UiAutomator2Options()
        options.platform_name = config.platform_name
        options.device_name = config.device_name
        options.platform_version = config.platform_version
        options.app = config.app_path
        options.automation_name = config.automation_name

        # Performance optimizations
        options.set_capability("skipServerInstallation", True)
        options.set_capability("skipDeviceInitialization", True)
        options.set_capability("noReset", True)

        return webdriver.Remote(cls.APPIUM_SERVER, options=options)

    @classmethod
    def create_ios_driver(
        cls,
        config: DeviceConfig = None
    ) -> webdriver.Remote:
        """Create iOS Appium driver."""
        config = config or cls.IOS_SIMULATOR

        options = XCUITestOptions()
        options.platform_name = config.platform_name
        options.device_name = config.device_name
        options.platform_version = config.platform_version
        options.app = config.app_path
        options.automation_name = config.automation_name

        # iOS-specific settings
        options.set_capability("useNewWDA", False)
        options.set_capability("wdaStartupRetries", 3)

        return webdriver.Remote(cls.APPIUM_SERVER, options=options)

    @classmethod
    def create_driver(cls, platform: str) -> webdriver.Remote:
        """Create driver based on platform."""
        if platform.lower() == "android":
            return cls.create_android_driver()
        elif platform.lower() == "ios":
            return cls.create_ios_driver()
        else:
            raise ValueError(f"Unsupported platform: {platform}")
