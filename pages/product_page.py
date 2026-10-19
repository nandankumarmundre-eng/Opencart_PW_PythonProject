from playwright.sync_api import Page


class ProductPage:
    def __init__(self, page: Page):
        self.page = page
        self.product_heading = page.locator("#content h1")
        self.quantity_field = page.locator("#input-quantity")
        self.add_to_cart_button = page.get_by_role(
            "button", name="Add to Cart", exact=True
        )

    def set_quantity(self, quantity: int) -> None:
        self.quantity_field.fill(str(quantity))

    def add_to_cart(self) -> None:
        self.add_to_cart_button.click()

