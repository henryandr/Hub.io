import log as logger
import threading, json, socket

class Sender(threading.Thread):

	com_log = None
	q = None

	def __init__(self,log_conf,q):
		threading.Thread.__init__(self)
		self.com_log = logger.set_log(__name__,log_conf[0],log_conf[1])
		self.q = q

	def run(self):
		data = self.q.get()
		self.com_log.info("Message received")