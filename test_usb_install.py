#!/usr/bin/env python3

def test_usb_installation():
    print("🧪 Testing USB library installation...")
    
    try:
        import usb.core
        print("✅ usb.core imported successfully")
        
        import usb.util
        print("✅ usb.util imported successfully")
        
        # Try to find devices
        devices = list(usb.core.find(find_all=True))
        print(f"✅ Found {len(devices)} USB devices")
        
        if devices:
            print("📱 USB devices found:")
            for i, device in enumerate(devices[:10]):  # Show first 10
                print(f"  {i+1}. 0x{device.idVendor:04x}:0x{device.idProduct:04x}")
                
                # Check if this might be your printer
                if device.idVendor == 0x09c5 and device.idProduct == 0x588e:
                    print(f"    ✅ This matches your printer!")
                    
                    # Test endpoint detection
                    try:
                        cfg = device.get_active_configuration()
                        print(f"    Configuration: {cfg.bConfigurationValue}")
                        print(f"    Interfaces: {cfg.bNumInterfaces}")
                        
                        interface = cfg[(0,0)]
                        print(f"    Interface 0 endpoints:")
                        for ep in interface:
                            direction = "OUT" if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT else "IN"
                            print(f"      - 0x{ep.bEndpointAddress:02x} ({direction})")
                            
                    except Exception as e:
                        print(f"    ⚠️ Could not read device details: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ USB library import failed: {e}")
        print("💡 Install with: pip install pyusb")
        print("💡 On Ubuntu: sudo apt-get install libusb-1.0-0-dev")
        return False
    except Exception as e:
        print(f"❌ USB test failed: {e}")
        return False

def test_direct_print():
    """Test direct printing to your specific printer"""
    print("\n🖨️ Testing direct print to your printer...")
    
    try:
        import usb.core
        import usb.util
        
        # Your printer IDs
        vendor_id = 0x09c5
        product_id = 0x588e
        
        device = usb.core.find(idVendor=vendor_id, idProduct=product_id)
        if device is None:
            print(f"❌ Your printer (0x{vendor_id:04x}:0x{product_id:04x}) not found")
            return False
        
        print(f"✅ Found your printer: 0x{vendor_id:04x}:0x{product_id:04x}")
        
        # Test endpoint access
        try:
            cfg = device.get_active_configuration()
            interface = cfg[(0,0)]
            
            ep_out = None
            for ep in interface:
                if usb.util.endpoint_direction(ep.bEndpointAddress) == usb.util.ENDPOINT_OUT:
                    ep_out = ep
                    print(f"✅ Found OUT endpoint: 0x{ep.bEndpointAddress:02x}")
                    break
            
            if ep_out:
                print("✅ Your printer is ready for direct USB printing!")
                return True
            else:
                print("❌ No OUT endpoint found")
                return False
                
        except Exception as e:
            print(f"❌ Endpoint test failed: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Direct print test failed: {e}")
        return False

if __name__ == "__main__":
    if test_usb_installation():
        print("✅ USB libraries are working correctly!")
        test_direct_print()
    else:
        print("❌ USB libraries need to be installed")