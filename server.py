import socket
import threading
import time

class FileSharingServer:
    def __init__(self):
        self.client_data = {}  # Stores client IP and shared files
        self.server_running = True
        self.create_listening_server()
        threading.Thread(target=self.receive_messages_in_a_new_thread, daemon=True).start()
        threading.Thread(target=self.run_command_shell, daemon=True).start()
    def create_listening_server(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        local_port = 9999
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((local_ip, local_port))
        print(f"Listening for incoming messages on {local_ip}:{local_port}")
        self.server_socket.listen(5)
        # self.receive_messages_in_a_new_thread()

    def handle_client(self, client_socket):
        while True:
            try:
                message = client_socket.recv(1024).decode('utf-8')
                if not message:
                    break

                command, data = self.parse_client_message(message)
                if command == 'publish':
                    self.publish_files(client_socket, data)
                elif command == 'fetch':
                    self.send_file_sources(client_socket, data)

            except socket.error:
                break

        client_socket.close()

    def parse_client_message(self, message):
        parts = message.split()
        return parts[0], parts[1:]

    def publish_files(self, client_socket, file_list):
        client_address = client_socket.getpeername()[0]
        self.client_data[client_address] = file_list
        client_socket.send("Files published successfully".encode('utf-8'))

    def send_file_sources(self, client_socket, data):
        file_name = data[0]
        sources = [ip for ip, files in self.client_data.items() if file_name in files]
        response = ' '.join(sources)
        client_socket.send(response.encode('utf-8'))

    def receive_messages_in_a_new_thread(self):
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"Connection from {addr} has been established.")
                self.client_data[addr[0]] = []  # Initialize client file list
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
            except Exception as e:
                print(f"An error occurred: {e}")
    def run_command_shell(self):
        while self.server_running:
                command = input("Enter command: ")
                if command.startswith("discover"):
                    _, hostname = command.split()
                    self.discover_files(hostname)
                elif command.startswith("ping"):
                    _, hostname = command.split()
                    self.ping_client(hostname)
                elif command == "exit":
                    print("Shutting down server...")
                    self.server_running = False
                    break
                else:
                    print("Unknown command")

    def discover_files(self, hostname):
        # Retrieve and print the list of files for the given hostname
        for client_ip, files in self.client_data.items():
            if hostname == client_ip:  # Assuming hostname is the IP of the client
                print(f"Files for {hostname}: {files}")
                break
        else:
            print(f"No files found for {hostname}")

    def ping_client(self, hostname):
        # Check if the client is active
        if hostname in self.client_data:
            print(f"{hostname} is active")
        else:
            print(f"{hostname} is not active or not connected")
# Usage
server = FileSharingServer() 
# Keep the main thread running until the 'exit' command is issued
try:
    while server.server_running:
        time.sleep(1)
except KeyboardInterrupt:
    print("Server is shutting down...")