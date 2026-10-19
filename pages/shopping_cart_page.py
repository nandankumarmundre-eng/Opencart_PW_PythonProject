from playwright.sync_api import Locator, Page


class ShoppingCartPage:
    def __init__(self, page: Page):
        self.page = page
        self.page_heading = page.locator("#content").get_by_role(
            "heading", name="Shopping Cart", exact=True
        )
        self.empty_cart_message = page.locator(
            "#content p", has_text="Your shopping cart is empty!"
        )
        self.cart_items = page.locator("#content .table-responsive tbody tr")

    def get_empty_cart_message(self) -> Locator:
        return self.empty_cart_message

    def get_cart_items(self) -> Locator:
        return self.cart_items