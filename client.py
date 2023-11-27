import socket
import threading
import os

class FileSharingClient:
    def __init__(self, server_ip, server_port, peer_port=10000):
        self.server_ip = server_ip
        self.server_port = server_port
        self.peer_port = peer_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_server()
        threading.Thread(target=self.start_peer_server, daemon=True).start()

    def connect_to_server(self):
        try:
            self.socket.connect((self.server_ip, self.server_port))
            print("Connected to server.")
        except socket.error as e:
            print(f"Error connecting to server: {e}")

    def publish_files(self, file_list):
        message = "publish " + " ".join(file_list)
        self.socket.send(message.encode('utf-8'))
        response = self.socket.recv(1024).decode('utf-8')
        print(response)

    def fetch_file_from_peer(self, peer_ip, file_name):
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((peer_ip, self.peer_port))  # Use the configurable peer port
            print(f"Connecting to peer at {peer_ip} to download {file_name}")
            # Send file request to peer
            peer_socket.send(f"GET {file_name}".encode('utf-8'))
            # Receive the file
            with open(file_name, 'wb') as file:
                while True:
                    file_data = peer_socket.recv(1024)
                    if not file_data:
                        break
                    file.write(file_data)
            print(f"File {file_name} downloaded from {peer_ip}")
            peer_socket.close()
        except socket.error as e:
            print(f"Error connecting to peer: {e}")

    def fetch_file(self, file_name):
        message = f"fetch {file_name}"
        self.socket.send(message.encode('utf-8'))
        sources = self.socket.recv(1024).decode('utf-8').split()
        if sources:
            print(f"File found at {sources}")
            self.fetch_file_from_peer(sources[0], file_name)
        else:
            print("File not found on the network.")

    def start_peer_server(self):
            def handle_peer_client(client_socket):
                while True:
                    try:
                        message = client_socket.recv(1024).decode('utf-8')
                        if message.startswith("GET"):
                            _, fname = message.split()
                            if os.path.isfile(fname):  # Check if file exists
                                print(f"Sending {fname} to peer")
                                with open(fname, 'rb') as file:
                                    while True:
                                        file_data = file.read(1024)
                                        if not file_data:
                                            break
                                        client_socket.send(file_data)
                                print(f"File {fname} sent to peer")
                            else:
                                print(f"File {fname} not found")
                                client_socket.send("File not found".encode('utf-8'))
                        else:
                            break
                    except socket.error:
                        break
                    finally:
                        client_socket.close()

            peer_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            peer_server_socket.bind(('0.0.0.0', self.peer_port))  # Using the configurable peer port
            peer_server_socket.listen(5)

            while True:
                peer_client_socket, addr = peer_server_socket.accept()
                print(f"Peer connection from {addr} has been established.")
                peer_thread = threading.Thread(target=handle_peer_client, args=(peer_client_socket,))
                peer_thread.start()

    def disconnect(self):
        """Gracefully disconnect from the server and close resources."""
        print("Disconnecting from server...")
        try:
            self.socket.send("disconnect".encode('utf-8'))  # Inform server about disconnection
            self.socket.close()
            print("Disconnected.")
        except socket.error as e:
            print(f"Error while disconnecting: {e}")
        finally:
            self.socket = None

    def run_command_shell(self):
        while True:
            command = input("Enter command: ")
            if command.startswith("publish"):
                parts = command.split()
                if len(parts) != 3:
                    print("Usage: publish lname fname")
                    continue
                lname, fname = parts[1], parts[2]
                if os.path.isfile(lname):
                    self.publish_files([fname])  # Publishing fname to the server
                    os.rename(lname, fname)  # Renaming local file lname to fname
                else:
                    print(f"File {lname} not found.")
            elif command.startswith("fetch"):
                if self.validate_fetch_command(command):
                    _, file_name = command.split()
                    self.fetch_file(file_name)
                else:
                    print("Invalid fetch command. Usage: fetch fname")
            else:
                print("Unknown command")

    def validate_publish_command(self, command):
        """Validate the publish command."""
        parts = command.split()
        if len(parts) != 3:
            return False
        lname, fname = parts[1], parts[2]
        # Further validation logic can be added here (e.g., check file existence)
        return True

    def validate_fetch_command(self, command):
        """Validate the fetch command."""
        parts = command.split()
        return len(parts) == 2 and parts[1].strip() != ""

# Usage Example
client = FileSharingClient("192.168.137.1", 9999)
client.run_command_shell()