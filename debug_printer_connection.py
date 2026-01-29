import usb.core
import usb.util
from escpos.printer import Usb
import sys


def scan_usb():
    print("Scanning USB devices...")
    devs = usb.core.find(find_all=True)
    found_printer = False
    for dev in devs:
        try:
            # Try to get manufacturer string, might fail if permissions are wrong
            manufacturer = usb.util.get_string(dev, dev.iManufacturer)
            product = usb.util.get_string(dev, dev.iProduct)
            print(
                f"Found Device: ID {hex(dev.idVendor)}:{hex(dev.idProduct)} - {manufacturer} {product}"
            )

            # Common Epson IDs or if user mentioned it
            if dev.idVendor == 0x04B8:
                print("  -> LIKELY EPSON PRINTER")
                found_printer = True
        except Exception as e:
            print(
                f"Found Device: ID {hex(dev.idVendor)}:{hex(dev.idProduct)} (Could not read details: {e})"
            )

    if not found_printer:
        print("\nWARNING: Did not find a device with Vendor ID 0x04b8 (Epson).")
        print("If you have a different printer, please check the IDs above.")


def test_printer_connection():
    print("\nAttempting to connect to printer with default settings (04b8:0202)...")
    try:
        # Default Epson TM-H6000IV IDs from code
        # Vendor: 0x04b8, Product: 0x0202
        # Endpoints: 0x81, 0x01
        p = Usb(0x04B8, 0x0202, 0, 0x81, 0x01)
        print("Success! Connection established.")

        print("Printing test line...")
        p.text("Hello from Debug Script!\n")
        p.cut()
        print("Print sent successfully.")

    except Exception as e:
        print(f"FAILED to connect: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if Vendor/Product IDs match the scan above.")
        print(
            "2. Check permissions: 'sudo python debug_printer_connection.py' might work if udev rules aren't set."
        )
        print("3. Check connection cables.")


if __name__ == "__main__":
    scan_usb()
    test_printer_connection()
