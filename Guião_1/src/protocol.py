"""Protocol for chat server - Computação Distribuida Assignment 1."""
import json
from datetime import datetime
from socket import socket

class Message:
    """Message Type."""
    def __init__(self,command) -> None:
        self.command = command
    
class JoinMessage(Message):
    """Message to join a chat channel."""
    def __init__(self,channel) -> None:
        super().__init__("join")
        self.channel = channel

    def __repr__(self) -> str:
        data = {"command": "join", "channel": self.channel}
        return json.dumps(data)

class RegisterMessage(Message):
    """Message to register username in the server."""
    def __init__(self,user) -> None:
        super().__init__("register")
        self.user = user

    def __repr__(self) -> str:
        data = {"command": "register", "user": self.user}
        return json.dumps(data)
    
class TextMessage(Message):
    """Message to chat with other clients."""
    def __init__(self, message, channel=None, ts=None) -> None:
        super().__init__("message")
        self.message = message
        self.channel = channel

        # If timestamp not given, use current time
        if ts == None: 
            self.ts = int(datetime.now().timestamp())
        else:
            self.ts = ts

    def __repr__(self) -> str:
        # If channel not given, send message to main channel
        if self.channel == None :
            data = {"command": "message", "message": self.message,"ts":self.ts}
            return json.dumps(data)
        else:
            data = {"command": "message", "message": self.message, "channel":self.channel,"ts":self.ts}
            return json.dumps(data)


class CDProto:
    """Computação Distribuida Protocol."""

    @classmethod
    def register(cls, username: str) -> RegisterMessage:
        """Creates a RegisterMessage object."""
        return RegisterMessage(username)

    @classmethod
    def join(cls, channel: str) -> JoinMessage:
        """Creates a JoinMessage object."""
        return JoinMessage(channel)

    @classmethod
    def message(cls, message: str, channel: str = None) -> TextMessage:
        """Creates a TextMessage object."""
        return TextMessage(message, channel)

    @classmethod
    def send_msg(cls, connection: socket, message: Message):
        """Sends through a connection a Message object."""

        message = str(message)

        size = len(message).to_bytes(2,"big")

        messageEncoded = message.encode('utf-8')

        connection.send(size + messageEncoded)

    @classmethod
    def recv_msg(cls, connection: socket) -> Message:
        """Receives through a connection a Message object."""

        messageSize = int.from_bytes(connection.recv(2),'big')

        if messageSize != 0:
            message = connection.recv(messageSize).decode('utf-8')

            try:
                message = json.loads(message)

                if "command" not in message.keys():
                    raise CDProtoBadFormat(message)
            except Exception:
                raise CDProtoBadFormat(message)

            command = message["command"]

            options = {
                "join": CDProto.join_message,
                "register": CDProto.register_message,
                "message": CDProto.text_message
            }

            # Get the message class from switcher dictionary
            return options[command](connection, message)
        else:
            return 

    
    @classmethod
    def join_message(cls, connection: socket, message: Message):
        if "channel" not in message.keys():
            raise CDProtoBadFormat(message)
        return JoinMessage(message["channel"])

    @classmethod
    def register_message(cls, connection: socket, message: Message):
        if "user" not in message.keys():
            raise CDProtoBadFormat(message)
        return RegisterMessage(message["user"])

    @classmethod
    def text_message(cls, connection: socket, message: Message):
        if "message" not in message.keys() or "ts" not in message.keys():
            raise CDProtoBadFormat(message)
        
        ts = int(message["ts"])
        text = message["message"]

        # If channel not given, export message to main channel
        if "channel" not in message.keys():
            return TextMessage(text,ts)
        
        channel = message["channel"]
        return TextMessage(text, channel, ts)


class CDProtoBadFormat(Exception):
    """Exception when source message is not CDProto."""

    def __init__(self, original_msg: bytes=None) :
        """Store original message that triggered exception."""
        self._original = original_msg

    @property
    def original_msg(self) -> str:
        """Retrieve original message as a string."""
        return self._original.decode("utf-8")
