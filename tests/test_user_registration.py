from playwright.sync_api import expect
import pytest

from config import Config
from pages.header_page import HeaderPage
from pages.registration_page import RegistrationPage
from utilities.random_data_util import RandomDataUtil

# @pytest.mark.skip(reason = 'Skipping the test for now')
@pytest.mark.smoke
@pytest.mark.datadriven
def test_user_registration(page):
    page.goto(Config.store_url)
    header_page = HeaderPage(page)
    registration_page = RegistrationPage(page)
    header_page.open_registration()

    random_data = RandomDataUtil()
    confirmation_message = registration_page.complete_registration(
        first_name=random_data.get_first_name(),
        last_name=random_data.get_last_name(),
        email=random_data.get_email(),
        telephone=random_data.get_phone_number(),
        password=random_data.get_password(),
    )
    expect(confirmation_message).to_have_text("Your Account Has Been Created!")
