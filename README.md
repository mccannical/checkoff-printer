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
                   :8080  │   nginx     │
                   ------>│  (frontend) │
                          └──────┬──────┘
                                 │ proxy /api/
                                 ▼
                          ┌─────────────┐
                          │  Flask API  │
                          │  (backend)  │
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

## Repository Structure

```
frontend/       Static SPA served by nginx
backend/        Flask API server
installers/     GL300 router + Pi host provisioning scripts
tools/          Standalone utility scripts
data/           Recipe data and test URLs
```

## Getting Started

### Prerequisites
-   Docker & Docker Compose (recommended)
-   OR: Python 3.9+ and `uv` for local development

### Quick Start (Docker)

```bash
cp .env.example .env       # Review and customize env vars
docker compose up --build -d
```
Open [http://localhost:8080](http://localhost:8080) in your browser.

### Local Development

1.  **Install backend dependencies:**
    ```bash
    cd backend && uv sync
    ```

2.  **Run the backend (mock mode):**
    ```bash
    cd backend && PRINTER_MODE=mock uv run app.py
    ```

3.  **Open the frontend:**
    Open `frontend/index.html` directly in a browser, or use the Docker setup for the full nginx proxy.

### Production - MQTT (Networked Printers)
For printers connected to GL300 routers on the network:

1.  **Deploy with Docker Compose:**
    ```bash
    PRINTER_MODE=mqtt docker compose up --build -d
    ```

2.  **Set up GL300 routers** (one per printer):
    ```bash
    cd installers/printers
    ./install.sh 192.168.50.208 'router-password' jesse-printer
    ./install.sh 192.168.50.59 'router-password' kitchen-huxley
    ```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PRINTER_MODE` | `mock` | `mock`, `usb`, or `mqtt` |
| `PORT` | `8080` | Flask server port |
| `PRINTER_VENDOR_ID` | `0x04B8` | USB vendor ID |
| `PRINTER_PRODUCT_ID` | `0x0202` | USB product ID |
| `MQTT_BROKER_HOST` | `mosquitto` | MQTT broker hostname |
| `MQTT_BROKER_PORT` | `1883` | MQTT broker port |
| `MQTT_BROKER_USER` | `printer` | MQTT username |
| `MQTT_BROKER_PASS` | `printer` | MQTT password |
| `MQTT_PRINTERS` | `jesse-printer:Jesse,kitchen-huxley:Kitchen` | Comma-separated `id:Label` printer list |

See `.env.example` for all available variables.

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
-   **Linting**: `cd backend && uv run ruff check .`
-   **Type Checking**: `cd backend && uv run ty .`
-   **Tests**: `cd backend && uv run pytest tests/`
