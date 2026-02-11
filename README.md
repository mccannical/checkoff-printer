# Checkoff Printer

A "Smart" Thermal Printer application for your home. It connects to Epson TM-H6000IV thermal printers to nicely format and print Recipes and Todo Lists.

Supports three modes: direct USB, mock (development), and MQTT (networked printers via GL-iNet GL300 routers).

## Features
-   **Web Interface**: Mobile-first UI to paste recipes or manage lists.
-   **Smart Formatting**: Automatically scrapes ingredients/steps from recipe URLs or raw text and formats them to fit the 80mm thermal tape.
-   **Print Preview**: "Dry Run" mode to see exactly what will print.
-   **Markdown Todo Lists**: Headers (`#`, `##`, `###`), checkboxes, numbered lists, bold text.
-   **MQTT Networked Printing**: Send print jobs to remote printers over MQTT via GL300 routers.
-   **Printer Selection**: Choose which printer to send to from the UI (Jesse, Kitchen, etc.).
-   **Hardware & Mock Modes**: Works with real USB hardware, MQTT, or simulates output for development.

## Architecture

```
                          ┌─────────────┐
                          │  Flask App  │
                          │  (any host) │
                          └──────┬──────┘
                                 │ publish ESC/POS bytes
                                 ▼
                          ┌─────────────┐
                          │ MQTT Broker │
                          │ (Mosquitto) │
                          └──────┬──────┘
                        ┌────────┴────────┐
                        ▼                 ▼
                 ┌─────────────┐   ┌─────────────┐
                 │ GL300 Router│   │ GL300 Router│
                 │jesse-printer│   │kitchen-huxley│
                 └──────┬──────┘   └──────┬──────┘
                        ▼                 ▼
                 ┌─────────────┐   ┌─────────────┐
                 │ TM-H6000IV  │   │ TM-H6000IV  │
                 └─────────────┘   └─────────────┘
```

## Getting Started

### Prerequisites
-   Python 3.9+
-   `uv` (Recommended for package management)
-   `libusb-1.0-0` (Required for physical USB printer access)

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-repo/checkoff-printer.git
    cd checkoff-printer
    ```

2.  **Install dependencies:**
    ```bash
    uv sync
    # OR using pip
    pip install -r requirements.txt
    ```

## Usage

### Development (Mock Mode)
Run the application without a printer connected. Output is simulated in the logs/api.

```bash
export PRINTER_MODE=mock
uv run app.py
```
Open [http://localhost:8080](http://localhost:8080) in your browser.

### Production - USB (Raspberry Pi)
1.  **Connect Printer**: Plug in the Epson TM-H6000IV via USB.
2.  **Find Device IDs**: Run `lsusb` to confirm vendor/product IDs.
    -   Default configured: `04b8:0202`.
    -   If different, set `PRINTER_VENDOR_ID` and `PRINTER_PRODUCT_ID` env vars.
3.  **Run**:
    ```bash
    export PRINTER_MODE=usb
    uv run app.py
    ```

### Production - MQTT (Networked Printers)
For printers connected to GL300 routers on the network:

1.  **Set up the MQTT broker** (Mosquitto in Docker):
    ```bash
    cd backend && docker compose up -d
    ```

2.  **Set up GL300 routers** (one per printer):
    ```bash
    cd printers
    ./install.sh 192.168.50.208 'router-password' jesse-printer
    ./install.sh 192.168.50.59 'router-password' kitchen-huxley
    ```

3.  **Run the app**:
    ```bash
    export PRINTER_MODE=mqtt
    export MQTT_BROKER_HOST=192.168.50.211
    export MQTT_BROKER_PORT=1883
    export MQTT_BROKER_USER=printer
    export MQTT_BROKER_PASS=printer
    export MQTT_PRINTERS="jesse-printer:Jesse,kitchen-huxley:Kitchen"
    uv run app.py
    ```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PRINTER_MODE` | `mock` | `mock`, `usb`, or `mqtt` |
| `PORT` | `8080` | Flask server port |
| `PRINTER_VENDOR_ID` | `0x04B8` | USB vendor ID |
| `PRINTER_PRODUCT_ID` | `0x0202` | USB product ID |
| `MQTT_BROKER_HOST` | `192.168.50.211` | MQTT broker hostname |
| `MQTT_BROKER_PORT` | `1883` | MQTT broker port |
| `MQTT_BROKER_USER` | `printer` | MQTT username |
| `MQTT_BROKER_PASS` | `printer` | MQTT password |
| `MQTT_PRINTERS` | `jesse-printer:Jesse,kitchen-huxley:Kitchen` | Comma-separated `id:Label` printer list |

## Docker Deployment
The easiest way to run on a Pi. The container includes all system dependencies.

```bash
docker-compose up --build -d
```
*Note: `docker-compose.yml` uses privileged mode/device mapping to access USB.*

## API Documentation

-   `GET /api/printers`
    -   Returns: `{ "printers": [{"id": "...", "name": "..."}], "mode": "mqtt" }`
-   `POST /api/print/recipe`
    -   Body: `{ "mode": "url"|"text", "url": "...", "title": "...", "text": "...", "printer": "jesse-printer", "preview": boolean }`
-   `POST /api/print/todo`
    -   Body: `{ "title": "...", "items": "# Header\n- item 1\n- item 2", "printer": "jesse-printer", "preview": boolean }`

## Todo Markdown Support

```
# Big Header        (bold, centered, underlined)
## Medium Header     (bold, centered)
### Small Header     (bold, left-aligned)
- [ ] Checkbox task
- [x] Checked task
1. Numbered item
- Bullet item
* Bullet item
**Bold text**
Plain text
```

## Development
-   **Linting**: `uv run ruff check .`
-   **Type Checking**: `uv run ty .`
