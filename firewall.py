from netifaces import interfaces, ifaddresses, AF_INET
import iptc
import sys
import socket

INPUT 	= 0
OUTPUT 	= 1
DEFAULT_TLS_PORT = 443


def get_local_ip():
	return ([l for l in ([ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] 
			if not ip.startswith("127.")][:1], [[(s.connect(('8.8.8.8', 53)), 
			s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, 
			socket.SOCK_DGRAM)]][0][1]]) if l][0][0]) 



class spaFirewall(object):


	def __init__(self, me, block_all = False, allowed_ips = []):
		# set default tls port
		self.table = iptc.Table(iptc.Table.FILTER)

		self.chains = { INPUT : iptc.Chain(self.table, "INPUT"),
						OUTPUT : iptc.Chain(self.table, "OUTPUT")}
		self.me = me
		self.block_all = block_all
		# Blocks all traffic to all ports
		if self.block_all:
			# flushes rules
			self.chains[INPUT].flush()
			self.chains[OUTPUT].flush()

			rule = iptc.Rule()
			rule.protocol = "tcp"
			rule = iptc.Rule()
			rule.target = iptc.Target(rule,"DROP")

			# add label comment
			match = rule.create_match("comment")
			match.comment = "\"%s\"" % (self.me + ":BLOCK_ALL")
			self.chains[INPUT].insert_rule(rule)
			# # flush output
			sys.stdout.flush()
		if allowed_ips : 
			i = 0
			for ip in allowed_ips:
				i += 1
				self.allow_ip(ip, 'PRE-ALLOW:' + str(i), ctstate="ESTABLISHED")	

	def allow_ip(self, ip, port, label, ctstate = "NEW,ESTABLISHED"):
			
		rule = iptc.Rule()
		rule.protocol = "tcp"
		
		# for same network addresses
		my_ip = get_local_ip()
		if ip == my_ip:
			rule.src = '127.0.0.1'
		else :
			rule.src = ip
		
		match = iptc.Match(rule,"tcp")
		match.dport = str(port)
		rule.add_match(match)

		# TODO add port option
		match = iptc.Match(rule,"conntrack")
		match.ctstate = ctstate
		rule.add_match(match)
		
		# add label comment
		match = rule.create_match("comment")
		match.comment = "\"%s\"" % (self.me + ":" + label)
		
		# add new rule
		rule.target = iptc.Target(rule,"ACCEPT")
		self.chains[INPUT].insert_rule(rule)
		sys.stdout.flush()
		self.table.refresh()

	# remove ip from allowed list
	def remove_ip(self, label):
		# turn off autocommit 
		# self.table.autocommit = False
		to_search = "\"%s\"" % (self.me + ":" + label)

		for rule in self.chains[INPUT].rules:
			for match in rule.matches:
				params = match.get_all_parameters()
				if 'comment' in params:
					if to_search in params['comment']:
						try:
							self.chains[INPUT].delete_rule(rule)
							break
						except Exception as err:
							break	
		sys.stdout.flush()
		self.table.refresh()

	# remove ip from allowed list
	def set_established(self, label):
		# turn off autocommit 
		# self.table.autocommit = False
		to_search = "\"%s\"" % (self.me + ":" + label)
		ip = None
		for rule in self.chains[INPUT].rules:
			found = False
			for match in rule.matches:
				if match.dport:
					port = match.dport
				params = match.get_all_parameters()
				if 'comment' in params:
					for param in params['comment']:
						if param.startswith(to_search):
							ip = rule.src.split('/', 1)[0]
							found = True
			if found:
				break							
		if not ip :
			return

		# remove old rule
		self.remove_ip(label)
		# add new rule
		self.allow_ip(ip, port, label, ctstate = 'ESTABLISHED')
		sys.stdout.flush()
		self.table.refresh()
	
	# remove ip from allowed list
	def delete_entries(self, ):
		# turn off autocommit 
		# self.table.autocommit = False
		to_search = "\"%s" % (self.me + ":")

		for rule in self.chains[INPUT].rules:
			for match in rule.matches:
				params = match.get_all_parameters()
				if 'comment' in params:
					for param in params['comment']:
						if param.startswith(to_search):
							try:
								self.chains[INPUT].delete_rule(rule)
								break
							except Exception as err:
								continue	
		sys.stdout.flush()
		self.table.refresh()
	

	def __str__(self):
		str_r = ""
		for chain in self.table.chains:
			str_r += "======================="
			str_r += "Chain ", chain.name
			for rule in chain.rules:
				str_r += "Rule", "proto:", rule.protocol, "src:", rule.src, "dst:", \
				rule.dst, "in:", rule.in_interface, "out:", rule.out_interface,
				str_r += "Matches:",
			for match in rule.matches:
				str_r += match.name,
				str_r += "Target:",
				str_r += rule.target.name
			str_r += "======================="
		return str_r
