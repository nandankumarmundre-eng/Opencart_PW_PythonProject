from playwright.sync_api import expect
import pytest

from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage

@pytest.mark.regression
@pytest.mark.smoke
def test_product_search(page):
    product_name = "iPhone"
    home_page = HomePage(page)
    search_results_page = SearchResultsPage(page)

    expect(home_page.search_field).to_be_visible()
    home_page.search_for_product(product_name)

    expect(page).to_have_url(
        f"https://tutorialsninja.com/demo/index.php?route=product/search&search={product_name}"        
    )
    expect(search_results_page.page_heading).to_have_text(
        f"Search - {product_name}"
    )
    assert search_results_page.is_product_exist(product_name), (
        f"Product '{product_name}' was not found in the search results"
    )
