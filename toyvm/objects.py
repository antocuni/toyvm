from dataclasses import dataclass
from toyvm.opcode import CodeObject

class W_Object:
    type = 'object'

@dataclass
class W_Int(W_Object):
    type = 'int'
    value: int

    def __repr__(self):
        return f'W_Int({self.value})'

@dataclass
class W_Str(W_Object):
    type = 'str'
    value: str

    def __repr__(self):
        return f'W_Str({self.value})'


@dataclass
class W_Function(W_Object):
    type = 'function'
    name: str
    code: CodeObject

    def call(self):
        from toyvm.frame import Frame
        frame = Frame(self.code)
        return frame.run()
