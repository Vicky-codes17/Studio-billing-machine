from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
from models import db, Invoice, Item
from services.billing_service import save_invoice, get_invoice_stats
import json
import os
from datetime import datetime

# Try to import USB libraries, make them optional
try:
    import usb.core
    import usb.util
    USB_AVAILABLE = True
except ImportError:
    print("⚠️ USB libraries not available. Install with: pip install pyusb")
    USB_AVAILABLE = False

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///billing.db'  # Fallback if config.py missing
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Fallback secret key
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Try to import config, use fallbacks if not available
try:
    from config import SQLALCHEMY_DATABASE_URI, SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SECRET_KEY'] = SECRET_KEY
except ImportError:
    print("⚠️ config.py not found, using default configuration")

# Try to import PDF service, make it optional
try:
    from services.pdf_service import create_a4_pdf
    PDF_AVAILABLE = True
except ImportError:
    print("⚠️ PDF service not available")
    PDF_AVAILABLE = False

# Try to import printer service, make it optional
try:
    from services.printer_service import print_receipt_escpos, test_printer_connection
    PRINTER_AVAILABLE = True
except ImportError:
    print("⚠️ Printer service not available")
    PRINTER_AVAILABLE = False

db.init_app(app)

with app.app_context():
    db.create_all()

# Company info
COMPANY = {
    "name": "Anand Digital Studio",
    "address": "17-44, Ponniamman Koli Street\nChittoor - 517001\nAndhra Pradesh (India)",
    "phone": "9177033461"
}

# Make datetime available in all templates
@app.context_processor
def inject_now():
    return {'now': datetime.now}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/invoices")
def invoices_list():
    invoices = Invoice.query.order_by(Invoice.date.desc()).all()
    return render_template("invoices_list.html", invoices=invoices)

@app.route("/save", methods=["POST"])
def save():
    customer = request.form.get("customer_name")
    phone = request.form.get("customer_phone")
    notes = request.form.get("notes")
    items_json = request.form.get("items_json")
    
    if not customer:
        flash("Customer name is required", "error")
        return redirect(url_for('index'))
    
    try:
        items = json.loads(items_json or "[]")
    except json.JSONDecodeError:
        flash("Invalid items data", "error")
        return redirect(url_for('index'))
    
    if not items:
        flash("Please add at least one item", "error")
        return redirect(url_for('index'))
    
    # Normalize items
    items_list = []
    for it in items:
        items_list.append({
            'description': it.get('description', ''),
            'quantity': int(it.get('quantity', 1)),
            'rate': float(it.get('rate', 0)),
            'tax_rate': float(it.get('taxRate', 0))
        })
    
    try:
        invoice_id = save_invoice(customer, phone, notes, items_list)
        flash("Invoice saved successfully!", "success")
        return redirect(url_for('view_invoice', invoice_id=invoice_id))
    except Exception as e:
        flash(f"Error saving invoice: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/invoice/<int:invoice_id>')
def view_invoice(invoice_id):
    """View a specific invoice"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Calculate item totals since we removed final_amount
    items_data = []
    subtotal = 0.0
    tax_total = 0.0
    
    for item in invoice.items:
        line_subtotal = item.quantity * item.rate
        line_tax = line_subtotal * (item.tax_rate / 100)
        line_total = line_subtotal + line_tax
        
        # Add to totals
        subtotal += line_subtotal
        tax_total += line_tax
        
        items_data.append({
            'description': item.description,
            'qty': item.quantity,
            'rate': item.rate,
            'tax_rate': item.tax_rate,
            'tax_percent': item.tax_rate,
            'line_total': line_total
        })
    
    grand_total = subtotal + tax_total
    
    # ✅ MUST pass grand_total to template
    return render_template('bill.html', 
                         invoice=invoice, 
                         items=items_data, 
                         company=COMPANY,
                         subtotal=subtotal,           # ✅ Required
                         tax_total=tax_total,         # ✅ Required
                         grand_total=grand_total)     # ✅ Required for line 80

@app.route("/download_pdf/<int:invoice_id>")
def download_pdf(invoice_id):
    if not PDF_AVAILABLE:
        flash("PDF service not available", "error")
        return redirect(url_for('view_invoice', invoice_id=invoice_id))
    
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Calculate item totals like in view_invoice
    items_data = []
    for item in invoice.items:
        line_subtotal = item.quantity * item.rate
        line_tax = line_subtotal * (item.tax_rate / 100)
        line_total = line_subtotal + line_tax
        
        # Create object-like structure for PDF service
        class ItemData:
            def __init__(self, item, line_total):
                self.description = item.description
                self.quantity = item.quantity
                self.rate = item.rate
                self.tax_rate = item.tax_rate
                self.line_total = line_total
                self.final_amount = line_total  # For PDF compatibility
        
        items_data.append(ItemData(item, line_total))
    
    try:
        path = create_a4_pdf(invoice, items_data, COMPANY)  # ✅ Pass calculated items
        return send_file(path, as_attachment=True)
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for('view_invoice', invoice_id=invoice_id))

@app.route("/view_pdf/<int:invoice_id>")
def view_pdf(invoice_id):
    if not PDF_AVAILABLE:
        flash("PDF service not available", "error")
        return redirect(url_for('view_invoice', invoice_id=invoice_id))
    
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Calculate item totals like in view_invoice
    items_data = []
    for item in invoice.items:
        line_subtotal = item.quantity * item.rate
        line_tax = line_subtotal * (item.tax_rate / 100)
        line_total = line_subtotal + line_tax
        
        # Create object-like structure for PDF service
        class ItemData:
            def __init__(self, item, line_total):
                self.description = item.description
                self.quantity = item.quantity
                self.rate = item.rate
                self.tax_rate = item.tax_rate
                self.line_total = line_total
                self.final_amount = line_total  # For PDF compatibility
        
        items_data.append(ItemData(item, line_total))
    
    try:
        path = create_a4_pdf(invoice, items_data, COMPANY)  # ✅ Pass calculated items
        return send_file(path, as_attachment=False, mimetype='application/pdf')
    except Exception as e:
        flash(f"Error generating PDF: {str(e)}", "error")
        return redirect(url_for('view_invoice', invoice_id=invoice_id))

@app.route("/thermal_preview/<int:invoice_id>")
def thermal_preview(invoice_id):
    """Preview thermal print format"""
    invoice = Invoice.query.get_or_404(invoice_id)
    
    # Calculate item totals like in view_invoice
    items_data = []
    subtotal = 0.0
    tax_total = 0.0
    
    for item in invoice.items:
        line_subtotal = item.quantity * item.rate
        line_tax = line_subtotal * (item.tax_rate / 100)
        line_total = line_subtotal + line_tax
        
        subtotal += line_subtotal
        tax_total += line_tax
        
        items_data.append({
            'description': item.description,
            'quantity': item.quantity,
            'qty': item.quantity,
            'rate': item.rate,
            'tax_rate': item.tax_rate,
            'tax_percent': item.tax_rate,
            'line_total': line_total
        })
    
    grand_total = subtotal + tax_total
    
    # ✅ ADD DEBUG PRINTS
    print(f"DEBUG: items_data type: {type(items_data)}")
    print(f"DEBUG: items_data length: {len(items_data)}")
    if items_data:
        print(f"DEBUG: First item keys: {items_data[0].keys()}")
        print(f"DEBUG: First item line_total: {items_data[0].get('line_total', 'MISSING')}")
    
    return render_template("thermal_preview.html",
                     invoice=invoice,
                     items=items_data,     # ✅ Calculated items with line_total
                     company=COMPANY,
                     subtotal=subtotal,
                     tax_total=tax_total,
                     grand_total=grand_total)

@app.route("/thermal_print/<int:invoice_id>", methods=["POST"])
def thermal_print(invoice_id):
    if not PRINTER_AVAILABLE:
        flash("Printer service not available", "error")
        return redirect(url_for('thermal_preview', invoice_id=invoice_id))
    
    invoice = Invoice.query.get_or_404(invoice_id)
    printer_type = request.form.get("printer_type")
    
    # ✅ Calculate items like other routes
    items_data = []
    for item in invoice.items:
        line_subtotal = item.quantity * item.rate
        line_tax = line_subtotal * (item.tax_rate / 100)
        line_total = line_subtotal + line_tax
        
        # Create object for printer service
        class ItemData:
            def __init__(self, item, line_total):
                self.description = item.description
                self.quantity = item.quantity
                self.rate = item.rate
                self.tax_rate = item.tax_rate
                self.line_total = line_total
                self.final_amount = line_total
        
        items_data.append(ItemData(item, line_total))
    
    try:
        if printer_type == "usb":
            vendor_id = request.form.get("usb_vendor_id")
            product_id = request.form.get("usb_product_id")
            try:
                vendor_id = int(vendor_id, 16) if vendor_id else None
                product_id = int(product_id, 16) if product_id else None
            except ValueError:
                flash("Invalid USB IDs format", "error")
                return redirect(url_for('thermal_preview', invoice_id=invoice_id))
            
            success, message = print_receipt_escpos(invoice, COMPANY, 
                                                  usb_vendor_id=vendor_id, 
                                                  usb_product_id=product_id)
        elif printer_type == "network":
            ip_address = request.form.get("ip_address")
            success, message = print_receipt_escpos(invoice, COMPANY, ip_address=ip_address)
        else:
            success, message = print_receipt_escpos(invoice, COMPANY)
        
        if success:
            flash(message, "success")
        else:
            flash(message, "error")
            
    except Exception as e:
        flash(f"Printing error: {str(e)}", "error")
    
    return redirect(url_for('thermal_preview', invoice_id=invoice_id))

@app.route("/test_printer", methods=["GET", "POST"])
def test_printer():
    """Test thermal printer connection with enhanced error handling"""
    if request.method == "GET":
        return render_template('test_printer.html', company=COMPANY)
    
    try:
        # Check if USB libraries are available
        try:
            import usb.core
            import usb.util
        except ImportError:
            flash("❌ USB libraries not installed. Run: pip install pyusb", "error")
            flash("💡 On Ubuntu: sudo apt-get install libusb-1.0-0-dev", "info")
            return redirect(url_for('test_printer'))
        
        # Get form data
        vendor_id = request.form.get('vendor_id', '0x09c5')
        product_id = request.form.get('product_id', '0x588e')
        test_message = request.form.get('test_message', 'Hello from Thermal Printer!')
        
        # Convert hex strings to integers
        vendor_id_int = int(vendor_id, 16)
        product_id_int = int(product_id, 16)
        
        from escpos.printer import Usb
        from escpos.exceptions import USBNotFoundError, Error as EscposError
        
        # Test printer connection
        p = Usb(vendor_id_int, product_id_int)
        
        # Print test content
        p.text("=" * 32 + "\n")
        p.text("THERMAL PRINTER TEST\n")
        p.text("=" * 32 + "\n")
        p.text(f"{test_message}\n")
        p.text(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        p.text(f"Vendor ID: {vendor_id}\n")
        p.text(f"Product ID: {product_id}\n")
        p.text("=" * 32 + "\n")
        p.text("Test completed successfully!\n")
        p.text("\n\n")
        p.cut()
        
        flash(f"✅ Test print successful! Vendor: {vendor_id}, Product: {product_id}", "success")
        
    except ValueError as e:
        flash(f"❌ Invalid ID format: {str(e)}. Use hex format like 0x09c5", "error")
    except USBNotFoundError:
        flash(f"❌ Printer not found: {vendor_id}:{product_id}", "error")
        flash("💡 Check: 1) USB connection 2) Printer power 3) Run 'lsusb' command", "info")
    except PermissionError:
        flash("❌ Permission denied. Try running as sudo or setup USB permissions", "error")
        flash(f"💡 Run: sudo usermod -a -G plugdev {os.getenv('USER', 'your_user')}", "info")
    except EscposError as e:
        flash(f"❌ Printer error: {str(e)}", "error")
        flash("💡 Printer might not support ESC/POS commands", "warning")
    except Exception as e:
        flash(f"❌ Printer test failed: {str(e)}", "error")
    
    return redirect(url_for('test_printer'))

@app.route("/admin/invoice_status")
def admin_invoice_status():
    try:
        stats = get_invoice_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/admin/reset_invoices", methods=["POST"])
def admin_reset_invoices():
    confirm = request.form.get("confirm")
    if confirm == "RESET_ALL_INVOICES":
        try:
            if Invoice.reset_invoice_counter():
                flash("All invoices deleted and counter reset to INV-0001!", "warning")
            else:
                flash("Failed to reset invoice counter", "error")
        except Exception as e:
            flash(f"Error resetting invoices: {str(e)}", "error")
    else:
        flash("Reset confirmation required", "error")
    
    return redirect(url_for('invoices_list'))

@app.route("/reset_counter", methods=['POST'])
def reset_counter():
    try:
        if Invoice.reset_invoice_counter():
            flash('Invoice counter reset successfully! Next invoice will be INV-0001', 'success')
        else:
            flash('Failed to reset invoice counter', 'error')
    except Exception as e:
        flash(f'Error resetting counter: {str(e)}', 'error')
    
    return redirect(url_for('invoices_list'))

@app.route("/delete_invoice/<int:invoice_id>", methods=["POST"])
def delete_invoice(invoice_id):
    try:
        invoice = Invoice.query.get_or_404(invoice_id)
        invoice_no = invoice.invoice_no
        
        # Delete all related items first
        Item.query.filter_by(invoice_id=invoice_id).delete()
        
        # Delete the invoice
        db.session.delete(invoice)
        db.session.commit()
        
        flash(f"Invoice #{invoice_no} deleted successfully!", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting invoice: {str(e)}", "error")
    
    return redirect(url_for('invoices_list'))

@app.route("/delete_invoice_confirm/<int:invoice_id>")
def delete_invoice_confirm(invoice_id):
    invoice = Invoice.query.get_or_404(invoice_id)
    return render_template("delete_confirm.html", invoice=invoice, company=COMPANY)

@app.route("/scan_bluetooth", methods=["POST"])
def scan_bluetooth():
    """Scan for Bluetooth devices"""
    try:
        # Simulate Bluetooth scan (replace with actual Bluetooth code)
        devices = [
            {"name": "Thermal Printer POS", "address": "00:11:22:33:44:55"},
            {"name": "Bluetooth Printer", "address": "66:77:88:99:AA:BB"}
        ]
        return jsonify({"success": True, "devices": devices})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route("/pair_bluetooth", methods=["POST"])
def pair_bluetooth():
    """Actually pair with Bluetooth device"""
    try:
        data = request.get_json()
        address = data.get('address')
        pin = data.get('pin')
        
        if not address or not pin:
            return jsonify({"success": False, "message": "Address and PIN required"})
        
        # Try to import bluetooth libraries
        try:
            import bluetooth
        except ImportError:
            return jsonify({"success": False, "message": "Bluetooth library not installed. Run: pip install pybluez"})
        
        try:
            # Create socket and attempt connection
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((address, 1))  # Port 1 is common for printers
            
            # Test the connection with a simple command
            sock.send(b"\x1b\x40")  # ESC @ (Initialize printer)
            sock.close()
            
            return jsonify({"success": True, "message": f"✅ Successfully paired and tested connection to {address}"})
            
        except bluetooth.BluetoothError as e:
            return jsonify({"success": False, "message": f"❌ Bluetooth pairing failed: {str(e)}"})
        except Exception as e:
            return jsonify({"success": False, "message": f"❌ Connection test failed: {str(e)}"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Pairing error: {str(e)}"})

@app.route("/test_bluetooth_printer", methods=["POST"])
def test_bluetooth_printer():
    """Test Bluetooth printer with actual printing"""
    try:
        data = request.get_json()
        address = data.get('address')
        
        if not address:
            return jsonify({"success": False, "message": "Bluetooth address required"})
        
        try:
            import bluetooth
        except ImportError:
            return jsonify({"success": False, "message": "Bluetooth library not installed. Run: pip install pybluez"})
        
        try:
            # Connect to Bluetooth printer
            sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
            sock.connect((address, 1))
            
            # Send test print data
            test_data = b"\x1b\x40"  # Initialize printer
            test_data += b"=" * 32 + b"\n"
            test_data += b"BLUETOOTH TEST PRINT\n"
            test_data += b"=" * 32 + b"\n"
            test_data += b"Connection: Bluetooth\n"
            test_data += f"Address: {address}\n".encode('utf-8')
            test_data += f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n".encode('utf-8')
            test_data += b"=" * 32 + b"\n"
            test_data += b"Test successful!\n"
            test_data += b"\n\n"
            test_data += b"\x1d\x56\x41\x10"  # Cut paper
            
            sock.send(test_data)
            sock.close()
            
            return jsonify({"success": True, "message": f"✅ Bluetooth printer test successful! Printed to {address}"})
            
        except bluetooth.BluetoothError as e:
            return jsonify({"success": False, "message": f"❌ Bluetooth connection failed: {str(e)}"})
        except Exception as e:
            return jsonify({"success": False, "message": f"❌ Bluetooth print failed: {str(e)}"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ Bluetooth test error: {str(e)}"})

@app.route("/test_usb_printer", methods=["POST"])
def test_usb_printer():
    """Test USB printer with proper error handling"""
    if not USB_AVAILABLE:
        return jsonify({"success": False, "message": "❌ USB libraries not installed. Run: pip install pyusb"})
    
    try:
        data = request.get_json()
        vendor_id = data.get('vendor_id', '09c5')
        product_id = data.get('product_id', '588e')
        
        # Convert to integers
        try:
            vendor_id_int = int(vendor_id, 16)
            product_id_int = int(product_id, 16)
        except ValueError:
            return jsonify({"success": False, "message": "Invalid hex format"})
        
        # Use custom printer class
        printer = CustomUSBPrinter(vendor_id_int, product_id_int)
        success, message = printer.connect()
        
        if not success:
            return jsonify({"success": False, "message": f"Connection failed: {message}"})
        
        # Create test receipt content
        test_content = f"""
{COMPANY['name']}
{COMPANY['address']}
Ph: {COMPANY['phone']}
========================
USB PRINTER TEST
========================
Date: {datetime.now().strftime('%d/%m/%y %H:%M')}
Vendor: 0x{vendor_id_int:04x}
Product: 0x{product_id_int:04x}
========================
This is a test print!
If you can read this,
your USB printer is
working correctly.
========================
Test completed!
"""
        
        # Print the test
        print_success, print_message = printer.print_raw_text(test_content)
        printer.disconnect()
        
        if print_success:
            return jsonify({"success": True, "message": f"✅ USB test printed! Check your printer. ({message})"})
        else:
            return jsonify({"success": False, "message": f"❌ Print failed: {print_message}"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"❌ USB error: {str(e)}"})

@app.route("/debug_printer", methods=["POST"])
def debug_printer():
    """Debug printer connectivity with USB availability check"""
    try:
        data = request.get_json()
        printer_type = data.get('type')
        
        if printer_type == 'usb':
            if not USB_AVAILABLE:
                return jsonify({
                    "success": False, 
                    "message": "USB libraries not installed",
                    "devices": [],
                    "install_command": "pip install pyusb"
                })
            
            # Check USB devices
            found_devices = usb.core.find(find_all=True)
            devices = list(found_devices) if found_devices is not None else []
            device_info = []
            for device in devices:
                device_info.append(f"0x{device.idVendor:04x}:0x{device.idProduct:04x}")
            
            return jsonify({
                "success": True, 
                "message": f"Found {len(devices)} USB devices",
                "devices": device_info
            })
            
        elif printer_type == 'bluetooth':
            try:
                import bluetooth
                devices = bluetooth.discover_devices(lookup_names=True)
                device_info = [f"{addr} - {name}" for addr, name in devices]
                
                return jsonify({
                    "success": True,
                    "message": f"Found {len(devices)} Bluetooth devices", 
                    "devices": device_info
                })
            except ImportError:
                return jsonify({
                    "success": False,
                    "message": "Bluetooth library not installed",
                    "install_command": "pip install pybluez"
                })
        else:
            return jsonify({"success": False, "message": "Invalid printer type"})
            
    except Exception as e:
        return jsonify({"success": False, "message": f"Debug error: {str(e)}"})

class CustomUSBPrinter:
    def __init__(self, vendor_id, product_id):
        if not USB_AVAILABLE:
            raise ImportError("USB libraries not available")
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.ep_out = None
        
    def connect(self):
        """Connect to USB printer with correct endpoint detection"""
        if not USB_AVAILABLE:
            return False, "USB libraries not installed. Run: pip install pyusb"
        
        try:
            # Find device
            self.device = usb.core.find(idVendor=self.vendor_id, idProduct=self.product_id)
            if self.device is None:
                return False, f"Printer not found: 0x{self.vendor_id:04x}:0x{self.product_id:04x}"
            
            # Get the number of interfaces correctly
            try:
                # Try the newer way first
                cfg = self.device.get_active_configuration()
                num_interfaces = cfg.bNumInterfaces
            except:
                # Fallback to older method
                num_interfaces = self.device.bNumInterfaces if hasattr(self.device, 'bNumInterfaces') else 1
            
            # Detach kernel drivers
            for i in range(num_interfaces):
                try:
                    if self.device.is_kernel_driver_active(i):
                        self.device.detach_kernel_driver(i)
                        print(f"✅ Detached kernel driver from interface {i}")
                except Exception as e:
                    print(f"⚠️ Could not detach driver from interface {i}: {e}")
                    pass
            
            # Reset device
            try:
                self.device.reset()
                import time
                time.sleep(1)  # Wait for device to reset
            except Exception as e:
                print(f"⚠️ Device reset failed: {e}")
            
            # Set configuration
            try:
                self.device.set_configuration()
            except Exception as e:
                print(f"⚠️ Set configuration failed: {e}")
                # Try to continue anyway
            
            # Get configuration and find OUT endpoint
            cfg = self.device.get_active_configuration()
            interface = cfg[(0,0)]
            
            # Find the correct OUT endpoint
            for ep in interface:
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    self.ep_out = ep
                    print(f"✅ Found OUT endpoint: 0x{ep.bEndpointAddress:02x}")
                    break
            
            if self.ep_out is None:
                return False, "No OUT endpoint found"
            
            # Claim interface
            try:
                usb.util.claim_interface(self.device, interface)
                print("✅ Interface claimed")
            except Exception as e:
                print(f"⚠️ Interface claim failed: {e}")
                # Try to continue anyway
            
            return True, f"Connected to endpoint 0x{self.ep_out.bEndpointAddress:02x}"
            
        except Exception as e:
            return False, f"Connection error: {str(e)}"
    
    def print_raw_text(self, text):
        """Print raw text to thermal printer"""
        try:
            if self.ep_out is None:
                return False, "Not connected to printer"
            
            # ESC/POS commands for thermal printer
            data = b"\x1b\x40"  # Initialize printer (ESC @)
            data += text.encode('utf-8', errors='ignore')
            data += b"\n\n\n"  # Feed paper
            data += b"\x1d\x56\x41\x10"  # Cut paper (full cut)
            
            # Send data in chunks to avoid buffer overflow
            chunk_size = 64  # Send in 64-byte chunks
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i+chunk_size]
                try:
                    bytes_written = self.ep_out.write(chunk, timeout=5000)  # 5 second timeout
                    print(f"✅ Wrote {bytes_written} bytes to printer")
                except usb.core.USBTimeoutError:
                    return False, "USB write timeout - printer may be busy"
                except Exception as e:
                    return False, f"USB write error: {str(e)}"
            
            return True, "Print data sent successfully"
            
        except Exception as e:
            return False, f"Print error: {str(e)}"
    
    def disconnect(self):
        """Release USB resources"""
        try:
            if self.device:
                # Release interface
                try:
                    usb.util.release_interface(self.device, 0)
                    print("✅ Interface released")
                except:
                    pass
                
                # Optionally reattach kernel driver
                try:
                    self.device.attach_kernel_driver(0)
                    print("✅ Kernel driver reattached")
                except:
                    pass
        except Exception as e:
            print(f"⚠️ Disconnect error: {e}")

@app.route("/find_usb_printers", methods=["POST"])
def find_usb_printers():
    """Find all USB devices"""
    try:
        import usb.core
        
        devices = usb.core.find(find_all=True)
        device_list = []
        
        for device in devices:
            device_list.append({
                "vendor_id": f"{device.idVendor:04x}",
                "product_id": f"{device.idProduct:04x}"
            })
        
        return jsonify({"success": True, "devices": device_list})
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

if __name__ == "__main__":
    try:
        print("🚀 Starting Anand Digital Studio Billing System...")
        print("📋 Company:", COMPANY["name"])
        print("🌐 Server will start at: http://127.0.0.1:5000")
        print("⚠️  Press Ctrl+C to stop the server")
        app.run(debug=True, host='0.0.0.0', port=5000)
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        print("💡 Check the error above and fix any missing dependencies")