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
    scale = 2  # Default scale value
    directions = {'north': None, 'south': None, 'east': None, 'west': None}  # Default direction pins
    mcp_enable = False
    mcp_address = 0x20
    mcp_bus = 1

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
                elif key == 'scale':
                    scale = int(value)
                elif key in directions:
                    directions[key] = int(value)  # Map direction to pin
                elif key == 'mcp_enable':
                    mcp_enable = value.strip() == '1'
                elif key == 'mcp_address':
                    mcp_address = int(value, 0)  # auto-detect hex/dec
                elif key == 'mcp_bus':
                    mcp_bus = int(value)
                else:
                    pin = int(key)
                    labels[pin] = value
                    pins.append(pin)

    return labels, pins, polling_speed, history_length, db_path, scale, directions, mcp_enable, mcp_address, mcp_bus

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
labels, pins, polling_speed, history_length, db_path, scale, directions, mcp_enable, mcp_address, mcp_bus = read_config('config.txt')
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
curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Light grey border
curses.noecho()
curses.cbreak()
stdscr.keypad(True)
stdscr.nodelay(True)  # Make getch() non-blocking
curses.curs_set(0)  # Hide the cursor

# Initialize database
db_conn = init_db(db_name)
logging_enabled = False


def file_requester(stdscr, initial_path="."):
    import os
    curses.curs_set(1)
    path = os.path.abspath(initial_path)
    files = []
    selected = 0
    input_mode = False
    filename = ""

    while True:
        try:
            files = [".."] + sorted(os.listdir(path))
        except Exception:
            files = [".."]
        stdscr.clear()
        stdscr.addstr(0, 0, "Select file location (Enter: select, Tab: type filename, Esc: cancel)")
        stdscr.addstr(1, 0, f"Current path: {path}")
        max_y, max_x = stdscr.getmaxyx()
        for idx, fname in enumerate(files):
            if 2 + idx >= max_y - 2:
                break  # Prevent overflow
            if idx == selected:
                stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(2 + idx, 2, fname[:max_x-4])
            if idx == selected:
                stdscr.attroff(curses.A_REVERSE)
        if input_mode:
            stdscr.addstr(max_y-2, 0, "Filename: " + filename)
            stdscr.move(max_y-2, 10 + len(filename))
        stdscr.refresh()

        key = stdscr.getch()
        if input_mode:
            if key in (curses.KEY_ENTER, 10, 13):
                curses.curs_set(0)
                return os.path.join(path, filename)
            elif key == 27:  # ESC
                curses.curs_set(0)
                return None
            elif key in (curses.KEY_BACKSPACE, 127, 8):
                filename = filename[:-1]
            elif key == 9:  # Tab to exit input mode
                input_mode = False
            elif 32 <= key <= 126:
                filename += chr(key)
        else:
            if key == curses.KEY_UP and selected > 0:
                selected -= 1
            elif key == curses.KEY_DOWN and selected < len(files) - 1:
                selected += 1
            elif key in (curses.KEY_ENTER, 10, 13):
                chosen = files[selected]
                full_path = os.path.join(path, chosen)
                if os.path.isdir(full_path):
                    path = os.path.abspath(full_path)
                    selected = 0
                else:
                    curses.curs_set(0)
                    return full_path
            elif key == 9:  # Tab to enter filename input mode
                input_mode = True
                filename = ""
            elif key == 27:  # ESC
                curses.curs_set(0)
                return None

# Function to update the main display
def update_main_display(win, pin_states, paused, logging_enabled):
    win.erase()

    max_label_length = max(len(label) for label in labels.values())
    graph_start_col = max_label_length + 15  # Use this for all graphs

    row = 0

    # Standard GPIOs
    for idx, (pin, states) in enumerate(pin_states.items()):
        label = labels.get(pin, f"BCM {pin}")
        win.addstr(idx + row, 0, f"{label.ljust(max_label_length)} BCM {pin}: ".ljust(graph_start_col))
        for state in states:
            win.addstr("-", curses.color_pair(1)) if state else win.addstr("_", curses.color_pair(2))
        win.addstr("\n")
    row += len(pin_states)

    # MCP23017 GPIOA
    if mcp_enable:
        for i in range(8):
            win.addstr(row + i, 0, f"MCP23017_A{i}: ".ljust(graph_start_col))
            for state in reversed(mcp_trace_a[i]):
                win.addstr("-", curses.color_pair(1)) if state else win.addstr("_", curses.color_pair(2))
            win.addstr("\n")
        row += 8
        for i in range(8):
            win.addstr(row + i, 0, f"MCP23017_B{i}: ".ljust(graph_start_col))
            for state in mcp_trace_b[i]:
                win.addstr("-", curses.color_pair(1)) if state else win.addstr("_", curses.color_pair(2))
            win.addstr("\n")
    win.refresh()

# Function to update the vectorscope display
def update_vector_display(win, pin_states, scale, directions):
    win.erase()  # Use erase instead of clear to reduce flicker
    win.box()
    win.addstr(0, 2, "Vectorscope")

    # Get directional controls from pin states
    north = pin_states.get(directions['north'], [0])[-1]
    south = pin_states.get(directions['south'], [0])[-1]
    east = pin_states.get(directions['east'], [0])[-1]
    west = pin_states.get(directions['west'], [0])[-1]

    # Calculate the center and movement scaling factor
    center_y, center_x = win.getmaxyx()[0] // 2, win.getmaxyx()[1] // 2
    y = center_y - scale * (north - south)
    x = center_x + scale * (east - west)

    # Initialize history if not already present
    if not hasattr(update_vector_display, "history"):
        update_vector_display.history = []  # Initialize history if not present

    # Add the current position to the history
    update_vector_display.history.append((y, x))

    # Draw lines between the blocks
    for i in range(1, len(update_vector_display.history)):
        prev_y, prev_x = update_vector_display.history[i - 1]
        curr_y, curr_x = update_vector_display.history[i]

        # Draw vertical line if x-coordinates are the same
        if prev_x == curr_x:
            start_y = min(prev_y, curr_y)
            end_y = max(prev_y, curr_y)
            for line_y in range(start_y + 1, end_y):
                win.addch(line_y, curr_x, "|", curses.color_pair(2))  # Vertical line

        # Draw horizontal line if y-coordinates are the same
        elif prev_y == curr_y:
            start_x = min(prev_x, curr_x)
            end_x = max(prev_x, curr_x)
            for line_x in range(start_x + 1, end_x):
                win.addch(curr_y, line_x, "-", curses.color_pair(2))  # Horizontal line

        # Draw diagonal line if both x and y change
        else:
            step_y = 1 if curr_y > prev_y else -1
            step_x = 1 if curr_x > prev_x else -1
            line_y, line_x = prev_y + step_y, prev_x + step_x
            while line_y != curr_y and line_x != curr_x:
                win.addch(line_y, line_x, "*", curses.color_pair(2))  # Diagonal line
                line_y += step_y
                line_x += step_x

    # Draw the history as blocks
    for prev_y, prev_x in update_vector_display.history:
        win.addstr(prev_y, prev_x, "█", curses.color_pair(2))  # Use "█" for a block

    # Limit the history length to avoid excessive memory usage
    if len(update_vector_display.history) > 100:  # Adjust the limit as needed
        update_vector_display.history.pop(0)

    # Draw the current position
    win.addstr(y, x, "O", curses.color_pair(1))  # Use "O" for the current position

    win.refresh()

# Function to update the header display
def update_header(win, paused, logging_enabled, polling_speed, history_length, key_flash):
    win.erase()
    win.attron(curses.color_pair(5))
    win.box()
    win.attroff(curses.color_pair(5))

    now = time.time()
    # Helper to flash a key label
    def flash_label(label, key):
        if now - key_flash.get(key, 0) < FLASH_DURATION:
            win.attron(curses.color_pair(4) | curses.A_BOLD)
            win.addstr(label)
            win.attroff(curses.color_pair(4) | curses.A_BOLD)
        else:
            win.addstr(label, curses.A_BOLD)

    # Help text (no flashing here)
    win.addstr(1, 1, "Keys: <v> Vectorscope <Ctrl+C> Quit")

    # Status line with flashing for relevant keys
    y, x = 2, 1
    win.addstr(y, x, "PAUSED")
    win.addstr("<p>: ")
    win.addstr("YES" if paused else "NO", curses.A_BOLD)
    win.addstr("   LOGGING")
    win.addstr("<l>: ")
    win.addstr("YES" if logging_enabled else "NO", curses.A_BOLD)
    win.addstr("   POLLING")
    flash_label("<", "-")
    flash_label("-", "-")
    win.addstr("/")
    flash_label("+", "+")
    flash_label(">", "+")
    win.addstr(": ")
    win.addstr(f"{polling_speed:.2f}s", curses.A_BOLD)
    win.addstr("   HISTORY")
    flash_label("<", "[")
    flash_label("[", "[")
    win.addstr("/")
    flash_label("]", "]")
    flash_label(">", "]")
    win.addstr(": ")
    win.addstr(str(history_length), curses.A_BOLD)

    win.refresh()

# Read configuration
labels, pins, polling_speed, history_length, db_path, scale, directions, mcp_enable, mcp_address, mcp_bus = read_config('config.txt')

key_flash = {
    '-': 0,
    '+': 0,
    '[': 0,
    ']': 0,
}
FLASH_DURATION = 0.2  # seconds



# Main loop
try:
    pin_states = {pin: [0] * history_length for pin in pins}
    paused = False
    vector_graph_visible = False

    header_height = 4
    height, width = stdscr.getmaxyx()
    header_win = curses.newwin(header_height, width, 0, 0)
    main_win = curses.newwin(height - header_height, width, header_height, 0)
    vector_win = None

    if mcp_enable:
        import smbus2
        bus = smbus2.SMBus(mcp_bus)
        mcp_trace_a = [[] for _ in range(8)]
        mcp_trace_b = [[] for _ in range(8)]

        def read_mcp_gpio():
            try:
                gpio_a = bus.read_byte_data(mcp_address, 0x12)
                gpio_b = bus.read_byte_data(mcp_address, 0x13)
                return gpio_a, gpio_b
            except Exception:
                return 0, 0

        def update_mcp_trace(trace, gpio, trace_length):
            for i in range(8):
                trace[i].append(1 if (gpio & (1 << i)) else 0)
                if len(trace[i]) > trace_length:
                    trace[i].pop(0)

    while True:
        # Check if window size or vector_graph_visible changed, and recreate windows if needed
        new_height, new_width = stdscr.getmaxyx()
        if (new_height, new_width) != (height, width) or \
           (vector_graph_visible and main_win.getmaxyx()[1] != new_width // 2) or \
           (not vector_graph_visible and main_win.getmaxyx()[1] != new_width):
            height, width = new_height, new_width
            header_win = curses.newwin(header_height, width, 0, 0)
            if vector_graph_visible:
                main_win = curses.newwin(height - header_height, width // 2, header_height, 0)
                vector_win = curses.newwin(height - header_height, width // 2, header_height, width // 2)
            else:
                main_win = curses.newwin(height - header_height, width, header_height, 0)
                vector_win = None

        key = stdscr.getch()
        if key != -1:
            stdscr.addstr(0, 30, f"Key pressed: {key}")
            stdscr.refresh()

        if key == ord('p'):
            paused = not paused
        elif key == ord('l'):
            logging_enabled = not logging_enabled
        elif key == ord('v'):
            vector_graph_visible = not vector_graph_visible
            stdscr.addstr(1, 30, f"Vector graph visible: {vector_graph_visible}")
            stdscr.refresh()
            # Force window recreation on toggle
            height, width = 0, 0
        elif key == ord('-'):
            polling_speed = max(0.01, polling_speed - 0.01)
            key_flash['-'] = time.time()
        elif key == ord('+') or key == ord('='):
            polling_speed += 0.01
            key_flash['+'] = time.time()
        elif key == ord('['):
            if history_length > 1:
                history_length -= 1
                for pin in pin_states:
                    pin_states[pin] = pin_states[pin][-history_length:]
                # Add this for MCP traces:
                if mcp_enable:
                    for i in range(8):
                        mcp_trace_a[i] = mcp_trace_a[i][-history_length:]
                        mcp_trace_b[i] = mcp_trace_b[i][-history_length:]
            key_flash['['] = time.time()
        elif key == ord(']'):
            history_length += 1
            for pin in pin_states:
                pin_states[pin] = [0] * (history_length - len(pin_states[pin])) + pin_states[pin]
            # Add this for MCP traces:
            if mcp_enable:
                for i in range(8):
                    mcp_trace_a[i] = [0] * (history_length - len(mcp_trace_a[i])) + mcp_trace_a[i]
                    mcp_trace_b[i] = [0] * (history_length - len(mcp_trace_b[i])) + mcp_trace_b[i]
            key_flash[']'] = time.time()
        elif key == ord('s'):
            curses.curs_set(1)
            new_db_path = file_requester(stdscr, db_path)
            curses.curs_set(0)
            if new_db_path:
                db_path = os.path.dirname(new_db_path)
                db_name = new_db_path
                db_conn.close()
                db_conn = init_db(db_name)

        if not paused:
            for pin in pins:
                state = GPIO.input(pin)
                pin_states[pin].append(state)
                if len(pin_states[pin]) > history_length:
                    pin_states[pin].pop(0)
            if logging_enabled:
                log_gpio_values(db_conn, pin_states, labels)

        # Update the header panel
        update_header(header_win, paused, logging_enabled, polling_speed, history_length, key_flash)

        # Update the main display
        update_main_display(main_win, pin_states, paused, logging_enabled)

        # Conditionally update or clear the vector graph display
        if vector_graph_visible and vector_win:
            update_vector_display(vector_win, pin_states, scale, directions)
        elif vector_win:
            vector_win.erase()
            vector_win.refresh()

        if mcp_enable and not paused:
            gpio_a, gpio_b = read_mcp_gpio()
            update_mcp_trace(mcp_trace_a, gpio_a, history_length)
            update_mcp_trace(mcp_trace_b, gpio_b, history_length)

        time.sleep(polling_speed)
finally:
    curses.nocbreak()
    stdscr.keypad(False)
    curses.echo()
    curses.endwin()
    curses.curs_set(1)  # Restore the cursor
    GPIO.cleanup()
    db_conn.close()
    if mcp_enable:
        bus.close()

