from playwright.sync_api import Locator, Page


class MyAccountPage:
    def __init__(self, page: Page):
        self.page = page
        self.my_account_section = page.locator("#content").get_by_role(
            "heading", name="My Account", exact=True
        )

    def get_my_account_section(self) -> Locator:
        return self.my_account_section