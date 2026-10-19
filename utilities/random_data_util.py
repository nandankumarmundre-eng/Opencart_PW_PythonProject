from faker import Faker

# generating the random data / mock data
class RandomDataUtil:
    def __init__(self):
        self.faker = Faker()

    def get_first_name(self):
        return self.faker.first_name()

    def get_last_name(self):
        return self.faker.last_name()

    def get_full_name(self):
        return self.faker.full_name()
    
    def get_email(self):
        return self.faker.email()

    def get_phone_number(self):
        return self.faker.phone_number()

    def get_user_name(self):
        return self.faker.user_name()

    def get_password(self, length: int = 10):
        return self.faker.password()
    

