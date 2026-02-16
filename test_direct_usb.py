#!/usr/bin/env python3
import usb.core
import usb.util

def test_direct_print():
    # Your printer IDs
    vendor_id = 0x09c5
    product_id = 0x588e
    
    try:
        print("🔍 Looking for USB printer...")
        device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        
        if device is None:
            print("❌ Printer not found. Check IDs with 'lsusb'")
            return
        
        print(f"✅ Found printer: {vendor_id:04x}:{product_id:04x}")
        
        # Detach kernel drivers
        for i in range(device.bNumInterfaces):
            if device.is_kernel_driver_active(i):
                try:
                    device.detach_kernel_driver(i)
                    print(f"✅ Detached kernel driver from interface {i}")
                except:
                    pass
        
        # Set configuration
        device.set_configuration()
        cfg = device.get_active_configuration()
        interface = cfg[(0,0)]
        
        # Find OUT endpoint
        ep_out = None
        for ep in interface:
            if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                ep_out = ep
                print(f"✅ Found OUT endpoint: 0x{ep.bEndpointAddress:02x}")
                break
        
        if ep_out is None:
            print("❌ No OUT endpoint found")
            return
        
        # Claim interface
        usb.util.claim_interface(device, interface)
        print("✅ Interface claimed")
        
        # Send test print
        test_data = b"\x1b\x40"  # Initialize printer
        test_data += b"DIRECT USB TEST\n"
        test_data += b"If you see this printed,\n"
        test_data += b"your USB printer works!\n"
        test_data += b"\n\n\n"
        test_data += b"\x1d\x56\x41\x10"  # Cut paper
        
        ep_out.write(test_data)
        print("✅ Test data sent to printer!")
        print("🖨️ Check your printer for output")
        
        # Release interface
        usb.util.release_interface(device, interface)
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_direct_print()