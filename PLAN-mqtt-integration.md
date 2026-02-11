# MQTT Printer Mode Integration Plan

## Goal

Add `mqtt` as a third printer mode alongside `usb` and `mock`. When in MQTT mode, the Flask app publishes ESC/POS binary data to the MQTT broker, which the GL300 print agents forward to the physical printers. The user selects which printer to send to from the UI.

## Current Architecture

```
[Browser] --> [Flask API] --> [python-escpos Usb()] --> [USB printer on same machine]
```

## Target Architecture

```
[Browser] --> [Flask API] --> [python-escpos Dummy()] --> [MQTT publish]
                                  capture ESC/POS bytes     |
                                                            v
                                                   [Mosquitto Broker]
                                                     /           \
                                           [GL300 jesse]    [GL300 kitchen]
                                               |                  |
                                        [TM-H6000IV]       [TM-H6000IV]
```

## Key Insight

python-escpos `Dummy()` captures all ESC/POS output in memory as raw bytes. In MQTT mode, we render to a Dummy printer, extract the bytes, and publish them. The GL300 agent writes those bytes directly to `/dev/usb/lp0`. The printer receives identical commands as if it were USB-connected locally.

---

## Implementation Steps

### 1. Add `paho-mqtt` dependency

**Files:** `requirements.txt`, `pyproject.toml`

- Add `paho-mqtt` to both files
- Run `uv lock` to update lockfile

### 2. Create MQTT printer backend (`mqtt_printer.py`)

**New file:** `mqtt_printer.py`

Thin wrapper that:
- Connects to the MQTT broker on init (configurable host/port/user/pass)
- Exposes a `publish(printer_name, data: bytes)` method
- Publishes to topic `printer/{printer_name}/jobs`
- Handles reconnection gracefully
- Connection params from env vars:
  - `MQTT_BROKER_HOST` (default: `192.168.50.211`)
  - `MQTT_BROKER_PORT` (default: `1883`)
  - `MQTT_BROKER_USER` (default: `printer`)
  - `MQTT_BROKER_PASS` (default: `printer`)

```python
# Sketch
import paho.mqtt.client as mqtt

class MqttPrinter:
    def __init__(self, host, port, user, password):
        self.client = mqtt.Client()
        self.client.username_pw_set(user, password)
        self.client.connect(host, port)
        self.client.loop_start()

    def publish(self, printer_name, data: bytes):
        topic = f"printer/{printer_name}/jobs"
        self.client.publish(topic, data, qos=1)

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()
```

### 3. Modify `printer_service.py` — add MQTT mode

**File:** `printer_service.py`

Changes:
- Import `MqttPrinter` and `Dummy`
- In `__init__`, when `mode == "mqtt"`, store the MqttPrinter client but use `Dummy()` as `self.printer` for ESC/POS rendering
- Add `self.target_printer` attribute — the name of the printer to publish to (e.g., `"jesse-printer"`)
- Add `set_target(printer_name)` method to change target at runtime
- Modify all print methods (`print_recipe`, `print_todo`, `print_text`) to:
  1. Render ESC/POS to `Dummy()` as usual
  2. Extract bytes via `self.printer.output`
  3. Publish bytes via `self.mqtt.publish(self.target_printer, bytes)`
  4. Reset Dummy for next job: `self.printer = Dummy()`

**Minimal change approach** — the existing Dummy rendering stays identical. We just add a "flush to MQTT" step after each print call.

```python
# In _connect():
if self.mode == "mqtt":
    self.printer = Dummy()
    self.mqtt = MqttPrinter(host, port, user, password)

# New method:
def _flush_to_mqtt(self):
    """Send captured ESC/POS output to MQTT and reset Dummy"""
    if self.mode == "mqtt" and self.target_printer:
        data = self.printer.output
        self.mqtt.publish(self.target_printer, data)
        self.printer = Dummy()  # reset for next job
```

Then at the end of `print_recipe()`, `print_todo()`, `print_text()`:
```python
self._flush_to_mqtt()
```

### 4. Add printer selection API endpoint

**File:** `app.py`

New endpoints:
- `GET /api/printers` — returns list of configured printers
  ```json
  {
    "printers": [
      {"id": "jesse-printer", "name": "Jesse"},
      {"id": "kitchen-huxley", "name": "Kitchen"}
    ],
    "mode": "mqtt"
  }
  ```
- Modify `POST /api/print/recipe` and `POST /api/print/todo` to accept `"printer"` field in request body
  ```json
  { "mode": "url", "url": "...", "printer": "jesse-printer" }
  ```
- Before printing, call `print_service.set_target(data["printer"])`
- Printer list configured via env var: `MQTT_PRINTERS=jesse-printer:Jesse,kitchen-huxley:Kitchen`

### 5. Add printer selector to frontend

**Files:** `templates/index.html`, `static/app.js`, `static/style.css`

Changes to `index.html`:
- Add a printer selector below the header, above the tabs:
  ```html
  <div class="printer-selector" id="printer-selector">
      <!-- Populated by JS on load -->
  </div>
  ```

Changes to `app.js`:
- On page load, fetch `GET /api/printers`
- If mode is `mqtt`, render printer toggle buttons (pill-style, like the tab bar)
- Store selected printer in a variable
- Include `printer` field in all form submissions
- If mode is `usb` or `mock`, hide the selector entirely (backwards compatible)

Changes to `style.css`:
- Style the printer selector as pill toggle buttons matching the existing dark theme

### 6. Update GL300 print agents to handle binary data

**Files:** Print agent on routers (`/root/print-agent.sh`)

Current agent uses `mosquitto_sub | while read` which is line-based and will mangle binary ESC/POS data.

Replace with a binary-safe approach:
```sh
#!/bin/sh
# Use mosquitto_sub with -N (no newline appending) and write directly
mosquitto_sub \
    -h "$BROKER_HOST" \
    -p "$BROKER_PORT" \
    -u "$BROKER_USER" \
    -P "$BROKER_PASS" \
    -t "$TOPIC" \
    -N \
    > /dev/usb/lp0
```

The `-N` flag prevents mosquitto_sub from appending newlines. Each message's raw bytes go straight to the printer device. Since MQTT preserves message boundaries and the printer processes ESC/POS commands sequentially, this works.

**Alternative (more robust):** Write a small Python or C helper if shell piping proves unreliable with binary data. But try the simple approach first.

### 7. Update `printers/install.sh`

**File:** `printers/install.sh`

- Move into the repo at the correct path
- Update the print agent script template to use the binary-safe version from step 6
- Add the MQTT broker config files to the repo

### 8. Update Docker and deployment config

**Files:** `docker-compose.yml`, `Dockerfile`, `checkoff-printer.service`, `.github/workflows/deploy.yml`

`docker-compose.yml` — add MQTT env vars:
```yaml
environment:
  - PRINTER_MODE=mqtt
  - MQTT_BROKER_HOST=192.168.50.211
  - MQTT_BROKER_PORT=1883
  - MQTT_BROKER_USER=printer
  - MQTT_BROKER_PASS=printer
  - MQTT_PRINTERS=jesse-printer:Jesse,kitchen-huxley:Kitchen
```

`Dockerfile` — no changes needed (paho-mqtt is pure Python)

`checkoff-printer.service` — add MQTT env vars to the systemd unit

No changes to deploy workflow.

---

## File Change Summary

| File | Action | Description |
|---|---|---|
| `requirements.txt` | Edit | Add `paho-mqtt` |
| `pyproject.toml` | Edit | Add `paho-mqtt` to dependencies |
| `mqtt_printer.py` | **New** | MQTT publish wrapper |
| `printer_service.py` | Edit | Add mqtt mode, target printer, flush-to-mqtt |
| `app.py` | Edit | Add `/api/printers`, accept `printer` field |
| `templates/index.html` | Edit | Add printer selector div |
| `static/app.js` | Edit | Fetch printers, render selector, include in requests |
| `static/style.css` | Edit | Style printer selector |
| `printers/install.sh` | Edit | Binary-safe print agent, move to repo |
| `docker-compose.yml` | Edit | Add MQTT env vars |
| `checkoff-printer.service` | Edit | Add MQTT env vars |

## Environment Variables (new)

| Variable | Default | Description |
|---|---|---|
| `MQTT_BROKER_HOST` | `192.168.50.211` | MQTT broker hostname/IP |
| `MQTT_BROKER_PORT` | `1883` | MQTT broker port |
| `MQTT_BROKER_USER` | `printer` | MQTT username |
| `MQTT_BROKER_PASS` | `printer` | MQTT password |
| `MQTT_PRINTERS` | `jesse-printer:Jesse,kitchen-huxley:Kitchen` | Comma-separated `id:label` pairs |

## Backwards Compatibility

- `PRINTER_MODE=usb` and `PRINTER_MODE=mock` continue to work exactly as before
- No MQTT dependency is loaded unless mode is `mqtt`
- Frontend hides printer selector when not in MQTT mode
- All existing API contracts preserved; `printer` field is optional (defaults to first configured printer)

## Testing Plan

1. Run with `PRINTER_MODE=mock` — verify nothing broke
2. Run with `PRINTER_MODE=mqtt` — verify printer selector appears
3. Preview still works in all modes (preview never hits hardware)
4. Print to jesse-printer — verify ESC/POS bytes arrive at GL300 and print correctly
5. Print to kitchen-huxley — same
6. Kill MQTT broker — verify graceful error message in UI
7. Reboot GL300 — verify print agent auto-restarts and reconnects
