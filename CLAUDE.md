# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Checkoff Printer is a multi-service monorepo for formatting and printing recipes and todo lists to Epson TM-H6000IV thermal printers. It supports three printer modes: `mock` (development), `usb` (direct USB), and `mqtt` (networked via GL-iNet GL300 routers running MQTT subscriber agents).

## Repository Structure

```
frontend/       # Static SPA served by nginx (index.html, app.js, style.css)
backend/        # Flask API server (app.py, printer_service.py, formatters/)
installers/     # Provisioning scripts (GL300 routers, Pi host setup)
tools/          # Standalone utility scripts (recipe extraction, URL fetching, debug)
data/           # Data files (recipes.json, test-recipes.txt, seed-recipes.txt)
```

## Commands

### Development
```bash
cd backend && uv sync                          # Install dependencies
cd backend && PRINTER_MODE=mock uv run app.py  # Run backend on :8080
```

For frontend development, open `frontend/index.html` directly or use the Docker setup.

### Docker (full stack)
```bash
docker compose up --build -d    # Builds frontend (nginx) + backend (Flask) + mosquitto
```
Frontend is served at `:80`, proxying `/api/` requests to the backend.

### Linting & Type Checking
```bash
cd backend && uv run ruff check .            # Lint (pycodestyle, pyflakes, isort)
cd backend && uv run ruff check --fix .      # Auto-fix lint issues
cd backend && uv run ty .                    # Type checking
```

### Tests
```bash
cd backend && uv run pytest tests/                              # Run all tests
cd backend && uv run pytest tests/test_extraction_batch.py -k "test_recipe_extraction[URL]"  # Single parametrized test
```

Note: `test_extraction_batch.py` makes live HTTP requests to recipe URLs listed in `data/test-recipes.txt`.

## Architecture

**Request flow:** Browser → nginx (frontend) → reverse proxy `/api/` → Flask routes (backend/`app.py`) → Formatters parse input → `PrinterService` renders ESC/POS → output destination (Dummy buffer, USB, or MQTT broker → GL300 router → physical printer).

### Key modules

- **`backend/app.py`** — Flask entry point. API-only (no template serving). Reads `PRINTER_MODE` env var, configures `PrinterService`, defines API routes (`/api/print/recipe`, `/api/print/todo`, `/api/printers`, `/api/status`). Debug CORS enabled when `app.debug` is True.
- **`backend/printer_service.py`** (`PrinterService`) — Core print logic. Uses `python-escpos` `Dummy` printer to build ESC/POS byte streams. In MQTT mode, flushes the Dummy buffer to `MqttPrinter`. Handles text wrapping (42-char width for 80mm tape), Unicode fraction normalization, and print logging to `logs/`.
- **`backend/mqtt_printer.py`** (`MqttPrinter`) — Publishes raw ESC/POS bytes to MQTT topic `printer/{name}/jobs`. GL300 routers subscribe and pipe to `/dev/usb/lp0`.
- **`backend/formatters/recipe.py`** (`RecipeFormatter`) — Extracts recipe data from URLs via JSON-LD schema parsing, with meta tag fallback. Also handles raw text input.
- **`backend/formatters/todo.py`** (`TodoFormatter`) — Parses markdown-like syntax (headers, checkboxes, numbered/bullet lists, bold) into structured item dicts with `type` and `text` fields.
- **`tools/extract_recipes.py`** — Standalone batch script using `recipe-scrapers` library to bulk-extract recipes from `data/test-recipes.txt` into `data/recipes.json`.
- **`installers/printers/install.sh`** — SSH-based provisioning script for GL300 routers (installs `mosquitto_sub`, creates print agent service).

### Frontend
Single-page app: `frontend/index.html` + `frontend/app.js` + `frontend/style.css`. Served by nginx, communicates with backend API via `/api/` reverse proxy.

### Docker Services
- **frontend** — `nginx:alpine`, serves static files, proxies `/api/` to backend
- **backend** — Python 3.9, Flask on port 8080 (internal only)
- **mosquitto** — Eclipse Mosquitto 2, MQTT broker on port 1883

## Conventions

- Commits follow [Conventional Commits](https://www.conventionalcommits.org/) (enforced by commitlint in CI).
- Ruff config: line-length 88, target Python 3.9, rules E/F/I (isort with known-first-party: `app`, `printer_service`, `mqtt_printer`, `formatters`).
- Thermal tape width is 42 characters (80mm paper). Double-width text uses 21-char width.
