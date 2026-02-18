# Checkoff Printer

A "Smart" Thermal Printer application for your home. It connects to Epson TM-H6000IV thermal printers to nicely format and print Recipes and Todo Lists.

Supports three modes: direct USB, mock (development), and MQTT (networked printers via GL-iNet GL300 routers).

## Features

- **Web Interface**: Mobile-first UI to paste recipes or manage lists.
- **Smart Formatting**: Automatically scrapes ingredients/steps from recipe URLs (via JSON-LD, meta tags, and the `recipe-scrapers` library) or raw text and formats them to fit the 80mm thermal tape.
- **Print Preview**: "Dry Run" mode to see exactly what will print.
- **Markdown Todo Lists**: Headers (`#`, `##`, `###`), checkboxes, numbered lists, bold text.
- **MQTT Networked Printing**: Send print jobs to remote printers over MQTT via GL300 routers.
- **Printer Selection**: Choose which printer to send to from the UI (Jesse, Kitchen, etc.).
- **Hardware & Mock Modes**: Works with real USB hardware, MQTT, or simulates output for development.
- **Print Logging**: All prints are automatically saved as `.txt` files in the `logs/` directory with timestamps and source URLs.
- **Fraction Normalization**: Automatic conversion of Unicode fractions (½, ⅓, etc.) to ASCII (1/2, 1/3, etc.) for printer compatibility.
- **CI/CD**: Automated commitlinting, releases via release-please, and deploy-on-push to Raspberry Pi via self-hosted GitHub Actions runner.

## Architecture

```
                          ┌─────────────┐
                     :80  │   nginx     │
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
frontend/                Static SPA served by nginx (index.html, app.js, style.css)
backend/                 Flask API server
  ├── app.py             Flask entry point & API routes
  ├── printer_service.py Core print logic (ESC/POS rendering, text wrapping)
  ├── mqtt_printer.py    MQTT publisher for networked printers
  └── formatters/        Input parsers (recipe.py, todo.py)
installers/
  ├── printers/          GL300 router provisioning (install.sh)
  └── host/              Raspberry Pi host setup (systemd service, permissions)
tools/                   Standalone utility scripts (recipe extraction, URL fetching, debug)
data/                    Recipe data and test URLs (recipes.json, test-recipes.txt)
logs/                    Auto-generated print logs (gitignored)
.github/workflows/       CI/CD (commitlint, release-please, deploy to Pi)
```

## Getting Started

### Prerequisites

- Docker & Docker Compose (recommended)
- OR: Python 3.9+ and `uv` for local development

### Quick Start (Docker)

```bash
cp .env.example .env       # Review and customize env vars
docker compose up --build -d
```

Open [http://printer.mccannical.com](http://printer.mccannical.com) in your browser.

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

### Production — MQTT (Networked Printers)

MQTT mode is the default. For printers connected to GL300 routers on the network:

1.  **Deploy with Docker Compose:**

    ```bash
    docker compose up --build -d
    ```

2.  **Set up GL300 routers** (one per printer):
    ```bash
    cd installers/printers
    ./install.sh 192.168.50.208 'router-password' jesse-printer
    ./install.sh 192.168.50.59 'router-password' kitchen-huxley
    ```

## Environment Variables

| Variable             | Default                                      | Description                             |
| -------------------- | -------------------------------------------- | --------------------------------------- |
| `PRINTER_MODE`       | `mqtt`                                       | `mock`, `usb`, or `mqtt`                |
| `PORT`               | `8080`                                       | Flask server port                       |
| `PRINTER_VENDOR_ID`  | `0x04B8`                                     | USB vendor ID (usb mode only)           |
| `PRINTER_PRODUCT_ID` | `0x0202`                                     | USB product ID (usb mode only)          |
| `PRINTER_IN_EP`      | `0x81`                                       | USB input endpoint (usb mode only)      |
| `PRINTER_OUT_EP`     | `0x01`                                       | USB output endpoint (usb mode only)     |
| `MQTT_BROKER_HOST`   | `mosquitto`                                  | MQTT broker hostname                    |
| `MQTT_BROKER_PORT`   | `1883`                                       | MQTT broker port                        |
| `MQTT_BROKER_USER`   | `printer`                                    | MQTT username                           |
| `MQTT_BROKER_PASS`   | `printer`                                    | MQTT password                           |
| `MQTT_PRINTERS`      | `jesse-printer:Jesse,kitchen-huxley:Kitchen` | Comma-separated `id:Label` printer list |

See `.env.example` for all available variables.

## API Documentation

The API is available at `http://printer.mccannical.com/api/` (or `http://<pi-ip>:3000/api/`). All POST endpoints accept JSON with `Content-Type: application/json`.

### Endpoints

- `GET /api/printers` — List available printers and current mode
- `GET /api/status` — Debug info (dummy output in mock mode)
- `POST /api/print/recipe` — Print a recipe from URL or text
- `POST /api/print/todo` — Print a todo/checklist

### Examples

**Print a recipe from a URL:**

```bash
curl -X POST http://printer.mccannical.com/api/print/recipe \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "url",
    "url": "https://www.allrecipes.com/recipe/24002/easy-meatloaf/",
    "printer": "jesse-printer"
  }'
```

**Print a recipe from raw text:**

```bash
curl -X POST http://printer.mccannical.com/api/print/recipe \
  -H 'Content-Type: application/json' \
  -d '{
    "mode": "text",
    "title": "Scrambled Eggs",
    "text": "3 eggs\n1 tbsp butter\nSalt and pepper\n\nWhisk eggs. Melt butter in pan over medium heat. Pour in eggs, stir gently until set.",
    "printer": "kitchen-huxley"
  }'
```

**Print a todo list:**

```bash
curl -X POST http://printer.mccannical.com/api/print/todo \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Grocery List",
    "items": "# Produce\n- Bananas\n- Spinach\n- Avocados\n# Dairy\n- Milk\n- Butter\n# Meat\n- Chicken thighs",
    "printer": "jesse-printer"
  }'
```

**Preview before printing** (returns formatted text without sending to printer):

```bash
curl -X POST http://printer.mccannical.com/api/print/todo \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Morning Routine",
    "items": "- [ ] Make bed\n- [ ] Stretch\n- [ ] Coffee",
    "printer": "jesse-printer",
    "preview": true
  }'
```

### Printers

| ID               | Name    | Location        |
| ---------------- | ------- | --------------- |
| `jesse-printer`  | Jesse   | Jesse's desk    |
| `kitchen-huxley` | Kitchen | Kitchen counter |

Get the current list at any time:

```bash
curl http://printer.mccannical.com/api/printers
```

### Todo Markdown Syntax

The `items` field in `/api/print/todo` supports markdown-like formatting:

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

## CI/CD

Three GitHub Actions workflows run on pushes to `main`:

| Workflow         | Trigger             | Description                                                                                          |
| ---------------- | ------------------- | ---------------------------------------------------------------------------------------------------- |
| **Commitlint**   | push & PR to `main` | Enforces [Conventional Commits](https://www.conventionalcommits.org/) format                         |
| **Release**      | push to `main`      | Automated versioning & changelogs via [release-please](https://github.com/googleapis/release-please) |
| **Deploy to Pi** | push to `main`      | Self-hosted runner syncs code to Pi and runs `docker compose up --build -d`                          |

## Deployment

### Podman Quadlet (brain server — current)

The primary deployment runs on `brain.mccannical.com` using Podman quadlets — systemd unit files that manage containers natively without Docker Compose.

**Architecture:** All three containers (`mosquitto`, `backend`, `frontend`) run inside a single Podman pod sharing the same network namespace (localhost). nginx proxies `/api/` to `localhost:8080`.

**Quadlet files** (`~/.config/containers/systemd/`):

| File | Description |
|------|-------------|
| `checkoff-printer.pod` | Pod definition, publishes ports 3000, 1883, 9883 |
| `checkoff-printer-mosquitto.container` | Mosquitto MQTT broker |
| `checkoff-printer-backend.container` | Flask API (locally built image) |
| `checkoff-printer-frontend.container` | nginx frontend (locally built image) |

**Runtime data** (`/opt/openclaw/platform/apps/printer/`):

```
config/
  mosquitto.conf      # allow_anonymous true, stdout logging
  nginx.conf          # proxies /api/ to localhost:8080
data/
  mosquitto/data/     # MQTT persistence
  logs/               # print logs
```

**Managing services:**

```bash
# Start
systemctl --user start checkoff-printer-pod checkoff-printer-mosquitto checkoff-printer-backend checkoff-printer-frontend

# Stop
systemctl --user stop checkoff-printer-frontend checkoff-printer-backend checkoff-printer-mosquitto checkoff-printer-pod

# Status
systemctl --user status checkoff-printer-pod checkoff-printer-backend checkoff-printer-frontend

# Logs
journalctl --user -u checkoff-printer-backend -f
```

**Rebuilding images** (after code changes):

```bash
# Clone or pull latest
git clone https://github.com/mccannical/checkoff-printer /opt/openclaw/workspace/huxley/infra/checkoff-printer/src

# Rebuild
podman build -t checkoff-printer-backend:latest ./backend
podman build -t checkoff-printer-frontend:latest ./frontend

# Restart to pick up new images
systemctl --user restart checkoff-printer-backend checkoff-printer-frontend
```

> **Note:** The pod's nginx.conf (mounted from `config/nginx.conf`) uses `localhost:8080` as the backend upstream instead of `backend:8080`. This is required because all containers share the pod's network namespace.

---

### Raspberry Pi (legacy)

The original deployment runs on a Raspberry Pi at `printer.mccannical.com`. Pushing to `main` triggers automatic deployment via a self-hosted GitHub Actions runner:

1. Checks out the code
2. Rsyncs to `/home/printer/checkoff-printer/` (excluding `.git`, `.venv`, `.env`, etc.)
3. Installs the systemd service if not already present
4. Rebuilds & restarts Docker Compose services

### Subpath Deployment

The app is served under the `/checkoff/` subpath at `printer.mccannical.com/checkoff/`. API paths in `frontend/app.js` use **relative paths** (e.g., `api/printers` instead of `/api/printers`) so that requests resolve correctly regardless of the base path. This is important because absolute paths would break when the app is mounted under a subpath like `/checkoff/`.

## Development

- **Linting**: `cd backend && uv run ruff check .`
- **Auto-fix**: `cd backend && uv run ruff check --fix .`
- **Type Checking**: `cd backend && uv run ty .`
- **Tests**: `cd backend && uv run pytest tests/`
- **Single test**: `cd backend && uv run pytest tests/test_extraction_batch.py -k "test_recipe_extraction[URL]"`

> **Note:** `test_extraction_batch.py` makes live HTTP requests to recipe URLs listed in `data/test-recipes.txt`.
