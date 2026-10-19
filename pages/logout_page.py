from playwright.sync_api import Locator, Page


class LogoutPage:
    def __init__(self, page: Page):
        self.page = page
        self.logout_message = page.locator(
            "#content p", has_text="You have been logged off your account."
        )

    def get_logout_message(self) -> Locator:
        return self.logout_message
