from playwright.sync_api import Page


class HomePage:
    def __init__(self, page: Page):
        self.page = page
        self.store_logo = page.get_by_role("link", name="Your Store", exact=True)
        self.search_field = page.locator("#search input[name='search']")
        self.search_button = page.locator("#search button")

    def go_to_home(self) -> None:
        self.store_logo.click()
        
    def search_for_product(self, product_name: str) -> None:
        self.search_field.fill(product_name)
        self.search_button.click()
