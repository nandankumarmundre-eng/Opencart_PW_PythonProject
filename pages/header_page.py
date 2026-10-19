from playwright.sync_api import Locator, Page


class HeaderPage:
    def __init__(self, page: Page):
        self.page = page
        self.my_account_menu = page.locator(
            "#top-links a.dropdown-toggle[title='My Account']"
        )
        self.login_link = page.locator("#top-links").get_by_role(
            "link", name="Login", exact=True
        )
        self.register_link = page.locator("#top-links").get_by_role(
            "link", name="Register", exact=True
        )
        self.logout_link = page.locator("#top-links").get_by_role(
            "link", name="Logout", exact=True
        )
        self.search_field = page.get_by_role("textbox", name="Search")
        self.search_button = page.locator("#search button")

    def open_login(self) -> None:
        self.my_account_menu.click()
        self.login_link.click()

    def open_registration(self) -> None:
        self.my_account_menu.click()
        self.register_link.click()

    def logout(self) -> None:
        self.my_account_menu.click()
        self.logout_link.click()

    def search(self, product_name: str) -> None:
        self.search_field.fill(product_name)
        self.search_button.click()

    def get_search_field(self) -> Locator:
        return self.search_field
