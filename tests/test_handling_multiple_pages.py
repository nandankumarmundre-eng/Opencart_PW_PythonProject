# to understand how playwright browser context is perfoming the actions in another pages
from math import exp
import pytest

from playwright.sync_api import expect

from pages import ptnewhome_page
from pages.aphome_page import AphomePage
from pages.ptnewhome_page import PtnewhomePage
from utilities.random_data_util import RandomDataUtil

@pytest.mark.skip(reason='Skipping the test for now')
def test_validate_multiple_tabs(page):
    aphome_page = AphomePage(page)
    ptnewhome_page = PtnewhomePage(page)

    header_title = aphome_page.get_ap_title()
    expect(header_title).to_have_text('Automation Testing Practice')

    aphome_page.click_new_tab()
    pt_header_title = ptnewhome_page.get_pt_heading_title()
    expect(pt_header_title).to_be_visible()

    # ptnewhome_page.click_online_traning()
    # expect(page).to_have_url('https://www.pavanonlinetrainings.com/')
    # page.wait_for_timeout(3000)

    # aphome_page.click_udemy_courses()
    # expect(page).to_have_url('https://www.pavanonlinetrainings.com/#udemy')
    # page.wait_for_timeout(3000)

    # random_data_util = RandomDataUtil()
    # username = random_data_util.get_first_name()
    # aphome_page.set_username(username)
    # page.wait_for_timeout(5000)


