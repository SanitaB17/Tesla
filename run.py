import gspread
import os
from tabulate import tabulate
from google.oauth2.service_account import Credentials
from datetime import datetime

SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

CREDS = Credentials.from_service_account_file('creds.json')
SCOPED_CREDS = CREDS.with_scopes(SCOPE)
GSPREAD_CLIENT = gspread.authorize(SCOPED_CREDS)
SHEET = GSPREAD_CLIENT.open('tesla')

sales = SHEET.worksheet('bookings')

AVAILABLE = {
    'Tesla model 3': 1,
    'Tesla model Y': 2,
    'Tesla model S': 1
}

PRICE_PER_DAY = {
    'Tesla model 3': 50,
    'Tesla model Y': 70,
    'Tesla model S': 75
}

HD = ['Name', 'Car Model', 'Start Date', 'End Date', 'Days', 'Total Price']


def main_menu():
    os.system('clear')
    print("\n###############################################")
    print("Welcome to the Tesla car rental system")
    print("###############################################\n")
    print("Please select an option from the main menu\n")
    print("1. Rent Car")
    print("2. View Booking")
    print("3. Cancel Booking\n")

    while True:
        try:
            choice = int(input("Please Enter your choice:\n"))
            if choice not in range(1, 4):
                raise ValueError("Please enter a number between 1 and 3.")
            break
        except ValueError as ve:
            print("Invalid choice. Please enter a number between 1 and 3.")
            continue

    if choice == 1:
        rent_car()
    elif choice == 2:
        view_booking()
    elif choice == 3:
        cancel_booking()


def rent_car():
    os.system('clear')
    cars = list(AVAILABLE.keys())

    while True:
        try:
            st_d_str = input("Enter start date (DD-MM-YYYY):\n")
            st_d = datetime.strptime(st_d_str, '%d-%m-%Y')
            if st_d.date() < datetime.now().date():
                raise ValueError("Start date should be in the future.")
        except ValueError as ve:
            print("Please enter a valid date example 17-07-2027")
            continue

        while True:
            try:
                end_d_str = input("Enter end date (DD-MM-YYYY):\n")
                end_d = datetime.strptime(end_d_str, '%d-%m-%Y')
                if st_d >= end_d:
                    raise ValueError("End date should be after start date.")
                break
            except ValueError:
                print("Please enter a valid date example 17-07-2027")

        if not any(a_car_available(car, st_d, end_d) for car in cars):
            print("Sorry, no cars available for rent at the specified dates.")
            while True:
                choice = input("Select model or exit?(return/exit):\n").lower()
                if choice == "return":
                    break
                elif choice == "exit":
                    main_menu()
                else:
                    print("Invalid choice. Please enter 'return' or 'exit'.")
                    continue
            continue

        print("Please select a car model to rent\n")
        for i, car in enumerate(cars, start=1):
            print(f"{i}. {car}")

        while True:
            try:
                choice = int(input("Please select a car model to rent:\n"))
                if choice not in range(1, len(cars) + 1):
                    raise ValueError("Please select a valid number.")
                car = cars[choice - 1]
                if not a_car_available(car, st_d, end_d):
                    raise ValueError(f"Sorry, {car} is fully booked.")
                break
            except ValueError as ve:
                print("Invalid choice.please select a valid number.")
                continue

        break

    user_n = input("Please enter your name:\n").upper()
    while not user_n.isalpha():
        print("Name should contain only letters.")
        user_n = input("Please enter your name:\n").upper()

    days = (end_d - st_d).days
    tot_p = booking_cost(car, days)
    print(f"\nYou have selected to rent the {car} for {days} days")
    print(f"Rental period: {st_d_str} to {end_d_str}")
    print(f"User name: {user_n}")
    print(f"Total price: ${tot_p}")

    while True:
        confirm = input("Please confirm your booking (yes/no):\n").lower()
        if confirm == "yes":
            sales.append_row([user_n, car, st_d_str, end_d_str, days, tot_p])
            print("Booking confirmed!")
            print("Thank you for using our service!")
            break
        elif confirm == "no":
            print("Booking cancelled!")
            break
        else:
            print("Please enter 'yes' or 'no'")
            input("Press enter to return to main menu...\n")
    print("Returning to main menu...")
    main_menu()


def a_car_available(car, start_date, end_date):
    bookings = sales.get_all_values()
    for booking in bookings:
        if booking[1] == car:
            booking_st = datetime.strptime(booking[2], '%d-%m-%Y')
            booking_end = datetime.strptime(booking[3], '%d-%m-%Y')
            if (start_date >= booking_st and start_date <= booking_end) or \
               (end_date >= booking_st and end_date <= booking_end):
                return False
    return True


def booking_cost(car, days):
    return PRICE_PER_DAY[car] * days


def cancel_booking():
    os.system('clear')
    search_n = input("Please select your name (in CAPITAL LETTERS):\n")
    while not search_n.isalpha() or not search_n.isupper():
        print("Name should contain only uppercase letters.")
        search_n = input("Please enter your name (in CAPITAL LETTERS):\n")

    try:
        sales = SHEET.worksheet('bookings')
    except gspread.WorksheetNotFound:
        print("Worksheet 'bookings' not found.")
        return

    try:
        bookings = sales.get_all_values()
    except Exception as e:
        print(f"Error retrieving bookings: {e}")
        return

    m_bookings = [
        booking for booking in bookings
        if booking[0].upper() == search_n
    ]

    if not m_bookings:
        print(f"No booking(s) found for {search_n}")
        input("Press enter to return to main menu...\n")
        main_menu()
        return

    print("Bookings found: ")
    print(tabulate(m_bookings, headers=HD, tablefmt="grid"))

    confirm = ""
    while confirm not in ["yes", "no"]:
        confirm = input("Cancel booking(s)? (yes/no): ").lower()
        if confirm == "yes":
            try:
                for booking in m_bookings:
                    row_index = sales.find(booking[0]).row
                    sales.delete_rows(row_index)
                print("All booking(s) canceled!")
                break
            except Exception as e:
                print(f"An error occurred while canceling the bookings: {e}")
        elif confirm == "no":
            print("Booking cancellation canceled.")
            break
        else:
            print("Invalid input. Please enter 'yes' or 'no'.")

    input("Press enter to return to main menu...\n")
    main_menu()


def view_booking():
    os.system('clear')
    search_n = input("Please enter your name (in CAPITAL LETTERS):\n")
    while not search_n.isalpha() or not search_n.isupper():
        print("Name should contain only uppercase letters.")
        search_n = input("Please enter your name (in CAPITAL LETTERS):\n")

    bookings = sales.get_all_values()

    m_bookings = [
        booking for booking in bookings
        if booking[0].upper() == search_n
    ]

    if not m_bookings:
        print(f"No booking(s) found for {search_n}")
    else:
        print("Booking(s) found:")
        print(tabulate(m_bookings, headers=HD, tablefmt="grid"))

    input("Press enter to return to main menu...\n")
    main_menu()


main_menu()
