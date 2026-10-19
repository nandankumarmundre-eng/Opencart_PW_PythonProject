from playwright.sync_api import Page

class AphomePage:
    def __init__(self, page:Page):
        self.page = page
        self.heading_title = page.locator("h1:has-text('Automation Testing Practice')")
        self.link_new_tab = page.locator("button:has-text('New Tab')")
        self.link_udemy_courses = page.locator("ul.nav-links").get_by_role(
            "link", name="Udemy Courses", exact=True
        )
        self.input_username = page.locator('#name')

    def get_ap_title(self):
        return self.heading_title

    def click_new_tab(self):
        self.link_new_tab.click() 

    def click_udemy_courses(self):
        self.link_udemy_courses.click()

    def set_username(self, username):
        self.input_username.fill(username)