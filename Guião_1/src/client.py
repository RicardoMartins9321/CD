import selectors
import socket
import sys
import fcntl
import os
import logging
from .protocol import CDProto, RegisterMessage, JoinMessage, TextMessage

logging.basicConfig(filename='client.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


class Client:
    def __init__(self, name, host="localhost", port=5050):
        self.name = name
        self.host = host
        self.port = port
        self.channel = "main"
        self.running = True

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        #self.socket.setblocking(False)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.socket, selectors.EVENT_READ, self.receive_message)
        self.selector.register(sys.stdin, selectors.EVENT_READ, self.send_message)


    def connect(self):
        self.socket.connect_ex((self.host, self.port))
        
        # Non-blocking stdin setup
        orig_fl = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
        fcntl.fcntl(sys.stdin, fcntl.F_SETFL, orig_fl | os.O_NONBLOCK)

        CDProto.send_msg(self.socket, RegisterMessage(self.name))
        logging.debug(f'Registered as {self.name}')


    def receive_message(self, conn):
        others_messages = CDProto.recv_msg(conn)
        command = others_messages.command
        
        if command == "message":
            print("<", others_messages.message)
            logging.debug('received "%s', others_messages.message)



    def send_message(self, conn):
        try:
            message = sys.stdin.readline().strip()
            if message:
                sys.stdout.flush()
                if message.startswith("/join"):
                    self.channel = message.split(' ', 1)[1] if ' ' in message else 'main'
                    CDProto.send_msg(self.socket, JoinMessage(self.channel))
                elif message.lower() == "exit":
                    self.running = False
                    return
                else:
                    CDProto.send_msg(self.socket, TextMessage(message, self.channel))
                    logging.debug('sent "%s', message)

        except Exception as e:
            logging.error(f"Failed to send message: {e}")
            self.running = False


    def loop(self):
        while self.running:
            events = self.selector.select()
            for key, _ in events:
                callback = key.data
                callback(key.fileobj)
        self.socket.close()
