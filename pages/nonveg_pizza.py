from veg_pizza import VegPizza

class NonvegPizza(VegPizza):
    service_tax = 2.15   # class attribute (shared)
    gst_tax = 79

    def __init__(
        self,
        veg_pizza_name,
        veg_pizza_price,
        nonveg_pizza_name,
        nonveg_pizza_price,
        veg_tips=0,
        nonveg_tips=0,
    ):
        super().__init__(veg_pizza_name, veg_pizza_price, veg_tips)
        self.nonveg_pizza_name = nonveg_pizza_name
        self.nonveg_pizza_price = nonveg_pizza_price
        self.nonveg_tips = nonveg_tips

    def calculate_tax(self):
        return self.service_tax + self.gst_tax

    def display_bill_nonveg_pizza(self):
        print(f'Name of the nonveg pizza: {self.nonveg_pizza_name}')
        print(f'Base price of non veg pizza: {self.nonveg_pizza_price}')
        print(f'Total taxs charged for nonveg pizza: {self.calculate_tax()}')
        print(f'Given tips for nonveg pizza: {self.nonveg_tips}')
        return (
            self.nonveg_pizza_price
            + self.calculate_tax()
            + self.nonveg_tips
        )

nonveg_pizza = NonvegPizza(
    veg_pizza_name='Veg Delight',
    veg_pizza_price=600,
    nonveg_pizza_name='Chicken Delight',
    nonveg_pizza_price=800,
    veg_tips=15,
    nonveg_tips=30,
)

print(f'Total cost of veg Pizza: {nonveg_pizza.display_bill_veg_pizza()}')
print(f'Total cost of non veg pizza: {nonveg_pizza.display_bill_nonveg_pizza()}')


