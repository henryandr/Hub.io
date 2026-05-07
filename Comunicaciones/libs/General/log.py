import logging

def set_log(name,path,debug,level='INFO'):
	"""Set the logger's format

	Configure logger for each name given.

	Args:
		name:		name for the logger to be created.
		path:		log file's path
		debug:		enable debug console
		[level]:	level of the logger. Default is set to INFO level.

	Returns:
		logger:		logger object formatted and ready to use!
	"""

	# Using dictionary to select level
	log_level = {
		'NOTSET':logging.NOTSET,
		'DEBUG':logging.DEBUG,
		'INFO':logging.INFO,
		'WARNING':logging.WARNING,
		'ERROR':logging.ERROR,
		'CRITICAL':logging.CRITICAL
	}.get(level)
	
	# Set logger
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)

	# Set format
	formatter = logging.Formatter('%(asctime)s - %(name)-23s - %(levelname)-8s - %(message)s')

	# Set File Handler
	file_hdlr = logging.FileHandler(path)
	file_hdlr.setLevel(level)
	file_hdlr.setFormatter(formatter)

	# add handler to logger
	logger.addHandler(file_hdlr)

	# Set Console handler if true
	if(debug == "true"):
		console_hdlr = logging.StreamHandler()
		console_hdlr.setLevel(logging.DEBUG)
		console_hdlr.setFormatter(formatter)
		logger.addHandler(console_hdlr)

	return logger