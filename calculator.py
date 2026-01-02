
import tkinter as tk

print("Enter one numbers")
x = int(input())
print("Enter another number")
y = int(input())

operator = input("Enter an operator (+, -, *, /): ")
if operator == '+':
    print(x + y)
else:
    if operator == '-':
        print(x - y)
    else:
        if operator == '*':
            print(x * y)
        else:
            if operator == '/':
                    if y != 0:
                        print(x / y)
                    else:
                        print("Error: Division by zero")
            else:
                print("Error: Invalid operator")