import threading, serial
import log as logger

class Serial(object):

	serial_port = None # Connection serial.py object
	com_type = None 
	port = None
	baud = None
	alive = None
	t = None
	state = "WAITING"
	__data = None
	com_log = None

	def __init__(self,uart_conf,log_conf):
		# threading.Thread.__init__(self)
		self.com_log = logger.set_log(__name__,log_conf[0],log_conf[1])
		self.com_type = uart_conf['type']
		self.port = uart_conf['uart']
		self.baud = uart_conf['baudrate']
		self.alive = threading.Event()
		self.alive.set()
		self.t = threading.Thread(target=self.rx) # threading instance
		self.t.daemon = True
		self.t.start()

	def __com_fsm(self,data):

		HEADER = 0xaa
		TAIL = 0xaa

		if(self.state == "WAITING"):
			if(HEADER == data):
				self.state = "MESSAGE"
				self.data = data
		elif(self.state == "MESSAGE"):
			self.__data += data
			if(TAIL == data):
				self.state = "END"
		else:
			pass
			# TODO: translate IEEE 11073 message

		self.com_log.debug("State %s" % self.state)		

	# run function: default name of function to be run by the thread
	# when it is initialized
	def rx(self):
		try:
			if self.serial_port: # Clear the serial port if exists
				self.serial_port.close()
			self.serial_port = serial.Serial(port=self.port,baudrate=self.baud)
			self.com_log.info("Interface %s on port %s ready to use" % (self.com_type,self.port))
		except serial.SerialException, e:
		    self.com_log.info("Error opening Interface %s in port %s" % (self.com_type,self.port))
		    return

		while self.alive.isSet(): # Only when data in the buffer exists
			data = self.serial_port.read(1) # Read the first Byte
			# actual_data += self.serial_port.read(self.serial_port.inWaiting()) # Keeps reading the buffer until there is no more data
			# data += actual_data
			if(data):
				self.__com_fsm(data)

	def close_serial(self):
		self.serial_port.close()
		self.com_log.debug("Interface %s on port %s closed" % (self.com_type,self.port))

if __name__ == "__main__":
	interface = {"type" : "wifi","uart" : "/dev/ttyO1","baudrate" : 115200}
	conf = {'log_path' : "./Logs/report.log", "debug" : "true"}
	wifi_com = Serial(interface,(conf['log_path'],conf['debug']))

	while 1:
		pass