from socket import socket
from json import JSONEncoder
from typing import Any


class person:
     def __init__(self, name: str, socket: socket, personal_id: str, token: str):
          self.name = name
          self.socket = socket
          self.personal_id = personal_id
          self.token = token

class personEncoder(JSONEncoder):
    def default(self, p: Any) -> Any:
        if isinstance(p, person):
            return dict(name=p.name, personal_id=p.personal_id, token=p.token)
        return super(self, p)
        