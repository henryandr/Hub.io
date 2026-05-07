import math

RESERVED_FLOAT_VALUES = ['INFINITY', 'NaN', 'NRes', 'RESERVED', '-INFINITY']

FLOAT_POSITIVE_INFINITY = 0x007FFFFE
FLOAT_NaN = 0x007FFFFF
FLOAT_NRes = 0x00800000
FLOAT_RESERVED = 0x00800001
FLOAT_NEGATIVE_INFINITY = 0x00800002

SFLOAT_POSITIVE_INFINITY = 0x07FE,
SFLOAT_NaN = 0x07FF,
SFLOAT_NRes = 0x0800,
SFLOAT_RESERVED_VALUE = 0x0801,
SFLOAT_NEGATIVE_INFINITY = 0x0802

def ble_translate_services(uuid):
	return __SERVICES.get(uuid,None)

def ble_translate_characteristics(uuid):
	return __CHARACTERISTICS.get(uuid,None)


__SERVICES = {
	0x1800 : {'name' : 'Generic Access'},
	0x1801 : {'name' : 'Generic Attribute'},
	0x1809 : {'name' : 'Health Thermometer'},
	0x180a : {'name' : 'Device Information'},
	0x180f : {'name' : 'Battery Service'},
	0x1810 : {'name' : 'Blood Pressure'},
	0x181d : {'name' : 'Weight Scale'}
}

__CHARACTERISTICS = {
	0x2a00 : {'name' : 'Device Name'},
	0x2a01 : {'name' : 'Appearance'},
	0x2a19 : {'name' : 'Battery Level'},
	0x2a1c : {'name' : 'Temperature Measurement'},
	0x2a1d : {'name' : 'Temperature Type'},
	0x2a24 : {'name' : 'Model Number String'},
	0x2a25 : {'name' : 'Serial Number String'},
	0x2a29 : {'name' : 'Manufacturer Name String'},
	0x2a35 : {'name' : 'Blood Pressure Measurement'},
	0x2a9d : {'name' : 'Weight Measurement'},
	0x2a9e : {'name' : 'Weight Scale Feature'}
}

# Data translation

def trl_data(data_array):
    data_trl = []
    for data in data_array:
        data_raw = [{}]
        if(data['name'] == 'Device Name'):
            data_raw[0] = data
        elif(data['name'] == 'Appearance'):
            data_raw[0]['name'] = data['name']
            data_raw[0]['data'] = appearance(str_to_int(data['data']))
        elif(data['name'] == 'Temperature Measurement'):
            data_raw[0]['name'] = data['name']
            value = str_to_int(data['data'][1:5])
            data_raw[0]['data'] = float_ieee_11073(value)
            data_raw[0]['units'] = temp_units(str_to_int(data['data'][0]))
        elif(data['name'] == 'Temperature Type'):
            data_raw[0]['name'] = data['name']
            data_raw[0]['data'] = temp_type(str_to_int(data['data']))
        elif(data['name'] == 'Blood Pressure Measurement'):
            flags = str_to_int(data['data'][0])
            measurement_present = flags & 0x10
            if(measurement_present):
                meassurements = []
                sys_data = {}
                dia_data = {}
                mean_data = {}
                units = blood_pressure_units(flags)
                PR_present = flags & 0x4
                if(PR_present):
                    PR_data = {}
                    PR_data['name'] = data['name']
                    PR_data['var'] = 'Pulse Rate'
                    PR_data['units'] = 'bpm'
                    PR_data['data'] = sfloat_ieee_11073(str_to_int(data['data'][7:9]))
                    meassurements.append(PR_data)

                sys_data['name'] = data['name']
                sys_data['var'] = 'Systolic'
                sys_data['units'] = units
                sys_data['data'] = sfloat_ieee_11073(str_to_int(data['data'][1:3]))
                meassurements.append(sys_data)
                dia_data['name'] = data['name']
                dia_data['var'] = 'Diastolic'
                dia_data['units'] = units
                dia_data['data'] = sfloat_ieee_11073(str_to_int(data['data'][3:5]))
                meassurements.append(dia_data)
                mean_data['name'] = data['name']
                mean_data['var'] = 'Mean Pressure'
                mean_data['units'] = units
                mean_data['data'] = sfloat_ieee_11073(str_to_int(data['data'][5:7]))
                meassurements.append(mean_data)

                data_raw = meassurements
        elif(data['name'] == 'Manufacturer Name String'):
            data_raw[0] = data
        elif(data['name'] == 'Model Number String'):
            data_raw[0] = data
        elif(data['name'] == 'Serial Number String'):
            data_raw[0] = data
        elif(data['name'] == 'Battery Level'):
            data_raw[0]['name'] = data['name']
            data_raw[0]['data'] = ord(data['data'])

        print(data_raw)
        data_trl.extend(data_raw)
    
    return data_trl


def str_to_int(val):
    val_int = 0
    shift_val = len(val) - 1
    for x in val[::-1]:
        val_int += (ord(x) << (8 * (shift_val)))
        shift_val -= 1
    
    return val_int

def appearance(key):
    __APPEARANCE = {
        0 : 'Unknown'
    }

    return __APPEARANCE.get(key)

def temp_units(flags):
    __TEMP_UNITS = {
        0 : 'C',
        1 : 'F'
    }

    flags = flags & 0x1

    return __TEMP_UNITS.get(flags,'Unknown')

def temp_type(val):
    __TEMP_TYPE = {
        1 : 'Armpit',
        2 : 'Body',
        3 : 'Ear',
        4 : 'Finger',
        5 : 'Gastro-intestinal Tract',
        6 : 'Mouth',
        7 : 'Rectum',
        8 : 'Toe',
        9 : 'Tympanum'
    }

    return __TEMP_TYPE.get(val,'Unknown')

def blood_pressure_units(flag):
    __TEMP_UNITS = {
        0 : 'mmHg',
        1 : 'kPa'
    }

    flag = flag & 0x1

    return __TEMP_UNITS.get(flag,'Unknown')

def float_ieee_11073(val):    
    mantissa = val & 0xFFFFFF;
    exponent = val >> 24

    if(mantissa >= FLOAT_POSITIVE_INFINITY and mantissa <= FLOAT_NEGATIVE_INFINITY):
        output = reserved_float_values[mantissa - FLOAT_POSITIVE_INFINITY]
    else:
        if(mantissa >= 0x800000):
            mantissa = -((mantissa ^ 0xFFFFFF) + 1)

        if(exponent >= 0x80):
            exponent = -((exponent ^ 0xFF) + 1)

        output = mantissa * math.pow(10,exponent)

    return output

def sfloat_ieee_11073(val):    
    mantissa = val & 0xFFF;
    exponent = val >> 12

    if(mantissa >= SFLOAT_POSITIVE_INFINITY and mantissa <= SFLOAT_NEGATIVE_INFINITY):
        output = reserved_float_values[mantissa - SFLOAT_POSITIVE_INFINITY]
    else:
        if(mantissa >= 0x800):
            mantissa = -((mantissa ^ 0xFFF) + 1)

        if(exponent >= 0x8):
            exponent = -((exponent ^ 0xF) + 1)

        output = mantissa * math.pow(10,exponent)

    return output