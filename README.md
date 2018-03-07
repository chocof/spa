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

The whole payload is then encrypted via AES256 using the common seed(32B) shared between the 
server and the client.

The server runs the SPA server daemon. This thread blocks access to all ports and monitors the network for 
SPA packets. Once an SPA packet has been received it tries to authenticate it.

Project not yet completed
-------
This project is still under development