from escpos.printer import Usb, Network, Dummy
import os
from datetime import datetime

def print_receipt_escpos(invoice, company, usb_vendor_id=None, usb_product_id=None, ip_address=None):
    """
    Print thermal receipt using ESC/POS commands with test mode messages.
    """
    try:
        # Choose printer connection method
        if usb_vendor_id and usb_product_id:
            print(f"Connecting to USB printer: {hex(usb_vendor_id)}:{hex(usb_product_id)}")
            p = Usb(usb_vendor_id, usb_product_id, timeout=0, in_ep=0x82, out_ep=0x01)
            connection_type = "USB"
        elif ip_address:
            print(f"Connecting to network printer: {ip_address}")
            p = Network(ip_address, port=9100, timeout=60)
            connection_type = "Network"
        else:
            print("Using test mode (no actual printing)")
            p = Dummy()  # Test mode
            connection_type = "Test"
        
        # Initialize printer
        p.open()
        
        # Header with company info
        p.set(align='center', font='a', bold=True, double_width=True)
        p.text(f"{company.get('name', 'Anand Digital Studio')}\n")
        
        # Add logo space indicator in test mode
        if connection_type == "Test":
            p.set(align='center', font='b', bold=False)
            p.text("[LOGO POSITION - CENTER]\n")
        
        p.set(align='center', font='b', bold=False, double_width=False)
        address_lines = company.get('address', '').split('\n')
        for line in address_lines:
            if line.strip():
                p.text(f"{line.strip()}\n")
        
        p.text(f"Phone: {company.get('phone', '')}\n")
        p.text("=" * 32 + "\n")
        
        # Invoice details
        p.set(align='left', font='a')
        p.text(f"Invoice: #{invoice.invoice_no}\n")
        p.text(f"Date: {invoice.date.strftime('%d/%m/%Y %H:%M')}\n")
        p.text(f"Customer: {invoice.customer_name}\n")
        if invoice.customer_phone:
            p.text(f"Phone: {invoice.customer_phone}\n")
        p.text("=" * 32 + "\n")
        
        # Items
        for item in invoice.items:
            desc = item.description[:25]
            qty = item.quantity
            rate = float(item.rate)
            line_total = item.line_total
            
            # Item name
            p.text(f"{desc}\n")
            # Quantity, rate, and total
            p.text(f"  {qty} x Rs.{rate:.2f} = Rs.{line_total:.2f}\n")
        
        p.text("-" * 32 + "\n")
        
        # Totals
        p.set(align='right', font='a')
        p.text(f"Subtotal: Rs.{invoice.subtotal:.2f}\n")
        if invoice.tax_amount > 0:
            p.text(f"Tax: Rs.{invoice.tax_amount:.2f}\n")
        
        p.set(align='center', font='a', bold=True, double_width=True)
        p.text(f"TOTAL: Rs.{invoice.grand_total:.2f}\n")
        
        # Footer
        p.set(align='center', font='b', bold=False, double_width=False)
        p.text("=" * 32 + "\n")
        
        if invoice.notes:
            p.text(f"Notes: {invoice.notes[:50]}\n")
            p.text("-" * 32 + "\n")
        
        p.text("Thank you for your business!\n")
        p.text("Visit us again!\n")
        p.text(f"Printed: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n")
        
        # Test mode messages
        if connection_type == "Test":
            p.text("\n")
            p.text("*** TEST MODE ***\n")
            p.text("No actual printing performed\n")
            p.text("Receipt preview only\n")
        
        p.text("\n\n")
        p.cut()
        p.close()
        
        # Return appropriate message based on connection type
        if connection_type == "Test":
            return True, "✅ Test mode: Receipt preview generated successfully! No actual printing performed."
        elif connection_type == "USB":
            return True, f"✅ Receipt printed successfully via USB printer!"
        else:
            return True, f"✅ Receipt printed successfully via network printer ({ip_address})!"
        
    except Exception as e:
        error_msg = str(e)
        print(f"Printing error: {error_msg}")
        
        if "No such device" in error_msg:
            return False, "❌ USB printer not found. Check connection and device IDs."
        elif "Permission denied" in error_msg:
            return False, "❌ Permission denied. Try running as administrator."
        elif "Connection refused" in error_msg:
            return False, "❌ Network connection failed. Check IP address."
        else:
            return False, f"❌ Print error: {error_msg}"

def test_printer_connection(usb_vendor_id=None, usb_product_id=None, ip_address=None):
    """Test printer connection with detailed messages"""
    try:
        if usb_vendor_id and usb_product_id:
            p = Usb(usb_vendor_id, usb_product_id, timeout=5)
            connection_type = f"USB ({hex(usb_vendor_id)}:{hex(usb_product_id)})"
        elif ip_address:
            p = Network(ip_address, timeout=10)
            connection_type = f"Network ({ip_address})"
        else:
            return True, "✅ Test mode connection successful - No actual printer required"
        
        p.open()
        p.close()
        return True, f"✅ {connection_type} printer connection successful!"
        
    except Exception as e:
        if usb_vendor_id and usb_product_id:
            return False, f"❌ USB connection failed: {str(e)}"
        elif ip_address:
            return False, f"❌ Network connection failed: {str(e)}"
        else:
            return False, f"❌ Connection test failed: {str(e)}"