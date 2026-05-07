def ble_translate_services(uuid):
	return __SERVICES.get(uuid,None)

def ble_translate_characteristics(uuid):
	return __CHARACTERISTICS.get(uuid,None)


__SERVICES = {
	0x1800 : {"name" : "Generic Access"},
	0x1801 : {"name" : "Generic Attribute"},
	0x1809 : {"name" : "Health Thermometer"},
	0x180a : {"name" : "Device Information"},
	0x180f : {"name" : "Battery Service"},
	0x1810 : {"name" : "Blood Pressure"},
	0x181d : {"name" : "Weight Scale"}
}

__CHARACTERISTICS = {
	0x2a00 : {"name" : "Device Name"},
	0x2a01 : {"name" : "Appearance"},
	0x2a19 : {"name" : "Battery Level"},
	0x2a1c : {"name" : "Temperature Measurement"},
	0x2a1d : {"name" : "Temperature Type"},
	0x2a24 : {"name" : "Model Number String"},
	0x2a25 : {"name" : "Serial Number String"},
	0x2a29 : {"name" : "Manufacturer Name String"},
	0x2a35 : {"name" : "Blood Pressure Measurement"},
	0x2a9d : {"name" : "Weight Measurement"},
	0x2a9e : {"name" : "Weight Scale Feature"}
}