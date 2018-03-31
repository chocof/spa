import spa_lib
import logging
import os

def init_logger(name, levl, file = False):
	logger = logging.getLogger(name)
	logger.setLevel(levl)

	# create formatter and add it to the handlers
	formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

	# create file handler
	if file:
		# create folder and file
		if not os.path.exists(file):
			if not os.path.exists(os.path.dirname(file)):
				crt_fldr(os.path.dirname(file))
			with open(path, 'a'):
				os.utime(path, None)
		fh = logging.FileHandler(file)
		fh.setLevel(levl)
		fh.setFormatter(formatter)
		logger.addHandler(fh)
	# create console
	ch = logging.StreamHandler()
	ch.setLevel(levl)

	ch.setFormatter(formatter)
	# add the handlers to the logger
	logger.addHandler(ch)
	return logger

def help():
	pass










