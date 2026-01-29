---
description: How to deploy Checkoff Printer to a Raspberry Pi
---

# Deploying to Raspberry Pi

This guide covers how to deploy the Checkoff Printer application to a Raspberry Pi with a USB Thermal Printer.

## Prerequisites

- Raspberry Pi (Zero W, 3, 4, or 5) running Raspberry Pi OS.
- Docker and Docker Compose installed on the Pi.
  ```bash
  curl -sSL https://get.docker.com | sh
  sudo usermod -aG docker $USER
  ```
- A USB Thermal Printer connected to the Pi.

## Step 1: Transfer Code
Copy the project files to your Raspberry Pi. You can use `scp`, `rsync`, or just `git clone` if you push your changes to a repository.

```bash
# Example using rsync
rsync -avz --exclude 'venv' --exclude '__pycache__' ./ pi@raspberrypi.local:~/checkoff-printer
```

## Step 2: Identify Printer IDs
Connect your thermal printer to the Pi and run:

```bash
lsusb
```

Look for your printer in the output. It typically looks like:
`Bus 001 Device 004: ID 04b8:0202 Seiko Epson Corp. Receipt Printer`

In this example:
- **Vendor ID**: `04b8`
- **Product ID**: `0202`

## Step 3: Configure Deployment
You can configure the application using environment variables.

1. Create a `.env` file in the project directory on the Pi:

```bash
# .env file content
PRINTER_MODE=usb
PRINTER_VENDOR_ID=0x04b8
PRINTER_PRODUCT_ID=0x0202
# Optional: Adjust endpoints if needed (defaults are usually fine)
# PRINTER_IN_EP=0x81
# PRINTER_OUT_EP=0x01
```

> [!NOTE]
> Make sure to prefix the IDs with `0x`.

## Step 4: Deploy with Docker Compose
The `docker-compose.yml` is already configured to pass USB devices to the container.

1. Build and start the container:
```bash
docker compose up -d --build
```

2. Check logs to ensure it connected:
```bash
docker compose logs -f
```

## Step 5: Access the Interface
Open a browser on your computer/phone and navigate to:
`http://raspberrypi.local:8080`

## Troubleshooting

### "Printer not found" or Permission Errors
- Ensure the Docker container has `privileged: true` in `docker-compose.yml` (already added).
- Try unplugging and replugging the printer.
- Verify the IDs in `.env` match `lsusb` exactly.

### "Endpoint not found"
- You may need to identify the correct Input/Output endpoints using `lsusb -v` or a Python script to inspect the device descriptors.
