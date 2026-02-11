# Changelog

## [Unreleased] - 2026-02-11

### GL300 Router Print Network Setup

Configured two GL-iNet GL-AR300M routers as networked print servers for Epson TM-H6000IV thermal printers, connected via MQTT.

#### Infrastructure
- **MQTT Broker**: Deployed Eclipse Mosquitto 2.1.2 in Docker on 192.168.50.211:1883 with authenticated access (user: `printer`)
- **jesse-printer** (192.168.50.208): GL-AR300M with TM-H6000IV, subscribing to `printer/jesse-printer/jobs`
- **kitchen-huxley** (192.168.50.59): GL-AR300M with TM-H6000IV, subscribing to `printer/kitchen-huxley/jobs`

#### Router Configuration (both routers)
- Installed `kmod-usb-printer` kernel module (printers detected at `/dev/usb/lp0`)
- Installed `mosquitto-client-ssl` for MQTT subscription
- Deployed `/root/print-agent.sh` — shell script that subscribes to MQTT topic and forwards messages to USB printer
- Deployed `/etc/init.d/print-agent` — procd service with auto-restart and respawn on failure
- Verified end-to-end: publish to MQTT broker -> GL300 receives -> prints to thermal printer

#### Files Created (not yet in repo)
- `backend/docker-compose.yml` — Mosquitto broker Docker config (created in monitoring dir, needs migration)
- `backend/mqtt/config/mosquitto.conf` — Broker config (port 1883, auth required)
- `backend/mqtt/config/passwd` — Hashed credentials
- `printers/install.sh` — Automated GL300 setup script (installs packages, deploys print agent, creates init service)

#### Architecture
```
[Flask App] --publish--> [MQTT Broker :1883] <--subscribe-- [GL300 routers]
                          (192.168.50.211)                    --> /dev/usb/lp0
                                                              --> Epson TM-H6000IV
```

---

## [v0.0.1] - 2026-01-29

### Added
- **Markdown Todo Support**: Use `# Headers`, `- [ ] Tasks`, and `**Bold**` in todo lists.
- **Print Logging**: All prints are automatically saved as `.txt` files in the `logs/` directory with timestamps and source URLs.
- **Global Font B**: Switched to compact "Font B" for all thermal prints.
- **Fraction Normalization**: Automatic conversion of Unicode fractions (½, ⅓, etc.) to ASCII (1/2, 1/3, etc.) for better readability.
- **Systemd Service**: Initial configuration for running the app as a service on boot using `uv run`.
- **Gitignore**: Comprehensive ignore list for Python, Logs, and IDE files.

### Changed
- Improved printer service robustness with safety checks for `Mock` mode.
- Optimized title and header formatting for font size hierarchy.

### Fixed
- Resolved `217/USER` and `203/EXEC` service errors by correcting user paths and using absolute script references.
- Fixed `AttributeError` in Mock mode for non-standard ESC/POS implementations.
