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

    def str(self):
        return str(self.value)

@dataclass
class W_Str(W_Object):
    type = 'str'
    value: str

    def __repr__(self):
        return f'W_Str({self.value})'

    def str(self):
        return self.value


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

    def str(self):
        return f"<toy function '{self.name}'>"


@dataclass
class W_Tuple(W_Object):
    type = 'tuple'
    items_w: list[W_Object]

    def str(self):
        parts = [w_item.str() for w_item in self.items_w]
        return '(%s)' % ', '.join(parts)


@dataclass
class W_NoneType(W_Object):
    type = 'NoneType'

    def __repr__(self):
        return 'w_None'

    def str(self):
        return '<toy None>'

w_None = W_NoneType()
