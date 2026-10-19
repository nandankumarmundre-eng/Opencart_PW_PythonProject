from playwright.sync_api import Locator, Page


class LoginPage:
    def __init__(self, page: Page):
        self.page = page
        self.email_field = page.locator("#input-email")
        self.password_field = page.locator("#input-password")
        self.login_button = page.get_by_role("button", name="Login")
        self.login_error_message = page.locator(
            "#account-login .alert.alert-danger, #content .alert.alert-danger"
        )

    def login(self, email: str, password: str) -> None:
        self.email_field.fill(email)
        self.password_field.fill(password)
        self.login_button.click()

    def get_login_error_message(self) -> Locator:
        return self.login_error_message
