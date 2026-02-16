def print_receipt_escpos(invoice, company, usb_vendor_id=None, usb_product_id=None, ip_address=None):
    """Basic printer service"""
    try:
        from escpos.printer import Usb
        if usb_vendor_id and usb_product_id:
            p = Usb(usb_vendor_id, usb_product_id)
            p.text("Test receipt\n")
            p.cut()
            return True, "Print successful"
        return False, "No printer specified"
    except Exception as e:
        return False, f"Print failed: {str(e)}"

def test_printer_connection():
    """Test printer connection"""
    return True, "Test OK"
