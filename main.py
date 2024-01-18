# Import the required modules
from tkinter import *
from tkinter import messagebox, colorchooser
import requests
import csv
import tkinter.font as tkFont
import os
import json
from datetime import datetime, timedelta
import webbrowser
import sys


# Main color variable
with open("files/settings.json", "r") as file:
    settings = json.load(file)
    COLOR = settings.get("color", "#002678")

# Global variables
BACKGROUND_COLOR = COLOR
API_URL = "https://open.er-api.com/v6/latest/{from_currency}"
SETTINGS = r"files/settings.json"
CONVERSIONS = r"files/conversions.json"
CURRENCIES = r"files/currencies.csv"
LOG = r"files/history.log"

# Create the Tkinter window
root = Tk()
root.title("Currency Converter App")
root.geometry("500x800")
root.configure(bg=BACKGROUND_COLOR)  # Set background color

# Function to handle button click and perform currency conversion
def convert_currency():
    """
    Handles the currency conversion process.
    This function is triggered by the Convert button in the GUI.
    It fetches conversion rates from an API or from a local file in offline mode.
    """
    global from_currency, to_currency, amount

    # Validate and get the selected "from" and "to" currency codes
    from_currency_name = from_currency_var.get()
    to_currency_name = to_currency_var.get()
    if from_currency_name in currency_names and to_currency_name in currency_names:
        from_currency = currency_codes[currency_names.index(from_currency_name)]
        to_currency = currency_codes[currency_names.index(to_currency_name)]
    else:
        # Show an error message if the currency selection is invalid
        messagebox.showerror("Error", "Invalid currency selection")
        return

    # Validate the user entered amount
    try:
        # Convert the amount to a float
        amount = float(entered_amount_var.get())
        if amount <= 0 or amount > 1000000:
            messagebox.showerror("Error", "Enter a valid amount (0 < amount <= 1000000)")
            return
    except ValueError:
        # Show an error message if the amount is invalid
        result_var.set("ERROR")
        messagebox.showerror("Error", "Invalid amount entered")
        return

    # Load offline_mode setting from JSON
    try:
        # Load the offline_mode setting from the JSON file
        with open(SETTINGS, "r") as file:
            settings = json.load(file)
            offline_mode = settings.get("offline_mode", False)
    except Exception as e:
        #   Show an error message if the offline_mode setting could not be loaded
        messagebox.showerror("Error", f"Failed to load settings: {e}")
        return

    # Try to get the conversion rate
    try:
        if offline_mode:
            # Offline mode: Load conversion rate from local file
            try:
                with open(CONVERSIONS, "r") as file:
                    api_data = json.load(file)
                    conversion_rate = api_data['rates'].get(to_currency)
                    if conversion_rate is None:
                        raise ValueError("Invalid conversion rate in offline mode")
            # Show an error message if the offline mode failed
            except (FileNotFoundError, ValueError, KeyError) as e:
                messagebox.showerror("Error", f"Offline mode error: {e}")
                return
        else:
            # Online mode: Fetch conversion rate from API
            response = requests.get(API_URL.format(from_currency=from_currency))
            if response.status_code != 200:
                # Raise an exception if the request failed
                raise ConnectionError("Failed to fetch data from API")
            api_data = response.json()
            conversion_rate = api_data['rates'].get(to_currency)
            if conversion_rate is None:
                raise ValueError("Invalid conversion rate from API")
    except (requests.exceptions.ConnectionError, ConnectionError, ValueError) as e:
        result_var.set("ERROR")
        messagebox.showerror("Error", f"Conversion error: {e}")
        return

    # Calculate and display the converted amount
    converted_amount = amount * conversion_rate
    decimal_places = settings.get("decimal_points", 4)
    result_var.set(f"{converted_amount:.{decimal_places}f} {to_currency}")
    log_text = f"{amount} {from_currency} = {result_var.get()} at {datetime.now().strftime('%Y-%m-%d %H:%M %p')}"
    history_log(log_text)

# Function to handle swapping of currencies
def swap_currencies():
    # Get the selected "from" and "to" currencies
    from_currency, to_currency = from_currency_var.get(), to_currency_var.get()
    # Swap the currencies
    from_currency_var.set(to_currency)
    to_currency_var.set(from_currency)

# Function to handle updating the offline conversions file
def offline():
    """
    Handles the offline functionality of the application.
    This function updates the local conversions file based on the offline_mode setting.
    It is called at startup and when the settings are saved.
    """
    file_path = CONVERSIONS  # Define the file_path variable

    try:
        # Load offline_mode setting from JSON
        with open(SETTINGS, "r") as file:
            settings = json.load(file)
            offline_mode = settings.get("offline_mode", False)
            last_update = settings.get("last_update", None)

        # Check if offline mode is enabled
        if offline_mode:
            # Update conversions file if necessary
            needs_update = not os.path.exists(file_path) or \
                           last_update is None or \
                           (datetime.now() - datetime.strptime(last_update, "%Y-%m-%d")) > timedelta(days=1)

            # Update the conversions file
            if needs_update:
                try:
                    # Fetch data from API
                    response = requests.get(API_URL.format(from_currency="USD"))
                    # Check if the request was successful
                    if response.status_code == 200:
                        api_data = response.json()
                        # Save the data to the conversions file
                        with open(file_path, "w") as file:
                            json.dump(api_data, file)

                        # Update the last_update setting
                        settings["last_update"] = datetime.now().strftime("%Y-%m-%d")
                        with open(SETTINGS, "w") as settings_file:
                            json.dump(settings, settings_file)
                    else:
                        # Raise an exception if the request failed
                        raise Exception(f"API request failed with status code: {response.status_code}")
                # Show an error message if the request failed
                except requests.exceptions.ConnectionError as e:
                    messagebox.showerror("Error", f"Failed to update offline data: {e}")
        else:
            # Remove conversions file if offline mode is disabled
            if os.path.exists(file_path):
                os.remove(file_path)
                settings["last_update"] = None
                with open(SETTINGS, "w") as settings_file:
                    json.dump(settings, settings_file)
    
    
    # Show an error message if the offline mode setting could not be loaded
    except Exception as e:
        messagebox.showerror("Error", f"Offline mode error: {e}")

def history_log(convertion):
    # Load the log setting from the JSON file
    with open(SETTINGS, "r") as file:
        settings = json.load(file)
        log = settings.get("log", False)

    # Check if the log setting is enabled
    if log:
        # Create a new history log file or append to the existing one
        with open(LOG, "a") as file:
            file.write(convertion + "\n")

# Function for the settings button
def open_settings():
    with open(SETTINGS, "r") as file:
        settings = json.load(file)

    # Create global variables
    global checkbox_var

    # Function to handle button click and open color picker
    def pick_color():
        current_color = None

        # Load the current color from the settings file
        with open(SETTINGS, "r") as file:
            settings = json.load(file)
            current_color = settings.get("color", None)

        # Open the color picker
        color = colorchooser.askcolor(title="Select Color")

        # Check if the user selected a color
        if color[1] and color[1] != current_color:
            # Save the selected color to the settings file
            with open(SETTINGS, "r") as file:
                settings = json.load(file)
                settings["color"] = color[1]

            # Save the settings to the JSON file
            with open(SETTINGS, "w") as settings_file:
                json.dump(settings, settings_file)
                
            # Update a global variable or use the color directly
            global COLOR
            COLOR = color[1]

    
    # Function to clear the history log
    def clear_history():
        # Show a warning popup before clearing the history log
        if messagebox.askokcancel("Clear History Log", "Are you sure you want to clear the history log?"):
            with open(LOG, "w") as file:
                file.write("")
            # Show a message box after clearing the history log
            messagebox.showinfo("History Log", "History Log Cleared")
    

    # Create a new settings window
    settings_window = Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("300x400")
    settings_window.configure(bg=BACKGROUND_COLOR)  # Set background color
    
    # Create a label and dropdown menu for the decimal points
    decimal_points_label = Label(settings_window, text="Decimal Points:", font=(None, 15), bg=BACKGROUND_COLOR)
    decimal_points_label.pack(padx=50, anchor="w")

    # Create a dropdown menu for the decimal points
    decimal_points_var = StringVar()
    decimal_points_var.set(settings.get("decimal_points","2"))
    decimal_points = OptionMenu(settings_window, decimal_points_var, "1", "2", "3", "4", "5")
    decimal_points.pack(padx=50,pady=10, anchor="w")

    # Create a button to open the color picker
    Label(settings_window, text="Change Background color:", font=(None, 15), bg=BACKGROUND_COLOR).pack(padx=50, anchor="w")
    
    # Create a button to open the color picker
    color_button = Button(settings_window, text="Pick Color", command=pick_color, relief="solid",highlightbackground=BACKGROUND_COLOR)
    color_button.pack(padx=50,pady=10, anchor="w")

    # create a history log checkbox
    Label(settings_window, text="History Log:", font=(None, 15), bg=BACKGROUND_COLOR).pack(padx=50, anchor="w")
    history_var = BooleanVar()
    history_var.set(settings.get("log", False))
    history_checkbox = Checkbutton(settings_window, text="History Log", variable=history_var, bg=BACKGROUND_COLOR)
    history_checkbox.pack(pady=5,padx=50, anchor="w")

    # Create a button to clear the history log
    Button(settings_window, text="Clear History Log", command=clear_history, highlightbackground=BACKGROUND_COLOR, borderwidth=3, relief="solid").pack(pady=5, padx=50, anchor="w")

    # Create a checkbox for the offline mode
    Label(settings_window, text="Offline Mode:", font=(None, 15), bg=BACKGROUND_COLOR).pack(padx=50,pady=10, anchor="w")
    checkbox_var = BooleanVar()
    checkbox = Checkbutton(settings_window, text="Offline Mode", variable=checkbox_var, bg=BACKGROUND_COLOR)
    checkbox.pack(padx=50, anchor="w")

    # Load the Checkbox setting from the JSON file
    with open(SETTINGS, "r") as file:
        settings = json.load(file)
        last_update = settings.get("last_update", None)
        offline_mode = settings.get("offline_mode", False)  # Get the value of offline_mode, default to False 
        checkbox_var.set(offline_mode)  # Set the initial value of the checkbox


    def save():
        
        # Save the settings to the JSON file
        offline_mode = checkbox_var.get()  

        # Load the Dictionary to the JSON file  
        settings = {
            "offline_mode": offline_mode,
            "last_update": last_update,
            "decimal_points": decimal_points_var.get(),
            "color": COLOR,
            "log": history_var.get()
        }

        with open(SETTINGS, "w") as file:
            json.dump(settings, file)  # Save the settings to the JSON file

        offline()  # Call the offline function to update the conversions file

        # close app GUI
        root.destroy()

        # Restart the application

        python = sys.executable
        os.execl(python, python, *sys.argv)

        


        
    # Create a button to save the settings
    Button(settings_window, text="Save", command=save, highlightbackground=BACKGROUND_COLOR, borderwidth=3, relief="solid").pack(pady=20, padx=50, anchor="w")


# Read currency data from the CSV file
csv_file = open(CURRENCIES, 'r')
file = csv.DictReader(csv_file)

# Create empty lists to store currency names and codes
currency_names = []
currency_codes = []

# Loop through the CSV file and append the currency names and codes to the lists
for row in file:
    currency_codes.append(row['CurrencyCode'])
    currency_names.append(row['CurrencyName'])

# Font size for the dropdown menu
drop_font = tkFont.Font(family="Verdana", size=15)

# GUI elements
Label(root, text="Currency Conversion", font=("Courier", 35), bg=BACKGROUND_COLOR).pack(pady=20)
from_text = Label(root, text="From:", font=(None, 25), bg=BACKGROUND_COLOR)
from_text.pack(pady=20, padx=75, anchor="w")

# Create a dropdown menu for the "from" currency
from_currency_var = StringVar()
from_currency_var.set(currency_names[142])  # Default currency: USD
from_drop = OptionMenu(root, from_currency_var, *currency_names)
from_drop.pack(padx=75, anchor="w")
from_drop.config(font=drop_font, bg=BACKGROUND_COLOR, borderwidth=3, relief="solid")

# Create a dropdown menu for the "to" currency
to_text = Label(root, text="To:", font=(None, 25), bg=BACKGROUND_COLOR)
to_text.pack(pady=20, padx=75, anchor="w")

# Create a dropdown menu for the "to" currency
to_currency_var = StringVar()
to_currency_var.set(currency_names[46])  # Default currency: GBP
to_drop = OptionMenu(root, to_currency_var, *currency_names)
to_drop.pack(padx=75, anchor="w")
to_drop.config(font=drop_font, bg=BACKGROUND_COLOR, borderwidth=3, relief="solid")

# Add a Swap button
Button(root, text="Swap", command=swap_currencies, highlightbackground=BACKGROUND_COLOR, borderwidth=3, relief="solid").pack(pady=10, padx=75, anchor="w")

# Create a label and entry for the amount
entered_amount_var = StringVar()
entered_amount_var.set("1")
amount_text = Label(root, text="Amount:", font=(None, 25), bg=BACKGROUND_COLOR)
amount_text.pack(pady=20, padx=75, anchor="w")

# Create an entry for the amount
amount_entry = Entry(root, textvariable=entered_amount_var)
amount_entry.pack(padx=75, anchor="w")

# Add a Convert button
Button(root, text="Convert", command=convert_currency, highlightbackground=BACKGROUND_COLOR, borderwidth=3, relief="solid").pack(pady=30, padx=75, anchor="w")

# Create a label for the result
result_var = StringVar()
result_var.set("Results")
result_label = Label(root, textvariable=result_var, borderwidth=7, font=("Currency", 30),
                     relief="solid", width=14, height=3, bg="#FFD733").pack(pady=20, padx=75, anchor="w")

# Add a Settings button
Button(root, text="Settings", command=open_settings, highlightbackground=BACKGROUND_COLOR, borderwidth=3, relief="solid").pack(side=BOTTOM, pady=20, padx=20, anchor="se")

# Credits to the API provider
def open_api_link():
    webbrowser.open("https://www.exchangerate-api.com")

api_link_label = Label(root, text="Rates By Exchange Rate API", fg="white", cursor="hand2",bg=BACKGROUND_COLOR)
api_link_label.pack(pady=5, padx=150, anchor="w")
api_link_label.bind("<Button-1>", lambda e: open_api_link())

# Call the offline function to update the conversions file
offline()

# Run the mainloop of the Tkinter window
root.mainloop()