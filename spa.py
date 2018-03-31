import spa_lib
import logging
import os
import argparse
import sys
import colorama
import termcolor 
import pyfiglet

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

def get_args():
	parser = argparse.ArgumentParser(
		description="A CLI for using the SPA library",
		epilog="In order to view the source code visit https://github.com/chocof/spa")
	parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2], 
		help="increase output verbosity (default:1)", default=1)
	
	subparsers = parser.add_subparsers()	
	
	# server options
	s_parser = subparsers.add_parser("srv", help="run an SPA server (default)")
	s_parser.add_argument("-g", "--generate_client", help="generate a new client and its file", default=False)
	s_parser.add_argument("-i", "--interface", help="interface to listen to", default="wlan0")
	s_parser.add_argument("-b", "--block_all", help="block access to all firewall ports", 
		action="store_true",default=True)
	s_parser.add_argument("-c", "--change_seeds", 
		help="change shared seed with clients after successful authentication", 
		action='store_true', default=True)
	s_parser.add_argument("-l", "--fw_label", help="label to mark new firewall rules with", default="my_firewall")
	s_parser.add_argument("-a", "--allowed", nargs='+', help="list of allowed IPs")
	s_parser.add_argument("-d", "--db", help="database name", default="spa_db")
	s_parser.add_argument("-o", "--db_host", 
		help="database host (default:'localhost')", default="localhost")
	s_parser.add_argument("-u", "--db_user", 
		help="database user (default:'root')", default="root")
	s_parser.add_argument("-p", "--db_pwd", 
		help="database password (default:'')", default="")
	s_parser.add_argument("-t", "--db_port", type=int, 
		help="database port (default:3316)", default=3316)

	# client options
	c_parser = subparsers.add_parser("clt", help="run an SPA client")
	c_parser.add_argument("-f","--client_file", type=str, 
		help="file where client data are stored", default="")
	c_parser.add_argument("-a","--aid", help="aid of the client")
	c_parser.add_argument("-p","--password", help="password of the client")
	c_parser.add_argument("-x","--seed", help="seed of the client")
	c_parser.add_argument("-s","--server", help="SPA server's IP")
	c_parser.add_argument("-t","--port", help="port to request access to")
	
	args = parser.parse_args()
	return args

def show_banner():
	colorama.init(strip=not sys.stdout.isatty())
	termcolor.cprint(pyfiglet.figlet_format('SPA', font='starwars'),
		'red', attrs=['bold'])


def main():
	show_banner()
	args = get_args() 
	print args

main()	





