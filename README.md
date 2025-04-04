# GCG - GCG Charts GPIOs
![GCG Logo](/images/GCG_Logo.png)
Ncurseson top of python to render GPIO logic to the console  

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
| v     | Enable / Disable Vectorscope            |

# Configuration Options

## General Settings

- **polling_speed**: Sets the interval (in seconds) for polling the GPIO pins.
- **history_length**: Specifies the length of the history to be maintained.
- **db_path**: Specifies the path to the SQLite database file.
- **north:12 south:16 east:25 west:23**: Used to map BCM pin number to direction for Vectorscope
- **scale**: Used to change the size of the vectorscope movement 

- **Pin Monitoring Designations**:
Specify in pairs the BCM number you want to monitor and the friendly name you want to give it seperated by a colon e.g.:

18:MyPin

## Demo Video

[Watch the video](/images/Demo_Video.mp4)

## Screenshots

![Screenshot](/images/GCG_Logging_01.png)
