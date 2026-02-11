import os

from flask import Flask, jsonify, render_template, request

from formatters.recipe import RecipeFormatter
from formatters.todo import TodoFormatter
from printer_service import PrinterService

app = Flask(__name__)

# Initialize Printer (Default to mock for safety until configured)
# In production, user would change this or we'd load from env
PRINTER_MODE = os.environ.get("PRINTER_MODE", "mock")

if PRINTER_MODE == "mqtt":
    mqtt_config = {
        "host": os.environ.get("MQTT_BROKER_HOST", "192.168.50.211"),
        "port": int(os.environ.get("MQTT_BROKER_PORT", "1883")),
        "user": os.environ.get("MQTT_BROKER_USER", "printer"),
        "password": os.environ.get("MQTT_BROKER_PASS", "printer"),
    }
    print_service = PrinterService(mode="mqtt", mqtt_config=mqtt_config)
else:
    print_service = PrinterService(mode=PRINTER_MODE)

# Parse printer list from env: "jesse-printer:Jesse,kitchen-huxley:Kitchen"
MQTT_PRINTERS_RAW = os.environ.get("MQTT_PRINTERS", "jesse-printer:Jesse,kitchen-huxley:Kitchen")
MQTT_PRINTERS = []
if PRINTER_MODE == "mqtt":
    for entry in MQTT_PRINTERS_RAW.split(","):
        parts = entry.strip().split(":")
        if len(parts) == 2:
            MQTT_PRINTERS.append({"id": parts[0], "name": parts[1]})

recipe_formatter = RecipeFormatter()
todo_formatter = TodoFormatter()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/api/printers")
def get_printers():
    return jsonify({
        "printers": MQTT_PRINTERS,
        "mode": print_service.mode,
    })


@app.route("/api/print/recipe", methods=["POST"])
def print_recipe():
    data = request.json
    mode = data.get("mode", "url")  # 'url' or 'text'

    parsed_data = {}
    if mode == "url":
        url = data.get("url")
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        parsed_data = recipe_formatter.parse_url(url)
    else:
        title = data.get("title", "My Recipe")
        text = data.get("text", "")
        # Basic text pass-through for now
        parsed_data = recipe_formatter.parse_text(title, text)

    if print_service.mode == "mqtt":
        printer_id = data.get("printer")
        if not printer_id:
            return jsonify({"error": "No printer selected"}), 400
        print_service.set_target(printer_id)

    try:
        if data.get("preview"):
            preview_text = print_service.get_recipe_preview(
                parsed_data["title"],
                parsed_data["ingredients"],
                parsed_data["instructions"],
            )
            return jsonify({"status": "success", "preview": preview_text})

        print_service.print_recipe(
            parsed_data["title"],
            parsed_data["ingredients"],
            parsed_data["instructions"],
            url=data.get("url"),
        )
        return jsonify(
            {"status": "success", "message": f"Printed '{parsed_data['title']}'"}
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/print/todo", methods=["POST"])
def print_todo():
    data = request.json
    title = data.get("title", "To Do")
    items_text = data.get("items", "")

    items = todo_formatter.parse(items_text)

    if not items:
        return jsonify({"error": "No items provided"}), 400

    if print_service.mode == "mqtt":
        printer_id = data.get("printer")
        if not printer_id:
            return jsonify({"error": "No printer selected"}), 400
        print_service.set_target(printer_id)

    try:
        if data.get("preview"):
            preview_text = print_service.get_todo_preview(title, items)
            return jsonify({"status": "success", "preview": preview_text})

        print_service.print_todo(title, items)
        return jsonify({"status": "success", "message": f"Printed {len(items)} items"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/status")
def status():
    # Only useful in mock mode to see what happened
    return jsonify(
        {
            "mode": print_service.mode,
            "dummy_output": str(print_service.get_dummy_output()),
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
