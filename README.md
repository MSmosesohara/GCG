# GCG - GPIO Charts

Terminal UI for monitoring Raspberry Pi GPIO and optional MCP23017 I/O states in real time.

## What It Does

- Polls configured BCM GPIO input pins and draws scrolling traces.
- Optionally polls MCP23017 GPIOA/GPIOB and draws traces for all 16 MCP bits.
- Supports per-pin friendly labels from config.
- Optional vectorscope view derived from four direction pins.
- Optional SQLite logging of sampled GPIO values.
- Runtime controls for polling speed, history length, pause, logging, and vectorscope.
- Config file defaults to `.gcg` extension.

## Dependencies

- Python 3.9+
- `RPi.GPIO`
- `curses` (standard on Linux)
- `smbus2` (only required when `mcp_enable:1`)

## Running

### Default config

```bash
python GPIO_Graph.py
```

This loads `config.gcg` by default.

### Explicit config file

```bash
python GPIO_Graph.py mountshabang.config.gcg
```

### Extensionless config name

```bash
python GPIO_Graph.py mountshabang.config
```

If no extension is provided, `.gcg` is automatically appended.

## Keyboard Shortcuts

- `p`: Pause/resume polling and rendering.
- `l`: Toggle SQLite logging on/off.
- `v`: Toggle vectorscope panel.
- `-`: Decrease polling speed by `0.01s` (minimum `0.01s`).
- `+` or `=`: Increase polling speed by `0.01s`.
- `[`: Decrease history length by `1`.
- `]`: Increase history length by `1`.
- `s`: Open file requester to choose database file path.
- `Ctrl+C`: Exit.

## UI Panels

### Header

Shows:

- Pause state
- Logging state
- Polling interval
- History length
- Hotkey legend

### Main Graph

- One trace per configured BCM pin.
- If MCP is enabled, 8 traces for GPIOA and 8 traces for GPIOB are shown below BCM traces.
- `-` (red) indicates logical 1, `_` (blue) indicates logical 0.

### Vectorscope

- Optional panel toggled by `v`.
- Uses `north/south/east/west` mapped pins from config.
- Draws movement history plus current position.

## Configuration File Format (`.gcg`)

Config lines are `key:value`.

### 1. BCM pin labels

Use numeric keys for BCM pins:

```text
4:GameInUse
17:ScrewMotorPin
```

### 2. MCP labels

Use MCP port/index keys:

```text
mcp_a0:Level1Ball
mcp_a1:Level2Ball
mcp_b0:Level4Ball
mcp_b1:Level5Ball
```

### 3. General settings

```text
polling_speed:0.1
history_length:40
db_path:/var/lib/arcade
scale:10
```

- `polling_speed`: Poll/render interval in seconds.
- `history_length`: Number of samples displayed per trace.
- `db_path`: Directory used to create `<hostname>_gpio_log.db` by default.
- `scale`: Vectorscope movement scaling.

### 4. Vectorscope direction pin mapping

```text
north:12
south:16
east:25
west:23
```

### 5. MCP transport settings

```text
mcp_enable:1
mcp_address:0x20
mcp_bus:1
```


- `mcp_enable`: `1` enables MCP polling, `0` disables.
- `mcp_address`: Supports hex (`0x20`) or decimal.
- `mcp_bus`: I2C bus index.

## SQLite Logging

When logging is enabled (`l`):

- Table: `gpio_log`
- Columns:
  - `id` (autoincrement)
  - `pin_name`
  - `value`
  - `timestamp`

One row is written per configured BCM pin on each polling cycle.

## Example Minimal Config

```text
4:GameInUse
17:ScrewMotorPin
polling_speed:0.1
history_length:40
db_path:/var/lib/arcade
scale:10
north:12
south:16
east:25
west:23
mcp_enable:0
mcp_address:0x20
mcp_bus:1
```
