# class NewClass:
#     def __init__(self):
#         self.value = 5

#     def get_value(self):
#         self.value += 1
#         return self.value + a
    
#     def new_function(self):
#         self.value -= 4
        
#         a = self.get_value() + 15 
#         print(a) 
        
        
        
#     def new_function2(self):
#         self.value += 5
#         print(self.value)
        
#     def new_function3(self):
#         a = self.get_value() + self.get_value() 

    
# obj = NewClass()
# print(obj.get_value()) 
# breakpoint()

# obj.new_function3()
# obj.new_function2()  
 
# obj.new_function()


# class Car:
#     def __init__(self, color):
#         self.color = color  # self.color is instance variable

#     def show_color(self):
#         print(f"Car ka color: {self.color}")


# my_car = Car("Red")
# my_car.show_color()  # Output: Car ka color: Red


class Hero:
    def __init__(ye_hu_main, naam, power):
        ye_hu_main.naam = naam
        ye_hu_main.power = power

    def show_details(ye_hu_main):
        print(f"Main hoon {ye_hu_main.naam}, aur meri power hai {ye_hu_main.power}!")

    def attack(ye_hu_main):
        print(f"{ye_hu_main.naam} attack karta hai with {ye_hu_main.power}!")

# Object banao
ironman = Hero("Iron Man", "Tech Suit")
ironman.show_details()
ironman.attack()
