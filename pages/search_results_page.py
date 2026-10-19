from playwright.sync_api import Error as PlaywrightError, Locator, Page


class SearchResultsPage:
    def __init__(self, page: Page):
        self.page = page
        self.product_cards = page.locator("#content .product-layout")
        self.page_heading = page.locator("#content h1")

    def get_product_cards(self) -> Locator:
        return self.product_cards

    def get_product(self, product_name: str) -> Locator:
        return self.product_cards.locator(".caption h4 a", has_text=product_name)

    def is_product_exist(self, product_name: str) -> bool:
        try:
            for index in range(self.product_cards.count()):
                product_title = self.product_cards.nth(index).locator(
                    ".caption h4 a"
                )
                if product_title.inner_text().strip().casefold() == product_name.casefold():
                    return True
            return False
        except PlaywrightError as error:
            raise RuntimeError(
                f"Could not inspect search results for product '{product_name}'"
            ) from error

    