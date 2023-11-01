from dataclasses import dataclass

class W_Object:
    type = 'object'

@dataclass
class W_Int(W_Object):
    type = 'int'
    value: int

@dataclass
class W_Str(W_Object):
    type = 'str'
    value: str
