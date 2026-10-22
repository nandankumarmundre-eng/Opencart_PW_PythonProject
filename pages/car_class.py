class Car():
    service_tax = 22500 # class attribute
    sales_tax = 38500
    road_Tax = 97500
    insurance = 34500

    def __init__(self, car_name, car_price):
        self.car_name = car_name
        self.car_price = car_price
        # super().pizza_name = self.pizza_name
        # super().pizza_price = self.pizza_price
        # super().tips = self.tips

    def calculate_all_taxes(self):
        return self.sales_tax + self.road_Tax + self.service_tax

    def on_road_Total_price(self):
        return self.calculate_all_taxes() + self.insurance + self.car_price

    def display_total_cost(self):
        print(f'Name of the car: {self.car_name}')
        print(f'Service tax: {self.service_tax}')
        print(f'Sales tax: {self.sales_tax}')
        print(f'road_tax: {self.road_Tax}')
        print(f'Insurance: {self.insurance}')
        print(f'On Road Price of Car: {self.on_road_Total_price()}')
            
car = Car('Tata Punch', 935000)
print(car.display_total_cost())
