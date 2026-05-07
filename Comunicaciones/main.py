import sys, os
import commentjson, signal
import Queue

# add paths for libraries
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/libs/General")
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + "/libs/Translate")

import log as logger
import serial_listener, serial_listener_ble
import sender

def read_config_file():
	""" Read the config.json file.

	Read the config.json file to set the options
	of the hub.io data getter.

	Returns.
		JSON configuration data without comments
	"""

	with open("./config.json","r") as config_file:
		return commentjson.load(config_file)

def log_config_file(c):
	""" Log the configuration file read """

	com_log.info("Configuration file Version %s" % c['version'])
	com_log.info("Logs are stored in %s" % c['log_path'])
	if(c['debug'] == "true"): com_log.info("Console debug is active")
	com_log.info("Messages will be send to %s REST version %s" % (c['base_url'],c['api_v']))
	com_log.info("Messages version HL7 %s" % c['HL7_v'])
	for x in c['interfaces']:
		com_log.info("Interface %s attach to uart %s at %d bps" % (x['type'],x['uart'],x['baudrate']))
	com_log.debug("File readed")

def signal_handler(signal, frame):
	""" Function to catch SIGINT event """
	global wifi_com,ble_com
	com_log.info('Closing ...')
	
	try:
		wifi_com.close_serial()
	except:
		pass

	try:
		ble_com.close_serial()
	except Exception as e:
		print(str(e))
		
	sys.exit(0)

if __name__ == "__main__":
	signal.signal(signal.SIGINT, signal_handler) # Capture Ctrl+C 

	conf = read_config_file()

	com_log = logger.set_log(__name__,conf['log_path'],conf['debug'])

	log_config_file(conf)

	q = Queue.Queue()

	com_log.info("Initializing interfaces")
	for interface in conf['interfaces']:
		if(interface['type'] == 'wifi'):
			wifi_com = serial_listener.Serial(interface,(conf['log_path'],conf['debug']))
		elif(interface['type'] == 'ble'):
			ble_com = serial_listener_ble.BleSerial(interface,(conf['log_path'],conf['debug']),q)
		else:
			com_log.warn("Interface %s not supported" % interface['type'])

	com_log.info("Initializing sender")
	data_sender = sender.Sender((conf['log_path'],conf['debug']),q)
	data_sender.daemon = True
	data_sender.start()

	while 1:
		pass