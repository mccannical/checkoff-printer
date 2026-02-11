#!/bin/sh
# GL300 Printer Agent Installer
# Usage: ./install.sh <router_ip> <router_password> <printer_name>
# Example: ./install.sh 192.168.50.208 'dytTes-gevfi1-rospax' jesse-printer

set -e

ROUTER_IP="$1"
ROUTER_PASS="$2"
PRINTER_NAME="$3"
BROKER_HOST="${BROKER_HOST:-192.168.50.211}"
BROKER_PORT="${BROKER_PORT:-1883}"
BROKER_USER="${BROKER_USER:-printer}"
BROKER_PASS="${BROKER_PASS:-printer}"

if [ -z "$ROUTER_IP" ] || [ -z "$ROUTER_PASS" ] || [ -z "$PRINTER_NAME" ]; then
    echo "Usage: $0 <router_ip> <router_password> <printer_name>"
    echo "  Env vars: BROKER_HOST, BROKER_PORT, BROKER_USER, BROKER_PASS"
    exit 1
fi

run_ssh() {
    sshpass -p "$ROUTER_PASS" ssh -o StrictHostKeyChecking=no "root@$ROUTER_IP" "$@"
}

echo "==> Installing packages on $PRINTER_NAME ($ROUTER_IP)..."
run_ssh "opkg update && opkg install kmod-usb-printer mosquitto-client-ssl"

echo "==> Verifying printer device..."
run_ssh "ls /dev/usb/lp0" || {
    echo "ERROR: No printer found at /dev/usb/lp0"
    exit 1
}

echo "==> Creating print agent script..."
run_ssh "cat > /root/print-agent.sh" <<EOF
#!/bin/sh
BROKER_HOST="$BROKER_HOST"
BROKER_PORT="$BROKER_PORT"
BROKER_USER="$BROKER_USER"
BROKER_PASS="$BROKER_PASS"
PRINTER_NAME="$PRINTER_NAME"
PRINTER_DEV="/dev/usb/lp0"
TOPIC="printer/\$PRINTER_NAME/jobs"

logger -t print-agent "Starting print agent for \$PRINTER_NAME"
logger -t print-agent "Subscribing to \$TOPIC on \$BROKER_HOST:\$BROKER_PORT"

while true; do
    mosquitto_sub \\
        -h "\$BROKER_HOST" \\
        -p "\$BROKER_PORT" \\
        -u "\$BROKER_USER" \\
        -P "\$BROKER_PASS" \\
        -t "\$TOPIC" \\
        -N \\
        > "\$PRINTER_DEV" 2>/dev/null
    logger -t print-agent "Connection lost, reconnecting in 5s..."
    sleep 5
done
EOF

run_ssh "chmod +x /root/print-agent.sh"

echo "==> Creating init service..."
run_ssh "cat > /etc/init.d/print-agent" <<'INITSCRIPT'
#!/bin/sh /etc/rc.common
START=99
STOP=10
USE_PROCD=1

start_service() {
    procd_open_instance
    procd_set_param command /root/print-agent.sh
    procd_set_param respawn 3600 5 5
    procd_set_param stdout 1
    procd_set_param stderr 1
    procd_close_instance
}
INITSCRIPT

run_ssh "chmod +x /etc/init.d/print-agent"
run_ssh "/etc/init.d/print-agent enable"
run_ssh "/etc/init.d/print-agent start"

echo "==> Verifying..."
sleep 2
run_ssh "ps | grep -v grep | grep print-agent" && \
    echo "==> SUCCESS: Print agent running on $PRINTER_NAME ($ROUTER_IP)" || \
    echo "==> WARNING: Print agent may not be running, check logs with: logread | grep print-agent"
