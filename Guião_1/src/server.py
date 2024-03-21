import selectors
import socket
import logging
import json

from .protocol import CDProto, CDProtoBadFormat 

logging.basicConfig(filename="server.log", level=logging.DEBUG)


class Server:
    def __init__(self, host="localhost", port=5050):
        self._host = host
        self._port = port
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._host, self._port))
        self._socket.listen()
        self._selector = selectors.DefaultSelector()
        self._selector.register(self._socket, selectors.EVENT_READ, self._accept_connection)
        self.channels = {"main": []}


    def _accept_connection(self, server_socket):
        client_socket, address = server_socket.accept()
        print(f"Registering new client from {address}")

        message = CDProto.recv_msg(client_socket)
        logging.debug('received "%s', message)
        client_socket.setblocking(False)

        self.channels["main"].append(client_socket)
        self._selector.register(client_socket, selectors.EVENT_READ, self._receive_message)

        
    def _receive_message(self, client_socket_conn):
        try:
            message = CDProto.recv_msg(client_socket_conn)
            logging.debug('received "%s', message)

            if message != None:
                command = message.command
                channel = message.channel


                # Create the dictionary options that contains commands and their respective functions
                options = {
                    "join": self.handle_join,
                    "message": self._broadcast_message
                }

                # Verify if the command is in the dictionary
                options[command](client_socket_conn, message)

            else:  # If None client has disconnected
                self._disconnect(client_socket_conn)
                
        except CDProtoBadFormat:
            print("Bad format")


    def handle_join(self, client_socket, message):
        if message.channel not in self.channels:
            self.channels[message.channel] = []

        if client_socket not in self.channels[message.channel]:
            self.channels[message.channel].append(client_socket)


    def _broadcast_message(self, client_socket_conn, message):
        for client in self.channels[message.channel]:
            try:
                CDProto.send_msg(client, message)
                logging.debug('sent "%s', message)
            except Exception as e:
                logging.error(f"Error sending message: {e}")
                self._disconnect(client)
            


    def _disconnect(self, client):
        self.channels = {channel: [conn for conn in connections if conn not in self.channels[channel]] for channel, connections in self.channels.items()}

        logging.info(f"Disconnecting client {client}")
        self._selector.unregister(client)
        client.close()
        channel = self.channels.pop(client, None)
        if channel:
            self.channels[channel].remove(client)


    def loop(self):
        print(f"Server listening on {self._host}:{self._port}")
        try:
            while True:
                events = self._selector.select(timeout=None)
                for key, _ in events:
                    callback = key.data
                    callback(key.fileobj)
        except KeyboardInterrupt:
            print("Server stopped manually.")
        finally:
            self._socket.close()
