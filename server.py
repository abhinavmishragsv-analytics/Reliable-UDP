import socket
import random
import struct
import hashlib

# Configuration

HOST = "0.0.0.0"
PORT = 5001

OUTPUT_FILE = "received_output.txt"

ACK_DROP_PROBABILITY = 0.20

BUFFER_SIZE = 2048

# Statistics

duplicate_packets = 0
acks_dropped = 0
packets_received = 0

# Helper function

def calculate_hash(filename):
    sha256 = hashlib.sha256()

    with open(filename, "rb") as f:
        while True:
            data = f.read(4096)

            if not data:
                break

            sha256.update(data)

    return sha256.hexdigest()

# Create UDP socket

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_socket.bind((HOST, PORT))

print("=" * 60)
print("UDP RELIABLE FILE TRANSFER - SERVER")
print("=" * 60)
print(f"Server listening on {HOST}:{PORT}")
print()

# Receive metadata

data, client_address = server_socket.recvfrom(BUFFER_SIZE)

message_type = data[:4]

if message_type != b"INFO":
    print("Invalid connection.")
    server_socket.close()
    exit()

total_packets = struct.unpack("!I", data[4:8])[0]

original_hash = data[8:].decode()

print(f"Client connected: {client_address}")
print(f"Total packets expected: {total_packets}")
print(f"Original SHA-256: {original_hash}")
print()

# Send metadata ACK

server_socket.sendto(b"INFO_ACK", client_address)

# Receive data packets

received_packets = {}

print("Receiving packets...")
print("-" * 60)

while len(received_packets) < total_packets:

    packet, address = server_socket.recvfrom(BUFFER_SIZE)

    if packet[:4] != b"DATA":
        continue

    sequence_number = struct.unpack("!I", packet[4:8])[0]

    file_data = packet[8:]

    packets_received += 1

    # Duplicate detection

    if sequence_number in received_packets:

        duplicate_packets += 1

        print(
            f"[DUPLICATE] Packet {sequence_number} received again"
        )

    else:

        received_packets[sequence_number] = file_data

        print(
            f"[RECEIVED] Packet {sequence_number} "
            f"({len(file_data)} bytes)"
        )

    # Simulate ACK loss

    if random.random() < ACK_DROP_PROBABILITY:

        acks_dropped += 1

        print(
            f"        ACK {sequence_number} deliberately DROPPED"
        )

        continue

    # Send ACK

    ack = struct.pack("!I", sequence_number)

    server_socket.sendto(
        b"ACK" + ack,
        client_address
    )

    print(
        f"        ACK {sequence_number} sent"
    )


print()
print("=" * 60)
print("All packets received.")
print("=" * 60)

# Reconstruct file

print("Reconstructing file...")

with open(OUTPUT_FILE, "wb") as output:

    for sequence_number in range(total_packets):

        if sequence_number not in received_packets:

            print(
                f"ERROR: Missing packet {sequence_number}"
            )

            server_socket.close()
            exit()

        output.write(
            received_packets[sequence_number]
        )

print(f"File written to: {OUTPUT_FILE}")

# Verify file

received_hash = calculate_hash(OUTPUT_FILE)

print()
print("=" * 60)
print("FILE VERIFICATION")
print("=" * 60)

print(f"Original hash   : {original_hash}")
print(f"Received hash   : {received_hash}")

if original_hash == received_hash:

    print("\nSUCCESS: Files are identical.")

else:

    print("\nERROR: Files are NOT identical.")

# Statistics

print()
print("=" * 60)
print("SERVER STATISTICS")
print("=" * 60)

print(f"Total packets expected      : {total_packets}")
print(f"Total packet arrivals      : {packets_received}")
print(f"Duplicate packets received : {duplicate_packets}")
print(f"ACKs deliberately dropped   : {acks_dropped}")

print("=" * 60)

server_socket.close()