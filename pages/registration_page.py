from playwright.sync_api import Locator, Page


class RegistrationPage:
    def __init__(self, page: Page):
        self.page = page

        self.first_name_field = page.locator("#input-firstname")
        self.last_name_field = page.locator("#input-lastname")
        self.email_field = page.locator("#input-email")
        self.telephone_field = page.locator("#input-telephone")
        self.password_field = page.locator("#input-password")
        self.confirm_password_field = page.locator("#input-confirm")
        self.privacy_policy_checkbox = page.locator("input[name='agree']")
        self.continue_button = page.get_by_role(
            "button", name="Continue", exact=True
        )
        self.confirmation_message = page.locator("#content h1")

    def complete_registration(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        telephone: str,
        password: str,
    ) -> Locator:
        self.first_name_field.fill(first_name)
        self.last_name_field.fill(last_name)
        self.email_field.fill(email)
        self.telephone_field.fill(telephone)
        self.password_field.fill(password)
        self.confirm_password_field.fill(password)
        self.privacy_policy_checkbox.check()
        self.continue_button.click()
        return self.confirmation_message

    def get_confirmation_message(self) -> Locator:
        return self.confirmation_message