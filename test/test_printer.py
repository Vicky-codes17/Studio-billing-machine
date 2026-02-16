import sys
import os

def test_usb_dependencies():
    """Test if USB dependencies are installed"""
    try:
        import usb.core
        import usb.util
        print("✅ USB libraries installed successfully")
        return True
    except ImportError as e:
        print(f"❌ USB library missing: {e}")
        print("💡 Install with: pip install pyusb")
        print("💡 On Ubuntu: sudo apt-get install libusb-1.0-0-dev")
        return False

def find_thermal_printers():
    """Find connected thermal printers"""
    try:
        import usb.core
        
        # Common thermal printer vendor/product IDs
        thermal_printers = [
            (0x09c5, 0x588e),  # Your current printer
            (0x04b8, 0x0202),  # Epson TM series
            (0x04b8, 0x0005),  # Epson TM-T88
            (0x154f, 0x154f),  # Generic thermal
            (0x0483, 0x5740),  # STM-based printers
        ]
        
        found_printers = []
        devices = usb.core.find(find_all=True)
        
        for device in devices:
            # Ensure we are working with a Device object
            if hasattr(device, 'idVendor') and hasattr(device, 'idProduct'):
                vendor_id = device.idVendor
                product_id = device.idProduct

                # Check if it's a known thermal printer
                if (vendor_id, product_id) in thermal_printers:
                    found_printers.append({
                        'vendor_id': f"0x{vendor_id:04x}",
                        'product_id': f"0x{product_id:04x}",
                        'device': device
                    })
                    print(f"🖨️ Found thermal printer: {vendor_id:04x}:{product_id:04x}")
        
        return found_printers
        
    except Exception as e:
        print(f"❌ Error scanning for printers: {e}")
        return []

def test_thermal_printer(vendor_id=0x09c5, product_id=0x588e):
    """Test thermal printer with better error handling"""
    try:
        # Check dependencies first
        if not test_usb_dependencies():
            return False
        
        from escpos.printer import Usb
        from escpos.exceptions import USBNotFoundError, Error as EscposError
        
        print(f"🔍 Attempting to connect to printer: {vendor_id:04x}:{product_id:04x}")
        
        # Try to connect
        p = Usb(vendor_id, product_id)
        
        # Test print
        print("📄 Sending test print...")
        p.text("=" * 32 + "\n")
        p.text("🖨️ THERMAL PRINTER TEST\n")
        p.text("=" * 32 + "\n")
        p.text("Hello from Python!\n")
        p.text(f"Vendor ID: 0x{vendor_id:04x}\n")
        p.text(f"Product ID: 0x{product_id:04x}\n")
        p.text("Test completed successfully!\n")
        p.text("\n\n")
        p.cut()
        
        print("✅ Test print sent successfully!")
        return True
        
    except USBNotFoundError:
        print(f"❌ Printer not found: {vendor_id:04x}:{product_id:04x}")
        print("💡 Check:")
        print("   1. Printer is connected via USB")
        print("   2. Printer is powered on")
        print("   3. USB cable is working")
        print("   4. Run 'lsusb' to see connected devices")
        return False
        
    except PermissionError:
        print("❌ Permission denied accessing USB device")
        print("💡 Try:")
        print("   1. sudo python test_printer.py")
        print("   2. Add udev rules (see setup instructions)")
        print(f"   3. sudo usermod -a -G plugdev {os.getenv('USER', 'your_username')}")
        return False
        
    except EscposError as e:
        print(f"❌ Printer error: {e}")
        print("💡 The printer might not support ESC/POS commands")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Thermal Printer Test Script")
    print("=" * 40)
    
    # Check dependencies
    if not test_usb_dependencies():
        sys.exit(1)
    
    # Scan for printers
    print("\n🔍 Scanning for thermal printers...")
    found_printers = find_thermal_printers()
    
    if found_printers:
        print(f"\n✅ Found {len(found_printers)} thermal printer(s)")
        for i, printer in enumerate(found_printers):
            print(f"   {i+1}. {printer['vendor_id']}:{printer['product_id']}")
        
        # Test first printer found
        printer = found_printers[0]
        vendor_id = int(printer['vendor_id'], 16)
        product_id = int(printer['product_id'], 16)
        
        print(f"\n🧪 Testing printer: {printer['vendor_id']}:{printer['product_id']}")
        test_thermal_printer(vendor_id, product_id)
    else:
        print("\n⚠️ No thermal printers found")
        print("💡 Using default IDs: 0x09c5:0x588e")
        test_thermal_printer()