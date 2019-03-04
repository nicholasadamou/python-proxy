import socket
import sys
import time


class Client:
    BUFFER_SIZE = 20  # Fast response
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Client Socket

    def __init__(self, addr, port):
        self.addr = addr
        self.port = port

        # Set a brief wait time until data or socket connects
        # If wait time expires, then timeout the socket
        self.client_socket.settimeout(10)

        try:
            # Connect to the proxy-server
            self.client_socket.connect((self.addr, self.port))
            print("[!] 🖥️ ('%s', %s): has connected" % (str(self.addr), str(self.port)))
        except:
            print("[X] Failed to send data to ('%s', %s)" % (str(self.addr), str(self.port)))
            sys.exit(1)

    def send(self, data):
        """Sends data to the proxy server"""

        try:
            # Send the GET request
            print("[!] DATA SENT TO PROXY-SERVER:\n------------\n%s\n------------" % str(data, 'iso-8859-1'))
            self.client_socket.send(data)
        except:
            print("[X] Failed to send data to ('%s', %s)" % (str(self.addr), str(self.port)))
            sys.exit(1)

    def recv(self):
        """Retrieves and stores the GET response from the proxy-server"""

        # Store the GET response from the proxy-server
        response = self.client_socket.recv(64536).decode('iso-8859-1')
        print("[!] RESPONSE FROM PROXY-SERVER:\n------------\n%s\n------------" % response)


if __name__ == '__main__':
    HOST = '127.0.0.1'
    PORT = 1337

    CLIENT = Client(HOST, PORT)

    # Send target host-address to proxy-server
    TARGET = 'www.google.com'
    CLIENT.send(str.encode(TARGET))

    # Receive data from proxy-server
    CLIENT.recv()

    # Wait 30 seconds
    time.sleep(30)  # Now Time = 30 < 60 seconds (aged content)s

    # ----------------------------------------
    # Prove that cache sends back cached data
    # ----------------------------------------

    # Send target host-address to proxy-server
    TARGET = 'www.google.com'
    CLIENT.send(str.encode(TARGET))

    # Receive data from proxy-server
    CLIENT.recv()

    # Wait 30 seconds
    time.sleep(35)  # Now Time = 30 + 35 = 65 seconds > 60 seconds (aged content)

    # ----------------------------------------
    # Prove that after time expires, the proxy-server
    # reconnects to the target
    # ----------------------------------------

    # Send target host-address to proxy-server
    TARGET = 'www.google.com'
    CLIENT.send(str.encode(TARGET))

    # Receive data from proxy-server
    CLIENT.recv()

    # Wait 30 seconds
    time.sleep(30)

    # ----------------------------------------

    # Send target host-address to proxy-server
    TARGET = 'www.yahoo.com'
    CLIENT.send(str.encode(TARGET))

    # Receive data from proxy-server
    CLIENT.recv()

    # Wait 30 seconds
    time.sleep(30)

    # ----------------------------------------

    # Send target host-address to proxy-server
    TARGET = 'www.uiowa.edu'
    CLIENT.send(str.encode(TARGET))

    # Receive data from proxy-server
    CLIENT.recv()

    # ----------------------------------------

    # Close the client socket
    CLIENT.client_socket.close()


