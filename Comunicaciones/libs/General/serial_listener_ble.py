import sys, os, time

# add paths for libraries
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/Bgapi")

file_path = os.path.dirname(os.path.realpath(__file__))
lib_path =  file_path[0:file_path.rindex('/')] + "/Translate"

sys.path.append(lib_path)

from api import BlueGigaAPI
from api import BlueGigaCallbacks
import cmd_def
import BLE_trl

import log as logger
import threading, json, socket

state = "WAITING"
nearby_devices = []
new_devices_data = False
known_device = None
pairing = False
connecting = False
disconnecting = False
server_gatt = []
discovering_services = False
services_discover_completed = False
discovering_characteristics = False
characteristics_discover_completed = False
actual_service_index = 0
actual_characteristics_index = 0
getting_data = False
data_read = []

class BleSerial(object):

	com_type = None 
	port = None
	baud = None
	com_log = None
	q = None
	CB_BLE = None
	tcp_gui = None
	t = None
	BlueGigaAPI_instance = None
	addr_connected = None
	scanning = False # start once the scan (discover)
	ble_initiated = False

	def __init__(self,uart_conf,log_conf,q):

		self.com_log = logger.set_log(__name__,log_conf[0],log_conf[1])
		self.com_type = uart_conf['type']
		self.port = uart_conf['uart']
		self.baud = uart_conf['baudrate']
		self.q = q

		self.CB_BLE = BleCallbacks(log_conf) # instance of BleCallbacks
		self.tcp_gui = SenderTCP(log_conf) # instance of TCP for GUI communication

		self.BlueGigaAPI_instance = BlueGigaAPI(self.port,self.CB_BLE,self.baud) # instance of BlueGigaAPI

		self.BlueGigaAPI_instance.start_daemon()
		self.com_log.info("Interface %s on port %s ready to use" % (self.com_type,self.port))

		self.t = threading.Thread(target=self.__com_fsm) # threading instance
		self.t.daemon = True
		self.t.start()

	def init_BLE(self):
		global state
		# Disconnect, stop advertising and stop self.scanning
		self.BlueGigaAPI_instance.ble_cmd_connection_disconnect(0)

		self.BlueGigaAPI_instance.ble_cmd_gap_set_mode(0,0)

		self.BlueGigaAPI_instance.ble_cmd_gap_end_procedure()

		self.BlueGigaAPI_instance.ble_cmd_gap_set_scan_parameters(0x320,0x320,1) # Active mode

		self.BlueGigaAPI_instance.ble_cmd_sm_set_bondable_mode(1) # Set bondable mode (Pairing)

		self.BlueGigaAPI_instance.ble_cmd_sm_set_parameters(0,7,3) # Set local security manager

	def __com_fsm(self):
		while 1:
			global state, nearby_devices, new_devices_data, known_device, pairing, connecting
			global disconnecting, server_gatt, discovering_services, services_discover_completed
			global discovering_characteristics, actual_service_index, characteristics_discover_completed
			global actual_characteristics_index, getting_data, data_read

			if(state == "WAITING"):
				if(not self.ble_initiated):
					self.init_BLE()

					# self.clear_bonding(0xff) # delete all bondings
					
					self.ble_initiated = True
			elif(state == "DISCOVER"):
				if(not self.scanning):
					self.BlueGigaAPI_instance.ble_cmd_gap_discover(2) # Start scaning in observation Mode
					self.scanning = True
			elif(state == "DISCOVERING"):
				if(nearby_devices and new_devices_data):
					for device in nearby_devices:
						if(device['bond'] != 0xff): # If bond is different to 0xff is an unknown device
							known_device = device
							break

					if(not known_device):
						# See if this device was already sent
						for i in range(len(nearby_devices)):
							if(not nearby_devices[i]['sent']):
								self.tcp_gui.send(json.dumps(nearby_devices[i]))
								nearby_devices[i]['sent'] = True

						self.addr_connected = self.tcp_gui.recv()

						if(self.addr_connected):
							self.BlueGigaAPI_instance.ble_cmd_gap_end_procedure()
							self.com_log.info("Pairing with %s" % self.addr_connected)
							self.addr_connected = ''.join([chr(int(a,16)) for a in self.addr_connected.split(":")])
							self.addr_connected = self.addr_connected[::-1]
							self.scanning = False
							state = "PAIRING"
							self.com_log.debug("FSM actual state: %s" % state)
					else:
						self.com_log.debug("Found a known device!")
						self.BlueGigaAPI_instance.ble_cmd_gap_end_procedure()
						state = "CONNECTING"
						self.com_log.debug("FSM actual state: %s" % state)
			elif(state == "PAIRING"):
				if(not pairing):
					self.BlueGigaAPI_instance.ble_cmd_gap_connect_direct(self.addr_connected,0,60,76,100,0)
					pairing = True
			elif(state == "PAIRED"):
				addr = self.addr_connected[::-1]
				addr = ":".join(["%02X" % ord(a) for a in addr])
				self.com_log.info("Pairing success with device %s" % addr)
				self.tcp_gui.send(json.dumps({'type':'paired'}))
				state = "DISCONNECTING"
				self.com_log.debug("FSM actual state: %s" % state)
			elif(state == "CONNECTING"):
				if(not connecting):
					addr = ''.join([chr(int(a,16)) for a in known_device["addr"].split(":")])
					addr = addr[::-1]
					self.BlueGigaAPI_instance.ble_cmd_gap_connect_direct(addr,0,60,76,100,0)
					connecting = True
			elif(state == "CONNECTED"): # search for services
				if(not discovering_services):
					self.addr_connected = known_device["addr"]
					self.BlueGigaAPI_instance.ble_cmd_attclient_read_by_group_type(0,1,65535,chr(0) + chr(0x28)) # look for all services
					discovering_services = True
				else:
					if(services_discover_completed):
						self.com_log.debug("All GATT services were read")						
						state = "READ"
			elif(state == "READ"):
				if(not discovering_characteristics):
					self.BlueGigaAPI_instance.ble_cmd_attclient_read_by_type(0,server_gatt[actual_service_index]["start"],server_gatt[actual_service_index]["end"],chr(0x3) + chr(0x28))
					discovering_characteristics = True
				else:
					if(characteristics_discover_completed):
						self.com_log.debug("All GATT characteristics were read")
						print(server_gatt)
						state = "DATA"
			elif(state == "DATA"):
				if(not getting_data):
					if((len(server_gatt)) != actual_service_index):
						if((len(server_gatt[actual_service_index]['characteristics']) != 0) and (len(server_gatt[actual_service_index]['characteristics']) != actual_characteristics_index)):
							if(server_gatt[actual_service_index]['characteristics'][actual_characteristics_index]['indicate']):
								# The hdl correspond to 0x2803. Need the hdl from the 0x2902, which is two above
								self.BlueGigaAPI_instance.ble_cmd_attclient_attribute_write(0,server_gatt[actual_service_index]['characteristics'][actual_characteristics_index]['hdl'] + 2,chr(2) + chr(0)) # Write 2 for indicate
							elif(server_gatt[actual_service_index]['characteristics'][actual_characteristics_index]['read']):
								# The hdl correspond to 0x2803. Need the hdl from the UUID, which is the next one
								self.BlueGigaAPI_instance.ble_cmd_attclient_read_by_handle(0,server_gatt[actual_service_index]['characteristics'][actual_characteristics_index]['hdl'] + 1)
							else:
								self.com_log.debug("No action with characteristic")

							actual_characteristics_index += 1
							getting_data = True
						else:
							self.com_log.debug('All %s characteristics read' % server_gatt[actual_service_index]['name'])
							actual_characteristics_index = 0
							actual_service_index += 1
					else:
						self.com_log.info('All services read')
						# print(data_read)
						data_trl = BLE_trl.trl_data(data_read)
						# print(data_trl)
						self.tcp_gui.send(json.dumps({'type':'data','data':data_trl}))
						self.q.put(data_trl)
						state = "DISCONNECTING"
			elif(state == "DISCONNECTING"):
				if(not disconnecting):
					time.sleep(1)
					self.BlueGigaAPI_instance.ble_cmd_connection_disconnect(0)
					disconnecting = True
			elif(state == "DISCONNECTED"):
				addr = self.addr_connected[::-1]
				addr = ":".join(["%02X" % ord(a) for a in addr])
				self.com_log.debug('Device %s disconnected' % addr)
				nearby_devices = []
				new_devices_data = False
				known_device = None
				pairing = False
				connecting = False
				disconnecting = False
				self.addr_connected = None
				self.scanning = False
				self.ble_initiated = False
				state = "WAITING"
				server_gatt = []
				discovering_services = False
				services_discover_completed = False
				discovering_characteristics = False
				characteristics_discover_completed = False
				actual_service_index = 0
				actual_characteristics_index = 0
				getting_data = False
				data_read = []
				self.com_log.debug("FSM actual state: %s" % state)
			else:
				self.com_log.warn("Bad state")

	def clear_bonding(self,handle):
		self.BlueGigaAPI_instance.ble_cmd_sm_delete_bonding(handle)

	def close_serial(self):
		self.BlueGigaAPI_instance.close_serial()
		self.com_log.debug("Interface %s on port %s closed" % (self.com_type,self.port))

class BleCallbacks(BlueGigaCallbacks):

	com_log = None
	cmd_def = None

	def __init__(self,log_conf):
		BlueGigaCallbacks.__init__(self)
		self.cmd_def_bgapi = cmd_def.ReturnCodeLookupDict(cmd_def.RESULT_CODE)
		self.com_log = logger.set_log(__name__ + "_RSP",log_conf[0],log_conf[1])

	def ble_rsp_connection_disconnect(self,connection, result):
		if(result == 0x0):
			self.com_log.debug("BLE disconnect cmd for connection 0x%02X success: %s" % (connection,self.cmd_def_bgapi.get(result)))
		else:
			self.com_log.debug("BLE disconnect cmd for connection 0x%02X error: %s" % (connection,self.cmd_def_bgapi.get(result)))

	def ble_evt_connection_disconnected(self,connection,reason):
		global state
		self.com_log.debug("BLE disconnected handler %s Reason: %s" % (connection,self.cmd_def_bgapi.get(reason)))
		state = "DISCONNECTED"
		self.com_log.debug("FSM actual state: %s" % state)

	def ble_rsp_gap_end_procedure(self,result):
		self.com_log.debug("BLE stop discover procedure success: %s" % self.cmd_def_bgapi.get(result))


	def ble_rsp_gap_set_mode(self,result):
		if(result == 0x0):
			self.com_log.debug("BLE gap_set success: %s" % self.cmd_def_bgapi.get(result))
		else:
			self.com_log.debug("BLE gap_set error: %s " % self.cmd_def_bgapi.get(result))

	def ble_rsp_gap_set_scan_parameters(self,result):
		if(result == 0x0):
			self.com_log.debug("BLE scan_set success: %s" % self.cmd_def_bgapi.get(result))
		else:
			self.com_log.debug("BLE scan_set error: %s" % self.cmd_def_bgapi.get(result))

	def ble_rsp_sm_set_bondable_mode(self):
		self.com_log.debug("BLE bondable_set success")

	def ble_rsp_sm_set_parameters(self):
		global state
		self.com_log.debug("BLE SM_parameters_set success")
		state = "DISCOVER"
		self.com_log.debug("FSM actual state: %s" % state)

	def ble_rsp_gap_discover(self,result):
		global state
		if(result == 0x0):
			self.com_log.debug("BLE scan_start success: %s" % self.cmd_def_bgapi.get(result))
			state = "DISCOVERING" # Discover state success, waiting for devices discovered
			self.com_log.debug("FSM actual state: %s" % state)
		else:
			self.com_log.debug("BLE scan_start error: %s" % self.cmd_def_bgapi.get(result))

	def ble_evt_gap_scan_response(self,rssi,packet_type,sender,address_type,bond,data):
		data_len = len(data)
		i = 0
		while data_len != 0:
			adv_pkt_len = ord(data[i])
			self.__store_adv_data(data[i+1],data[i+2:i+adv_pkt_len+1],rssi,sender[::-1],bond)
			i += adv_pkt_len + 1
			data_len -= (adv_pkt_len + 1)

	def __store_adv_data(self,data_type,data,rssi,sender,bond):
		global nearby_devices, new_devices_data
		exists = False

		for i in range(len(nearby_devices)):
			if(nearby_devices[i]['addr'] == ":".join(["%02X" % ord(a) for a in sender])):
				exists = True
				break

		if(not exists):
			json_data = {}
			translated = self.__translate_adv_data(data_type,data)
			if(translated):
				json_data['addr'] = ":".join(["%02X" % ord(a) for a in sender])
				json_data['rssi'] = rssi
				json_data['bond'] = bond
				json_data['sent'] = False
				json_data['name'] = ''
				json_data['type'] = 'new_device'
				json_data[translated[0]] = translated[1]
				nearby_devices.append(json_data)
				# new_devices_data = True
		else:
			translated = self.__translate_adv_data(data_type,data)
			if(translated):
				nearby_devices[i][translated[0]] = translated[1]
				nearby_devices[i]['rssi'] = rssi
				self.com_log.debug(json.dumps(nearby_devices))
				if(nearby_devices[i]['name']):
					new_devices_data = True

	def __translate_adv_data(self,data_type,data):
		msg = []
		data_type = ord(data_type)
		if(data_type == 0x1): # Flags
			self.com_log.debug("Flags adv packet")
		elif(data_type == 0x2 or data_type == 0x3): # partial or complete list of 16-bit UUIDs
			msg.extend(["uuid16",data[::-1]])
			self.com_log.debug(msg[0] + " 0x" + "".join(["%02X" % ord(a) for a in data[::-1]]) + " found")
		elif(data_type == 0x4 or data_type == 0x5): # partial or complete list of 32-bit UUIDs
			self.com_log.debug("32-bit UUID custom service not supported")
		elif(data_type == 0x6 or data_type == 0x7): # partial or complete list of 128-bit UUIDs
			self.com_log.debug("128-bit UUID custom service not supported")
		elif(data_type == 0x8 or data_type == 0x9): # shortened or complete local name
			msg.extend(["name","".join([a for a in data])])
			self.com_log.debug("Device " + "".join([a for a in data]) +" found")
		elif(data_type == 0xff):
			pass
		else:
			self.com_log.debug("Adv packet type 0x%02X not supported" % data_type)

		return msg

	def ble_rsp_gap_connect_direct(self,result,connection_handle):
		# global state
		if(result == 0x0):
			self.com_log.debug("BLE connect_direct success: %s handle: 0x%02X" % (self.cmd_def_bgapi.get(result),connection_handle))
			# state = "CONNECTED"
		else:
			self.com_log.debug("BLE connect_direct error: %s" % self.cmd_def_bgapi.get(result))

	def ble_evt_connection_status(self,connection,flags,address,address_type,conn_interval,timeout,latency,bonding):
		global state
		self.com_log.debug("BLE connection_status: %02X %02X" % (flags,bonding))
		if(flags == 0x5 and bonding != 0xff): # Flags 0x05 is connection_connected and connection_completed. If bonding is different to 0xff is known connection
			state = "CONNECTED"
			self.com_log.debug("FSM actual state: %s" % state)

	def ble_evt_sm_bond_status(self,bond,keysize,mitm,keys):
		global state
		if(state == 'PAIRING'):
			self.com_log.debug("BLE bond_status: %02X %02X" % (bond,keys))
			state = "PAIRED"
			self.com_log.debug("FSM actual state: %s" % state)

	def ble_evt_sm_bonding_fail(self,handle,result):
		global state
		self.com_log.error("BLE bonding_fail error: %s" % self.cmd_def_bgapi.get(result))
		state = "DISCONNECTING"
		self.com_log.debug("FSM actual state: %s" % state)

	def ble_rsp_sm_delete_bonding(self,result):
		self.com_log.debug("BLE delete_bonding: %s" % self.cmd_def_bgapi.get(result))

	def ble_rsp_attclient_read_by_group_type(self,connection,result):
		self.com_log.debug("BLE Attribute Client Read By Group Type: %s" % self.cmd_def_bgapi.get(result))

	def ble_evt_attclient_group_found(self,connection,start,end,uuid):
		global server_gatt
		self.com_log.debug("UUID found: 0x%s" % "".join(["%02X" % ord(b) for b in uuid[::-1]]))
		uuid_int = BLE_trl.str_to_int(uuid)
		service_name = BLE_trl.ble_translate_services(uuid_int)

		if(service_name):
			server_gatt.append({"uuid":uuid,"start":start,"end":end,"name":service_name["name"],"characteristics":[]})
			self.com_log.info("Service know: %s" % service_name["name"])

	def ble_evt_attclient_procedure_completed(self,connection,result,chrhandle):
		global services_discover_completed, discovering_characteristics, actual_service_index
		global characteristics_discover_completed, getting_data
		if(not result):
			if(not getting_data):
				self.com_log.debug("Attribute protocol event completed with handle 0x%02X" % chrhandle)
				if(not services_discover_completed):
					services_discover_completed = True
				elif((len(server_gatt) - 1) != actual_service_index): # len of server_gatt - 1 because starts with 0
					discovering_characteristics = False
					actual_service_index += 1
				else:
					characteristics_discover_completed = True
					actual_service_index = 0 # restart for the next process
			else:
				self.com_log.debug("Attribute protocol write event completed with handle 0x%02X" % chrhandle)
		else:
			self.com_log.error("An error occurred in attribute protocol")
			# print("chrhdl 0x%02X - Error: %s" % (chrhandle,self.cmd_def_bgapi.get(result)))
			state = "DISCONNECTING"
			self.com_log.debug("FSM actual state: %s" % state)

	def ble_rsp_attclient_read_by_type(self,connection,result):
		self.com_log.debug("BLE Attribute Client Read By type: %s" % self.cmd_def_bgapi.get(result))

	def ble_evt_attclient_attribute_value(self,connection,atthandle,atttype,value):
		global server_gatt, actual_service_index, getting_data, actual_characteristics_index, data_read

		atttype = int(atttype)

		if(atttype == 0): # value read
			self.com_log.debug("%s Value read 0x%s" % (server_gatt[actual_service_index]['characteristics'][actual_characteristics_index - 1]['name'],"".join(["%02X" % ord(a) for a in value])))
			data_read.append({"name":server_gatt[actual_service_index]['characteristics'][actual_characteristics_index - 1]['name'],"data":value})
			getting_data = False
		elif(atttype == 2): # value indicated
			self.com_log.debug("%s Value indicated 0x%s" % (server_gatt[actual_service_index]['characteristics'][actual_characteristics_index - 1]['name'],"".join(["%02X" % ord(a) for a in value])))
			data_read.append({"name":server_gatt[actual_service_index]['characteristics'][actual_characteristics_index - 1]['name'],"data":value})
			getting_data = False
		elif(atttype == 3): # value read by type
			chr_prop = value[0]
			chr_uuid = value[3:]
			self.com_log.debug("UUID found: 0x%s" % "".join(["%02X" % ord(a) for a in chr_uuid[::-1]]))
			uuid_int = BLE_trl.str_to_int(chr_uuid)
			chr_name = BLE_trl.ble_translate_characteristics(uuid_int)

			if(chr_name):
				self.com_log.info("Characteristic know: %s" % chr_name["name"])
				characteristic = {"uuid":chr_uuid,"name":chr_name["name"],"hdl":atthandle}
				characteristic["read"] = True if (ord(chr_prop) & 0x2) else False
				characteristic["write"] = True if (ord(chr_prop) & 0x8) else False
				characteristic["notify"] = True if (ord(chr_prop) & 0x10) else False
				characteristic["indicate"] = True if (ord(chr_prop) & 0x20) else False
				server_gatt[actual_service_index]["characteristics"].append(characteristic)

	def ble_rsp_attclient_read_by_handle(self,connection,result):
		self.com_log.debug("BLE Attribute Client Read By handle: %s" % self.cmd_def_bgapi.get(result))

	def ble_rsp_attclient_attribute_write(self,connection,result):
		self.com_log.debug("BLE Attribute Client Write: %s" % self.cmd_def_bgapi.get(result))

class SenderTCP(object):

	URL = ""
	PORT = 0
	BUFFER = 0
	com_log = None
	s = None

	def __init__(self,log_conf,url="localhost",port=9000,buf_size=1024):
		self.URL = url
		self.PORT = port
		self.BUFFER = buf_size
		
		self.com_log = logger.set_log(__name__ + "_TCP",log_conf[0],log_conf[1])

		self.__connect()

	def __connect(self):
		try:
			self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

			x = self.s.getsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE)
			if(x == 0):
				self.s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
				self.com_log.debug("Keep-alive turned on")

			self.s.connect((self.URL,self.PORT))
			self.com_log.info("TCP socket to app connected")	
		except socket.error, e:
			self.com_log.error("Cannot connect to the app socket")

	def send(self,data):
		self.s.send(data)

	def recv(self):
		try:
			# s.settimeout(5)
			data = self.s.recv(self.BUFFER)
			return data
		except Exception as e:
			self.com_log.debug("No TCP GUI data")
			return False
