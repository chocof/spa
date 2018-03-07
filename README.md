# SPA (Single Packet Authorization)


Description
-------
Most network protocols establish a connection before authorization with client takes place. 
The problem with this is that open ports are visible to outsiders and therefore are susceptible
to network attacks.

The first solution to this problem was the Port Knocking Protocol. The client, in order to open
and sustain a TLS connection with the server, would first have to send some packets to a predefined sequence
of ports. However this protocol was also susceptible
to a list of [attacks](http://www.cipherdyne.org/fwknop/docs/SPA.html)  

SPA is a solution that maintains the basic Port Knocking's idea (authorize -> connect) while trying to solve
its problems.

Implementation
--------

#### Packet

This implementation is based on fwknop' version of SPA as well as the RFC 4226. A SPA packet payload has 
the following fields : 
* AID(32B): agent ID which is a unique ID for the device. (UUID is recommended)
* Password(32B): user password
* Random(4B): Random number created in order to find doubles and avoid MiTM attacks
* MD5 Hash(16B): MD5 Hash of the following fields. Used in order to detect changes to initial payload
* New Seed(32B): Seed to be used in the next client-server interaction
* IP(4B): Client IP to be allowed in firewall
* Port(4B): Port to allow tcp connections
The whole payload is then encrypted via AES256 using the common seed(32B) shared between the 
server and the client.

The server runs the SPA server daemon. This thread blocks access to all ports and monitors the network for 
SPA packets. Once an SPA packet has been received it tries to authenticate it. Once the packet is authenticated
it allows the client to connect to the given port and ip.

spa_lib
--------

### Client

#### *get_public_ip*()
Returns the client's public IP

#### *get_network_ip*()
Returns the client's network IP

#### *port_is_open*(ip, port)
Check if SPA worked and SPA server has allowed firewall access

#### *generate_seed*(l)
Generate random string of size l

#### *send_spa*(aid, password, seed, new_seed, ip, port, server_ip)
* AID : ID of the client
* password : password of the client
* seed : seed to encrypt the packet with
* new_seed : seed to be used in the next transaction (must be 32 bytes, best use designated function)
* ip, port : IP and port to request access to (in order to get IP use one of the designated fucntions)
* server_ip : the ip of the SPA server

#### Usage
Ideally the client shall try to authenticate itself. The server changes the shared seed only if authentication
was successful therefore the client shall change the encryption seed only once it is authenticated

Example: 
```python
aid = "92de863e74dbbe8d9b8da1e2a476ca6f"
password = "mypassword"
seed = "46facea6c4f41fdd11e8acf9646e69b2"
new_seed = spa_lib.generate_seed(32)
ip = spa_lib.get_public_ip()
server_ip = "30.205.223.69"
port = 443

while True:
	spa_lib.send_spa(aid, password, seed, new_seed, ip, port, server_ip)
	if spa_lib.port_is_open(server_ip, port):
		break

# store new key for next transaction
user_files.store(me, {seed : new_seed})
```

### Server

#### Class *spaListener*(interface, block_all, change_seeds, allowed_ips, fw_label,
		db_host, db_user, db_passwd, db, db_port)
This is the SPA Server. It runs as a background daemon threads, blocks access to all of the system's
ports, listens for SPA packets and authenticates clients.
* interface : interface to listen to for packets
* block_all : block or firewall connections (default : True)
* change_seeds : change each client's seed to new_seed after successful authentication (default : True)
* allowed_ips : a list with ips to allow (in case where the block_all option is set)
* fw_label : the label to add to new firewall rules as a comment (default : 'spa_server')
* db_host, db_user, db_passwd, dp_port : Credentials used to connect to the database in which client data are stored 

##### *start*()
Start daemon thread

##### *block*()
Block program execution until the SPA server closes

##### *terminate*()
Terminate the SPA server

##### *is_alive*()
Check if SPA server is alive

##### *add_firewall_entry*(ip, label, ctstate)
Add a new firewall entry
* ip : IP to allow firewall entry to
* label : label to mark new allow rule
* ctstate : Set rule to accept NEW,ESTABLISHED or both (default : 'NEW, ESTABLISHED')

##### *set_client_established*(label)
Sets the rule with the corresponding label to established.  


#####*add_client*(password, seed)
Creates a new client to the database with the corresponding password and seed.
The seed must be 32 bytes (use the *generate_key* function)


#####*edit_client*(aid, password)
Edits the password of the client with the specified id.

#####*remove_client*(aid):)
Removes the client with the specified id.

#####*set_new_seed*(aid, seed)
Changes the used shared seed for the client with the specified id.

#####*use_old_seed*(aid)
Instructs the SPA server to use the previously used shared secret seed to decrypt client messages
for the client with the corresponding id.

### Usage
The user has to first initialize the SPA server and then start the SPA daemon thread.
```python

interface = 'wlan0'
block_all = True
change_seeds = True
allowed_ips = "127.0.0.1"
fw_label = "my_firewall"
#mysql creds
db_host="localhost"
db_user="root"
db="spa_db"
db_passwd="drowssap"
db_port=3316

s = spa_lib.spaListener(interface, block_all, change_seeds, allowed_ips, fw_label,
		db_host, db_user, db_passwd, db, db_port)
#initiate daemon thread
s.start()
s.block()
```


Project not yet completed
-------
This project is still under development