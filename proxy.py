import socket
import time
import sys


class Proxy:
    MAX_CLIENTS = 1  # Number of allowed asynchronous clients
    BUFFER_SIZE = 20  # Fast response
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Proxy Socket

    def __init__(self, addr, port):
        self.cache = Cache()

        self.proxy_socket.bind((addr, port))
        self.proxy_socket.listen(self.MAX_CLIENTS)

        print("[*] Waiting for Clients to Connect")
        print("[*] TCP proxy listening on ('%s', %s)" % (addr, port))

        self.accept_incoming_connections()

    def accept_incoming_connections(self):
        # Accept incoming client connections
        while 1:
            client, addr = self.proxy_socket.accept()
            print("[!] 🖥️ ('%s', %s): has connected" % (addr[0], addr[1]))
            self.handle_client(client, addr)

    def handle_client(self, client, addr):
        """Handles the mechanics of a client connected to this server"""

        # Store the cache dictionary
        cache = self.cache.get()

        # Store client address + port
        client_addr = addr[0]
        client_port = addr[1]

        while 1:
            data = client.recv(self.BUFFER_SIZE)

            if not data:
                print("[!] 🖥 ('%s', %s): has disconnected" % (addr[0], addr[1]))

                client.close()
                sys.exit(0)  # When client disconnects, exit the program

            print("[!] DATA RECEIVED FROM CLIENT:\n------------\n%s\n------------" % str(data, 'iso-8859-1'))

            # Decode target byte-stream-data from client
            target_addr = self.decode(data)
            # Store target port information
            target_port = 80

            # Store the current time
            now = time.time()

            # Check if target exists within the cache
            if target_addr in cache:
                # Get the data attached to the target in the cache
                content = cache.get(target_addr)

                # Time that has elapsed since last retrieval of targets data
                delta = int(now - content.age)

                print("[!] %s seconds have elapsed since last retrieval of %s's data" % (delta, target_addr))

                # Check if the target in cache has gone stale after a minute
                # since last retrieval of its data
                if content.is_fresh():
                    # If the target exists and it has not gone stale,
                    # send the client the data attached to the target in the cache
                    print("[!] %s's has not aged, using cached data" % target_addr)
                    self.send_to_client(client, (client_addr, client_port), content.data)
                else:
                    # If the data's age of the target has expired then, update its data
                    # in the cache by reconnecting to target server and sending
                    # the header-less response back to the client
                    print("[!] %s's has aged, updating data" % target_addr)

                    # Send the data back to client
                    self.send_to_target('update', client, (client_addr, client_port), (target_addr, target_port))
            else:
                # If target is not in cache, then connect to target and send
                # the header-less response back to the client
                self.send_to_target('add', client, (client_addr, client_port), (target_addr, target_port))

    def decode(self, data):
        """Decodes a byte-stream to a string"""

        return data.decode('iso-8859-1')

    def get_response(self, target):
        """Listens and store the GET response from target server"""

        # Demuxify target tuple
        target_socket, target_addr, target_port = target

        response = ''

        while True:
            received = target_socket.recv(4096)
            response += received.decode('iso-8859-1')
            if len(received) == 0:
                break

        print("[!] RESPONSE FROM ('%s', %s):\n------------\n%s\n------------" % (target_addr, str(target_port), response))

        return response

    @staticmethod
    def send_to_client(client_socket, client, data):
        """Sends data to a specific client"""

        # Demuxify client tuple
        addr, port = client

        try:
            # Send the data back to client
            z = client_socket.send(str.encode(data))
            print("[!] Successfully sent %s bytes to ('%s', %s)" % (str(z), addr, port))
            print("[!] DATA SENT TO CLIENT:\n------------\n%s\n------------" % data)
        except:
            print("[X] Failed to send data to ('%s', %s)" % (addr, port))
            sys.exit(1)

    def send_to_target(self, method, client_socket, client, target):
        """Sends a GET request to a specific host & port and returns the header-less response
        to the client and stores that data within the cache along with the current time"""

        # Create target socket (e.g. a socket to 'www.google.com:80')
        target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Demuxify target tuple
        target_addr, target_port = target

        # If the target does not exist, then connect to the target server
        # and send the header-less response back to the client
        try:
            # Connect to the target server
            target_socket.connect((target_addr, target_port))
        except:
            print("[X] ('%s', %s) has failed to connect" % (target_addr, target_port))
            sys.exit(1)

        try:
            # Send the GET request to the target server
            header = str.encode("GET / HTTP/1.0\r\nHost: " + target_addr + "\r\nConnection: close\r\n\r\n")
            z = target_socket.send(header)
            print("[!] Successfully sent %s bytes to ('%s', %s)" % (str(z), target_addr, target_port))
            print("[!] DATA SENT TO ('%s', %s):\n------------\n%s\n------------" % (
                target_addr, target_port, header.decode('iso-8859-1')))
        except:
            print("[X] Failed to send data to ('%s', %s)" % (target_addr, target_port))
            sys.exit(1)

        # Listen and store the GET response from target server
        response = self.get_response((target_socket, target_addr, target_port))

        # Discard the header and store only the data from the response
        data = response.split('\r\n\r\n')[1]

        if method is 'add':
            # Add target to the cache
            self.cache.add(target_addr, data)
        elif method is 'update':
            # Update target within the cache
            self.cache.update(target_addr, data)
        else:
            print("[X] 'method' must be either 'add' or 'update'")
            sys.exit(1)

        # Send the data back to client
        self.send_to_client(client_socket, client, data)

        # Close the socket used by the proxy to the target
        target_socket.close()


class Content:
    """A representation of the header-less response
    from target server (payload-portion of the response)"""

    def __init__(self, data):
        self.data = data  # header-less response
        self.age = time.time()  # time added to cache

    def is_fresh(self):
        """Determines if the data is fresh"""

        return time.time() - self.age < 60


class Cache:
    def __init__(self):
        self.cache = {}

    def add(self, target_addr, data):
        """Adds an item to the cache"""

        # Add target + data (response) + current time to cache
        self.cache.update({target_addr: Content(data)})

        print("[!] %s has been added to the cache" % target_addr)

    def update(self, target_addr, data):
        """Adds an item to the cache"""

        # Add target + data (response) + current time to cache
        self.cache.update({target_addr: Content(data)})

        print("[!] Cache for %s has been updated" % target_addr)

    def get(self):
        """Returns the cache dictionary"""

        return self.cache


if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 1337

    PROXY = Proxy(HOST, PORT)
