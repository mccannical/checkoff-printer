from typing import Any
import os
import textwrap

from escpos.printer import Dummy, Usb


class PrinterService:
    def __init__(self, mode="mock", usb_args=None):
        print(f"Initializing PrinterService in {mode.upper()} mode")
        self.mode = mode
        self.printer: Any = None

        # Epson TM-H6000IV Vendor/Product IDs (Standard Epson IDs, user might need to adjust)
        # Default is usually Vendor: 0x04b8 (Seiko Epson)
        self.usb_args = usb_args or {
            "idVendor": int(os.environ.get("PRINTER_VENDOR_ID", "0x04B8"), 16),
            "idProduct": int(os.environ.get("PRINTER_PRODUCT_ID", "0x0202"), 16),
            "in_ep": int(os.environ.get("PRINTER_IN_EP", "0x81"), 16),
            "out_ep": int(os.environ.get("PRINTER_OUT_EP", "0x01"), 16),
        }

        self._connect()

    def _connect(self):
        if self.mode == "usb":
            try:
                self.printer = Usb(
                    self.usb_args["idVendor"],
                    self.usb_args["idProduct"],
                    0,
                    self.usb_args["in_ep"],
                    self.usb_args["out_ep"],
                )
            except Exception as e:
                print(f"Failed to connect to USB Printer: {e}. Falling back to Dummy.")
                self.printer = Dummy()
        else:
            self.printer = Dummy()

    def _normalize_fractions(self, text):
        """Replaces Unicode fraction characters with their ASCII counterparts."""
        if not text:
            return ""

        fraction_map = {
            "\u00bd": "1/2",
            "\u00bc": "1/4",
            "\u00be": "3/4",
            "\u2150": "1/7",
            "\u2151": "1/9",
            "\u2152": "1/10",
            "\u2153": "1/3",
            "\u2154": "2/3",
            "\u2155": "1/5",
            "\u2156": "2/5",
            "\u2157": "3/5",
            "\u2158": "4/5",
            "\u2159": "1/6",
            "\u215a": "5/6",
            "\u215b": "1/8",
            "\u215c": "3/8",
            "\u215d": "5/8",
            "\u215e": "7/8",
        }

        for unicode_frac, ascii_frac in fraction_map.items():
            text = text.replace(unicode_frac, ascii_frac)
        return text

    def _wrap_text(self, text, width=42, indent=""):
        """Wraps text to the specified width, preserving existing newlines."""
        if not text:
            return ""

        text = self._normalize_fractions(text)
        wrapped_lines = []
        for line in text.splitlines():
            if not line.strip():
                wrapped_lines.append("")
                continue

            wrapped = textwrap.fill(
                line, width=width, initial_indent=indent, subsequent_indent=indent
            )
            wrapped_lines.append(wrapped)

        return "\n".join(wrapped_lines)

    def print_text(self, text):
        """Prints simple text with automatic encoding handling"""
        self.printer.text(text)
        if hasattr(self.printer, "cut"):
            self.printer.cut()

    def _generate_recipe_text(self, title, ingredients, instructions):
        """Generates the text content for a recipe"""
        out = []
        # Title usually centers or wraps, but for preview we just wrap
        out.append(self._wrap_text(title))
        out.append("-" * 42)
        out.append("INGREDIENTS")
        for ing in ingredients:
            # indent ingredients slightly or just wrap them
            out.append(self._wrap_text(f"[ ] {ing}", indent="    "))
        out.append("")
        out.append("INSTRUCTIONS")
        out.append(self._wrap_text(instructions))
        out.append("\n")
        return "\n".join(out)

    def get_recipe_preview(self, title, ingredients, instructions):
        return self._generate_recipe_text(title, ingredients, instructions)

    def print_recipe(self, title, ingredients, instructions):
        """Formats and prints a recipe"""
        self.printer.hw("init")

        # Title
        self.printer.set(
            align="center",
            double_height=False,
            double_width=False,
            bold=True,
            font="b",
        )
        # We might not want to hard wrap the title if we trust the printer's flow,
        # but 42 chars doubled is 21 chars, so it might overflow.
        # For safety/consistency with preview:
        self.printer.text(
            self._wrap_text(title, width=21) + "\n"
        )  # Double width = half capacity
        self.printer.set(
            align="left",
            double_height=False,
            double_width=False,
            bold=False,
            font="b",
        )
        self.printer.text("-" * 42 + "\n")  # 42 chars is approx width for 80mm

        # Ingredients
        self.printer.set(bold=True, font="b")
        self.printer.text("INGREDIENTS\n")
        self.printer.set(bold=False, font="b")
        for ing in ingredients:
            # indent slightly for checkbox look
            # The preview used 4 spaces, we can do similar or just plain
            txt = self._wrap_text(f"[ ] {ing}", indent="    ")
            self.printer.text(f"{txt}\n")

        self.printer.text("\n")

        # Instructions
        self.printer.set(bold=True, font="b")
        self.printer.text("INSTRUCTIONS\n")
        self.printer.set(bold=False, font="b")
        self.printer.text(self._wrap_text(instructions) + "\n\n")

        self.printer.cut()

    def _generate_todo_text(self, title, items):
        out = []
        out.append(self._wrap_text(title))
        out.append("-" * 42)
        for item in items:
            out.append(self._wrap_text(f"[ ] {item}"))
        out.append("\n")
        return "\n".join(out)

    def get_todo_preview(self, title, items):
        return self._generate_todo_text(title, items)

    def print_todo(self, title, items):
        """Formats and prints a todo list"""
        self.printer.hw("init")

        self.printer.set(align="center", double_height=False, bold=True, font="b")
        self.printer.text(self._wrap_text(title) + "\n")
        self.printer.set(
            align="left",
            double_height=False,
            double_width=False,
            bold=False,
            font="b",
        )
        self.printer.text("-" * 42 + "\n")

        for item in items:
            self.printer.text(self._wrap_text(f"[ ] {item}") + "\n")

        self.printer.text("\n\n")
        self.printer.cut()

    def get_dummy_output(self):
        """Returns the output if in Dummy mode"""
        if isinstance(self.printer, Dummy):
            return self.printer.output
        return b""
