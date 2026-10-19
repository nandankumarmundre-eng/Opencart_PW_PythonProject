import re
import pytest

from playwright.sync_api import expect
from config import Config
from pages.header_page import HeaderPage
from pages.login_page import LoginPage
from pages.logout_page import LogoutPage
from pages.my_account_page import MyAccountPage

@pytest.mark.skip(reason = 'Skipping the test for now')
@pytest.mark.end_to_end
@pytest.mark.regression
@pytest.mark.sanity
def test_login_with_valid_credentails(page):
    assert Config.email and Config.password, "Login credentials are missing from config.Config"
    page.goto(Config.store_url)

    header_page = HeaderPage(page)
    login_page = LoginPage(page)
    my_account_page = MyAccountPage(page)
    logout_page = LogoutPage(page)

    header_page.open_login()
    login_page.login(Config.email, Config.password)
    expect(page).to_have_url(re.compile(r".*route=account/account(?:&|$)"))
    expect(my_account_page.get_my_account_section()).to_be_visible()

    header_page.logout()
    expect(page).to_have_url(re.compile(r".*route=account/logout(?:&|$)"))
    expect(logout_page.get_logout_message()).to_contain_text(
        "You have been logged off your account."
    )
@pytest.mark.skip(reason = 'Skipping the test for now')
@pytest.mark.end_to_end
@pytest.mark.smoke
def test_login_with_invalid_credentails(page):
    page.goto(Config.store_url)
    header_page = HeaderPage(page)
    login_page = LoginPage(page)
    header_page.open_login()
    login_page.login(Config.invalid_email, Config.invalid_password)

    expect(login_page.get_login_error_message()).to_contain_text(
        re.compile(
            r"Warning: (?:No match for E-Mail Address and/or Password|"
            r"Your account has exceeded allowed number of login attempts)\."
        )
    )
