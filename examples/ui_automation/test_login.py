import pytest
from login_page import LoginPage
from dashboard_page import DashboardPage


class TestLogin:

    def test_successful_login(self, browser, test_user):
        login_page = LoginPage(browser)
        dashboard = DashboardPage(browser)

        login_page.navigate()
        login_page.login(test_user.username, test_user.password)

        assert dashboard.is_dashboard_loaded(), "should be on dashboard"
        assert dashboard.get_username() == test_user.display_name

    def test_login_invalid_password(self, browser, test_user):
        login_page = LoginPage(browser)

        login_page.navigate()
        login_page.login(test_user.username, "intentionally_wrong_password")

        assert login_page.is_error_displayed()
        assert "Invalid credentials" in login_page.get_error_message()

    def test_login_empty_fields(self, browser):
        login_page = LoginPage(browser)

        login_page.navigate()
        login_page.click_login()  # submit without filling

        assert login_page.is_error_displayed()
        assert "required" in login_page.get_error_message().lower()

    @pytest.mark.parametrize("username,password,error_msg", [
        ("", "any_password", "Username is required"),
        ("user@test.com", "", "Password is required"),
        ("invalid-email", "any_password", "Invalid email format"),
    ])
    def test_login_validation(self, browser, username, password, error_msg):
        login_page = LoginPage(browser)

        login_page.navigate()
        login_page.login(username, password)

        assert login_page.is_error_displayed()
        assert error_msg in login_page.get_error_message()

    # FIXME: this test is flaky on CI, needs investigation
    @pytest.mark.skip(reason="flaky - session handling issue")
    def test_remember_me(self, browser, test_user):
        login_page = LoginPage(browser)

        login_page.navigate()
        login_page.check_remember_me()
        login_page.login(test_user.username, test_user.password)

        browser.delete_all_cookies()
        browser.refresh()

        dashboard = DashboardPage(browser)
        assert dashboard.is_dashboard_loaded()


class TestLogout:

    def test_logout(self, browser, authenticated_user):
        dashboard = DashboardPage(browser)
        login_page = LoginPage(browser)

        dashboard.click_logout()

        assert login_page.is_login_page()

    def test_session_cleared_after_logout(self, browser, authenticated_user):
        dashboard = DashboardPage(browser)

        dashboard.click_logout()

        # try accessing protected page directly
        browser.get("/dashboard")

        login_page = LoginPage(browser)
        assert login_page.is_login_page()
