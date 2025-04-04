import curses
import RPi.GPIO as GPIO
import time
import sqlite3
from datetime import datetime
import socket
import os

# Function to read labels and settings from config file
def read_config(config_file):
    labels = {}
    pins = []
    polling_speed = 0.1  # Default polling speed
    history_length = 50  # Default history length
    db_path = '.'  # Default database path
    with open(config_file, 'r') as file:
        for line in file:
            if ':' in line:
                key, value = line.strip().split(':', 1)
                if key == 'polling_speed':
                    polling_speed = float(value)
                elif key == 'history_length':
                    history_length = int(value)
                elif key == 'db_path':
                    db_path = value
                else:
                    pin = int(key)
                    labels[pin] = value
                    pins.append(pin)
    return labels, pins, polling_speed, history_length, db_path

# Function to initialize the SQLite database
def init_db(db_name):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gpio_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pin_name TEXT,
            value INTEGER,
            timestamp TEXT
        )
    ''')
    conn.commit()
    return conn

# Function to log GPIO values to the database
def log_gpio_values(conn, pin_states, labels):
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')  # Timestamp with microsecond precision
    for pin, states in pin_states.items():
        pin_name = labels.get(pin, f"BCM {pin}")
        value = states[-1]  # Get the latest value
        cursor.execute('''
            INSERT INTO gpio_log (pin_name, value, timestamp)
            VALUES (?, ?, ?)
        ''', (pin_name, value, timestamp))
    conn.commit()

# Setup GPIO
GPIO.setmode(GPIO.BCM)
labels, pins, polling_speed, history_length, db_path = read_config('config.txt')  # Read labels, pins, polling speed, history length, and db path from config file

for pin in pins:
    GPIO.setup(pin, GPIO.IN)

# Get hostname and prepend to database file name
hostname = socket.gethostname()
db_name = os.path.join(db_path, f"{hostname}_gpio_log.db")

# Initialize ncurses
stdscr = curses.initscr()
curses.start_color()
curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)  # Red background for pause indicator
curses.init_pair(4, curses.COLOR_BLACK, curses.COLOR_GREEN)  # Green background for logging indicator
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
stdscr.nodelay(True)  # Make getch() non-blocking
curses.curs_set(0)  # Hide the cursor

# Initialize database
db_conn = init_db(db_name)
logging_enabled = False

# Create windows for main display and vectorscope
height, width = stdscr.getmaxyx()
main_win = curses.newwin(height, width // 2, 0, 0)
vector_win = curses.newwin(height, width // 2, 0, width // 2)

# Function to update the main display
def update_main_display(win, pin_states, paused, logging_enabled):
    win.erase()  # Use erase instead of clear to reduce flicker
    if paused:
        win.addstr(0, 0, "PAUSED", curses.color_pair(3))
    if logging_enabled:
        win.addstr(0, 10, "LOGGING ENABLED", curses.color_pair(4))
    
    max_label_length = max(len(label) for label in labels.values())
    graph_start_col = max_label_length + 15  # Adjust this value to align the graph correctly
    
    for idx, (pin, states) in enumerate(pin_states.items()):
        label = labels.get(pin, f"BCM {pin}")
        win.addstr(idx + 2, 0, f"{label.ljust(max_label_length)} BCM {pin}: ")
        win.addstr(idx + 2, graph_start_col, "")  # Align the start of the graph
        for state in states:
            if state:
                win.addstr("-", curses.color_pair(1))
            else:
                win.addstr("_", curses.color_pair(2))
        win.addstr("\n")
    win.refresh()

# Function to update the vectorscope display
def update_vector_display(win, pin_states):
    win.erase()  # Use erase instead of clear to reduce flicker
    win.box()
    win.addstr(0, 2, "Vectorscope")
    
    # Example directional controls (replace with actual pins)
    north = pin_states.get(12, [0])[-1]
    south = pin_states.get(16, [0])[-1]
    east = pin_states.get(1, [0])[-1]
    west = pin_states.get(7, [0])[-1]
    
    center_y, center_x = win.getmaxyx()[0] // 2, win.getmaxyx()[1] // 2
    y = center_y - (north - south)
    x = center_x + (east - west)
    
    win.addstr(y, x, "O", curses.color_pair(1))
    win.refresh()

# Main loop
try:
    pin_states = {pin: [0] * history_length for pin in pins}
    paused = False
    while True:
        key = stdscr.getch()
        if key == ord('p'):
            paused = not paused
        elif key == ord('l'):
            logging_enabled = not logging_enabled
        if not paused:
            for pin in pins:
                state = GPIO.input(pin)
                pin_states[pin].append(state)
                if len(pin_states[pin]) > history_length:
                    pin_states[pin].pop(0)
            if logging_enabled:
                log_gpio_values(db_conn, pin_states, labels)
        update_main_display(main_win, pin_states, paused, logging_enabled)
        update_vector_display(vector_win, pin_states)
        time.sleep(polling_speed)
finally:
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
    curses.curs_set(1)  # Restore the cursor
    GPIO.cleanup()
    db_conn.close()