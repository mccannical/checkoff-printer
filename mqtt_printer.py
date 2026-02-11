"""Thin MQTT publish wrapper for thermal printers.

Publishes raw ESC/POS bytes to an MQTT broker. GL300 routers subscribe
to the relevant topics and forward payloads to USB-connected printers.
"""

import logging

import paho.mqtt.client as mqtt

log = logging.getLogger(__name__)


class MqttPrinter:
    """Publishes print jobs over MQTT."""

    def __init__(self, host: str, port: int, user: str, password: str):
        self._client = mqtt.Client()
        self._client.username_pw_set(user, password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

        try:
            self._client.connect(host, port)
        except Exception:
            log.exception("Failed to connect to MQTT broker at %s:%s", host, port)
            raise

        self._client.loop_start()

    # -- public api ----------------------------------------------------------

    def publish(self, printer_name: str, data: bytes) -> None:
        """Publish raw ESC/POS bytes to a printer's job topic."""
        topic = f"printer/{printer_name}/jobs"
        result = self._client.publish(topic, payload=data, qos=1)
        if result.rc != mqtt.MQTT_ERR_SUCCESS:
            log.error(
                "Publish to %s failed (rc=%s)", topic, result.rc
            )
        else:
            log.debug("Published %d bytes to %s", len(data), topic)

    def disconnect(self) -> None:
        """Stop the background network loop and disconnect cleanly."""
        self._client.loop_stop()
        self._client.disconnect()
        log.info("Disconnected from MQTT broker")

    # -- callbacks -----------------------------------------------------------

    @staticmethod
    def _on_connect(client, userdata, flags, rc):
        if rc == 0:
            log.info("Connected to MQTT broker")
        else:
            log.error("MQTT connection failed (rc=%s)", rc)

    @staticmethod
    def _on_disconnect(client, userdata, rc):
        if rc != 0:
            log.warning("Unexpected MQTT disconnect (rc=%s)", rc)
