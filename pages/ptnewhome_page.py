from playwright.sync_api import Page

class PtnewhomePage:
    def __init__(self, page:Page):
        self.page = page
        self.pt_heading_title = page.locator('h1.title')
        self.link_online_training = page.locator("a:has-text('Online Training')")

    def get_pt_heading_title(self):
        return self.pt_heading_title

    def click_online_traning(self):
        self.link_online_training.click() 
         