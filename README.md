# GCG - GCG Charts GPIOs
![GCG Logo](/images/GCG_Logo.png)
Ncurses on top of Python to render GPIO logic to the console.

## Dependencies

| Dependency | Version | Description                       |
|------------|---------|-----------------------------------|
| ncurses    | 6.2     | Library for text-based user interfaces |
| Python     | 3.9     | Programming language              |
| RPi.GPIO   | 0.7.0   | Python library for GPIO interface on Raspberry Pi |

## Hot Keys

| Key | Description                                      |
|-----|--------------------------------------------------|
| p   | Pause/resume the GPIO polling and display        |
| l   | Toggle logging GPIO output to SQLite file        |
| v   | Enable/disable Vectorscope panel                 |
| -/+ | Decrease/increase polling speed (flashes green)  |
| [/] | Decrease/increase history length (flashes green) |
| s   | Open ncurses file requester to set DB save path  |
| Ctrl+C | Quit the application                          |

## UI Features

- **Header Panel:**  
  - Displays hotkeys and current status (Paused, Logging, Polling Rate, History Length).
  - Has a light grey border.
  - Status line keys (-, +, [, ]) flash green when pressed.
- **Main Panel:**  
  - Shows GPIO pin states as a scrolling graph.
- **Vectorscope Panel:**  
  - Shows direction mapped to GPIO pins (enable with `v`).
- **Ncurses File Requester:**  
  - Press `s` to open a file requester to select or type a new SQLite database file location.
  - Navigate with arrow keys, Enter to select, Tab to type filename, Esc to cancel.

# Configuration Options

## General Settings

- **polling_speed**: Sets the interval (in seconds) for polling the GPIO pins.
- **history_length**: Specifies the length of the history to be maintained.
- **db_path**: Specifies the path to the SQLite database file.
- **north:12 south:16 east:25 west:23**: Used to map BCM pin number to direction for Vectorscope.
- **scale**: Used to change the size of the vectorscope movement.

- **Pin Monitoring Designations**:  
  Specify in pairs the BCM number you want to monitor and the friendly name you want to give it, separated by a colon, e.g.:
  ```
  18:MyPin
  ```

## Demo Video

[Watch the video](/images/Demo_Video.mp4)

## Screenshots

![Screenshot](/images/GCG_Logging_01.png)
![Screenshot](/images/GCG_Logging_02.png)
![Screenshot](/images/GCG_Logging_03.png)

