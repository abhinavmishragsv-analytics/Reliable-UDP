import socket
import random
import struct
import hashlib
import time

# Configuration

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5001

INPUT_FILE = "input.txt"

# Size of file data in each packet
CHUNK_SIZE = 1024

# Timeout for ACK
TIMEOUT = 1.0

# Probability of deliberately dropping
# a packet before transmission
PACKET_DROP_PROBABILITY = 0.20

# Probability of deliberately retransmitting
# a packet even after receiving an ACK
EXTRA_RETRANSMISSION_PROBABILITY = 0.10

# Statistics

total_packets_generated = 0
total_packets_transmitted = 0
packets_deliberately_dropped = 0
retransmissions = 0

# Hash function

def calculate_hash(filename):

    sha256 = hashlib.sha256()

    with open(filename, "rb") as f:

        while True:

            data = f.read(4096)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()

# Read file

with open(INPUT_FILE, "rb") as f:

    file_data = f.read()

# Divide file into chunks

packets = []

for i in range(0, len(file_data), CHUNK_SIZE):

    chunk = file_data[i:i + CHUNK_SIZE]

    packets.append(chunk)


total_packets_generated = len(packets)

original_hash = calculate_hash(INPUT_FILE)

# Create UDP socket

client_socket = socket.socket(
    socket.AF_INET,
    socket.SOCK_DGRAM
)

client_socket.settimeout(TIMEOUT)

server_address = (
    SERVER_IP,
    SERVER_PORT
)


print("=" * 60)
print("UDP RELIABLE FILE TRANSFER - CLIENT")
print("=" * 60)

print(f"Input file       : {INPUT_FILE}")
print(f"File size        : {len(file_data)} bytes")
print(f"Chunk size       : {CHUNK_SIZE} bytes")
print(f"Total packets    : {total_packets_generated}")
print(f"Original SHA-256 : {original_hash}")
print()

# Send metadata

info_packet = (
    b"INFO"
    + struct.pack("!I", total_packets_generated)
    + original_hash.encode()
)

client_socket.sendto(
    info_packet,
    server_address
)


# Wait for metadata ACK

while True:

    try:

        response, _ = client_socket.recvfrom(1024)

        if response == b"INFO_ACK":

            break

    except socket.timeout:

        client_socket.sendto(
            info_packet,
            server_address
        )


print("Metadata acknowledged.")
print()
print("Starting file transfer...")
print("-" * 60)

# Send packets

for sequence_number, chunk in enumerate(packets):

    packet = (
        b"DATA"
        + struct.pack("!I", sequence_number)
        + chunk
    )

    acknowledged = False

    first_attempt = True

    while not acknowledged:

        # Simulate deliberate packet loss

        if first_attempt:

            first_attempt = False

            if random.random() < PACKET_DROP_PROBABILITY:

                packets_deliberately_dropped += 1

                print(
                    f"[DROP] Packet {sequence_number} "
                    f"deliberately dropped"
                )

                # No packet is sent.
                # Wait briefly and then
                # retransmit.

                time.sleep(0.1)

                retransmissions += 1

                continue

        # Send packet

        client_socket.sendto(
            packet,
            server_address
        )

        total_packets_transmitted += 1

        if retransmissions > 0:

            print(
                f"[RETRANSMIT] Packet "
                f"{sequence_number}"
            )

        else:

            print(
                f"[SEND] Packet "
                f"{sequence_number}"
            )

        # Wait for ACK

        try:

            while True:

                ack_packet, _ = client_socket.recvfrom(
                    1024
                )

                if ack_packet[:3] != b"ACK":

                    continue

                ack_number = struct.unpack(
                    "!I",
                    ack_packet[3:7]
                )[0]

                if ack_number == sequence_number:

                    acknowledged = True

                    print(
                        f"       ACK {sequence_number} received"
                    )

                    break

        except socket.timeout:

            # ACK was probably lost

            retransmissions += 1

            print(
                f"       TIMEOUT -> "
                f"retransmitting packet "
                f"{sequence_number}"
            )

    # Optional extra duplicate
    
    if random.random() < EXTRA_RETRANSMISSION_PROBABILITY:

        print(
            f"       Simulating EXTRA "
            f"retransmission of packet "
            f"{sequence_number}"
        )

        client_socket.sendto(
            packet,
            server_address
        )

        total_packets_transmitted += 1

        retransmissions += 1


print()
print("=" * 60)
print("FILE TRANSFER COMPLETE")
print("=" * 60)

# Statistics

print()
print("CLIENT STATISTICS")
print("-" * 60)

print(
    f"Total packets generated     : "
    f"{total_packets_generated}"
)

print(
    f"Total packets transmitted   : "
    f"{total_packets_transmitted}"
)

print(
    f"Packets deliberately dropped: "
    f"{packets_deliberately_dropped}"
)

print(
    f"Number of retransmissions   : "
    f"{retransmissions}"
)

print("=" * 60)


client_socket.close()