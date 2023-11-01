from dataclasses import dataclass

@dataclass
class OpCode:
    name: str
    args: tuple

    def __init__(self, name: str, *args):
        self.name = name
        self.args = args

    def __repr__(self):
        if self.args:
            return f'<OpCode {self.name} {list(self.args)}>'
        else:
            return f'<OpCode {self.name}>'


class CodeObject:

    def __init__(self, name, body):
        self.name = name
        self.body = body

    def emit(self, op):
        self.body.append(op)
