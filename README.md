# GCG - GCG Charts GPIOs
![GCG Logo](/images/GCG_Logo.png)
GCG Charts GPIOs - Uses ncurses and python to render GPIO logic to the console  

## Dependencies

| Dependency | Version | Description                       |
|------------|---------|-----------------------------------|
| ncurses    | 6.2     | Library for text-based user interfaces |
| Python     | 3.9     | Programming language              |
| RPi.GPIO   | 0.7.0   | Python library for GPIO interface on Raspberry Pi |

## Hot Keys 

| Key | Description                       |
|------------|-----------------------------------|
| p    | Pauses the logging output on the screen  |
| l     | write GPIO output to SQLite file             |

# Configuration Options

## General Settings

- **polling_speed**: Sets the interval (in seconds) for polling the GPIO pins.
- **history_length**: Specifies the length of the history to be maintained.
- **db_path**: Specifies the path to the SQLite database file.

- **Pin Monitoring Designations**:
Specify in pairs the BCM number you want to monitor and the friednly name you want to give it specrated by a colon e.g.:

18:MyPin


## Screenshots

![Screenshot](/images/GCG_Logging_01.png)
