import hid

print("Listing all HID devices...")
devices = hid.enumerate()
for d in devices:
    mfg = d.get('manufacturer_string', '') or ''
    prod = d.get('product_string', '') or ''
    
   
    print(f"VID: {d['vendor_id']:04x} | PID: {d['product_id']:04x} | {mfg} - {prod} | Usage Page: {d.get('usage_page', 0):04x} | Usage: {d.get('usage', 0):04x} | Path: {d['path']}")
