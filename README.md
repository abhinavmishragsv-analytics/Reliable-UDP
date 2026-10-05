This project demonstrates reliable file transfer over the UDP protocol.
UDP is an unreliable transport protocol because it does not guarantee
packet delivery, packet ordering, or duplicate-free transmission.

To provide reliability, the client divides the input file into packets.
Each packet is assigned a unique sequence number. The server sends an
acknowledgement for every successfully received packet.

The system deliberately simulates network problems including packet loss,
ACK loss, and retransmissions. The server detects duplicate packets
using sequence numbers and ensures that duplicate data is not written
more than once.

After receiving all packets, the server reconstructs the original file
in the correct sequence and verifies the reconstructed file using SHA-256.

This experiment demonstrates how reliability can be implemented at the
application layer on top of an unreliable UDP transport protocol.
