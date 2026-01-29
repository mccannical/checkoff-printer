# Checkoff Printer

A "Smart" Thermal Printer application for your home. It connects a Raspberry Pi to an Epson TM-H6000IV thermal printer to nicely format and print Recipes and Todo Lists.

## Features
-   **Web Interface**: Mobile-first UI to paste recipes or manage lists.
-   **Smart Formatting**: Automatically scrapes ingredients/steps from recipe URLs or raw text and formats them to fit the 80mm thermal tape.
-   **Print Preview**: "Dry Run" mode to see exactly what will print.
-   **Hardware & Mock Modes**: Works with real USB hardware or simulates output for development.

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
# Using uv (checks pyproject.toml)
export PRINTER_MODE=mock
uv run app.py

# OR directly with python
export PRINTER_MODE=mock
python app.py
```
Open [http://localhost:8080](http://localhost:8080) in your browser.

### Prodution (Raspberry Pi + USB)
1.  **Connect Printer**: Plug in the Epson TM-H6000IV via USB.
2.  **Find Device IDs**: Run `lsusb` to confirm vendor/product IDs.
    -   Default configured: `04b8:0202`. 
    -   If different, update `printer_service.py` or pass arguments.
3.  **Run**:
    ```bash
    export PRINTER_MODE=usb
    python app.py
    ```

## Docker Deployment
The easiest way to run on a Pi. The container includes all system dependencies.

1.  **Build & Run**:
    ```bash
    docker-compose up --build -d
    ```
    *Note: `docker-compose.yml` uses privileged mode/device mapping to access USB.*

## API Documentation

-   `POST /api/print/recipe`
    -   Body: `{ "mode": "url"|"text", "url": "...", "title": "...", "text": "...", "preview": boolean }`
-   `POST /api/print/todo`
    -   Body: `{ "title": "...", "items": "Line 1\nLine 2", "preview": boolean }`

## Development
-   **Linting**: `uv run ruff check .`
-   **Type Checking**: `uv run ty .`
