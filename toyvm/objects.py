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
    argnames: list[str]
    code: CodeObject

    def call(self, *args_w):
        from toyvm.frame import Frame
        frame = Frame(self.code)
        # setup parameters
        assert len(self.argnames) == len(args_w)
        for varname, w_arg in zip(self.argnames, args_w):
            frame.locals[varname] = w_arg
        #
        return frame.run()
