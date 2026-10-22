class VegPizza:
    service_tax = 0.75   # class attribute (shared)
    gst_tax = 64

    def __init__(self, pizza_name, pizza_price, tips=0):
        # instance attributes
        self.pizza_name = pizza_name         
        self.pizza_price = pizza_price
        self.tips = tips

    def calculate_tax(self):
        return self.service_tax + self.gst_tax

    def calculate_total(self):
        return self.calculate_tax() + self.tips + self.pizza_price

    def display_bill_veg_pizza(self):
        tax = VegPizza.service_tax + VegPizza.gst_tax
        print(f'Name of the veg pizza: {self.pizza_name}')
        print(f'Base price of veg pizza: {self.pizza_price}')
        print(f'Total taxs charged for veg pizza: {tax}')
        print(f'Given tips for veg pizza: {self.tips}')
        return tax + self.tips + self.pizza_price

veg_pizza = VegPizza('Veg Delight', 500, 10)
# print(f'Total cost of veg Pizza: {veg_pizza.display_bill()}')



