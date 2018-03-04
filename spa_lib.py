import spa_packet
import threading
import socket
from config import Config
import os
import firewall
import client_db
import random
import string
import sys
import logging
import struct
from scapy.all import *
from urllib2 import urlopen

# directory with configuration
MAX_USERS = 1024
MTU = 1024
MAX_KILL_TRIES = 10
CONNECTED = 1
DISCONNECTED = 0

MIN_PORT = 1024
MAX_PORT = 49151
JUNK = "X"*12


TCP_TYPE = 1 
UDP_TYPE = 2

# used for errors defined by SPA function
class spaError(Exception):
	pass

slash_os = lambda: '\\' if os.name == 'nt' else '/'

def send_spa(AID, password, seed, new_seed, ip="localhost", port=443):
	"""
		Sends an spa packet to ip:port
		Uses as authentication user AID and password
		Uses seed to encrypt payload
	"""
	try :
		request = spa_packet.SPAreq(str(AID), str(password), str(seed), str(new_seed))
	except Exception as e:
		raise spaError(e)
	#generate random IP address and port
	dst_ip = ip
	dst_port = random.randint(MIN_PORT, MAX_PORT)

	# get payload
	payload = JUNK + request.get_encoded_pack()
	send(IP(dst=dst_ip)/UDP(dport=int(dst_port))/Raw(load=payload))

def port_is_open(ip, port, conn_type=TCP):
	"""
		Checks if auth worked by attempting to connect to 
		target (ip, port)
	"""
	result = 1
	if conn_type == TCP_TYPE:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		result = sock.connect_ex((ip, port))
	elif conn_type == UDP_TYPE:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		result = sock.connect_ex((ip, port))
	
	return result == 0

# find hosts public ip
def get_public_ip():
	return urlopen('http://ip.42.pl/raw').read()

# find hosts network ip (192.**.**.**)
def get_network_ip():
	return firewall.get_local_ip()



STOP_PORT = 6666
class spaListener(threading.Thread):


	def __init__(self, interface="wlp2s0", 
		block_all = True, change_seeds = True, allowed_ips = [], fw_label = "spa_server",
		db_host='localhost', db_user="root", db_passwd="", db="spa_db", db_port=3316):
		"""
			Establishes a connection on ip:port
			and waits for spa packets.
			Uses user_file data to authenticate users
		"""
		self.interface = interface
		if not os.geteuid() == 0:
			raise spaError("\nYou should be root to run this script")
		super(spaListener, self).__init__()
		# used for terminating daemon
		self.death_event = threading.Event()

		# initiate firewall class
		self.fw = firewall.spaFirewall(fw_label, block_all = block_all, allowed_ips = allowed_ips)

		# mysql models initiate
		self.models = client_db.spa_db(db_host, db_user, db_passwd, db, db_port)	

		self.is_running = False
		self.logged_users = []
		self.change_seeds = change_seeds

	def run(self):
		self.is_running = True
		# sniff untill packet is received
		while not self.death_event.is_set():
			try :
				sniff(stop_filter=lambda x : self._stop_filter(x), filter="udp", \
						prn=lambda x : self._handle_con(x), store=0)
			except Scapy_Exception as err:
				continue	
		self.is_running = False


	def block(self,):
		while True:
			if self.death_event.wait(2):
				break
			
	# terminate by sending death event and messages to the death port 
	def terminate(self):
		self.death_event.set()
		for i in range(0, MAX_KILL_TRIES):
			send(IP(dst='localhost')/UDP(dport=STOP_PORT)/Raw(load=''), verbose = False)
		self.fw.delete_entries()

	def is_alive(self):
		return self.is_running

	def set_client_established(self, aid):
		self.fw.set_established(aid)

	def _stop_filter(self, x):
		# in order to stop sniffing wait for
		# stop_port as destination port
		if x[UDP].dport == STOP_PORT:
			return True
		else:
			return False
		# TODO when there are too many stop packs
		# change port

	def add_firewall_entry(self, ip, label,ctstate="NEW,ESTABLISHED"):
		self.fw.allow_ip(ip, label, ctstate = ctstate)
	
	def _handle_con(self, packet):
		spa_p = None
		try :
			spa_p = spa_packet.SPAreq(packet[Raw].load)
		except Exception as err:
			return
		# get aid for encrypted packet
		aid = spa_p.get_aid()
		# replay packet or tries to login again
		if aid in self.logged_users:
			return
		client = self.models.get_client(aid)
		if not client['success']:
			return
		client = client['client']	
		seed = client['seed']	
		old_seed = client['old_seed']
		pwd = client['password']
		randoms = client['randoms']
		old_randoms = client['old_randoms']
		
		# decrypt the spa packet
		try :
			spa_p.decrypt_packet(seed)
		except spa_packet.InvalidSPA as err:
			# pass because it might be using old seed
			pass
		except Exception as ex:
			return
		
		reset_rand = True	
		# check if authenticated
		if not spa_p.is_authenticated(pwd):
			# check with old seed too
			if old_seed:
				try : 
					spa_p.decrypt_packet(old_seed)
				except Exception as ex:
					# no reason to wait
					return
				if not spa_p.is_authenticated(pwd):
					return
				# check if replay packets
				u_rand = spa_p.get_random()
				if u_rand in old_randoms:
					return
				# set new seed -> old_seed 
				self.use_old_seed(aid)
				self.add_random_to_seed(aid, spa_p.get_random())
		else :
			# check if replay attack for new seed
			u_rand = spa_p.get_random()
			if u_rand in randoms:
				return 
			self.add_random_to_old_seed(aid, spa_p.get_random())
		
		new_seed = spa_p.get_new_seed()	
		if new_seed and self.change_seeds:
			self.set_new_seed(aid, seed = spa_p.get_new_seed())
		# TODO get packet fields 
		# get user ip
		try :
			ip_src = packet[IP].src
		except Exception as err:
			return
		self.logged_users.append(aid)
		# now allow in firewall
		self.fw.allow_ip(ip_src, aid)


	# model functions

	def add_client(self, password, seed):
		return self.models.add_client(password, seed)


	def edit_client(self, aid, password = None):
		return self.models.edit_client(aid, password)

	def remove_client(self, aid):
		return self.models.remove_client(aid)
	
	def set_new_seed(self, aid, seed):
		return self.models.set_new_seed(aid, seed)
	
	def use_old_seed(self, aid):
		return self.models.use_old_seed(aid)

	def add_random_to_seed(self, aid, random):
		return self.models.add_random_to_seed(aid, random)

	def add_random_to_old_seed(self, aid, random):
		return self.models.add_random_to_old_seed(aid, random)
