from dataclasses import dataclass
from toyvm.opcode import CodeObject

class W_Object:
    type = 'object'

    def get_iter(self):
        raise TypeError(f"cannot call get_iter on instances of '{self.type}'")


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
    _unroll = False

    def str(self):
        parts = [w_item.str() for w_item in self.items_w]
        return '(%s)' % ', '.join(parts)

    def get_iter(self):
        return W_TupleIterator(self, self._unroll)

    def mark_unroll(self):
        self._unroll = True


@dataclass
class W_TupleIterator(W_Object):
    type = 'tuple_iterator'
    w_tuple: W_Tuple
    unroll: bool

    def __post_init__(self):
        self._iter = iter(self.w_tuple.items_w)

    def iter_next(self):
        return next(self._iter, 'STOP')


@dataclass
class W_NoneType(W_Object):
    type = 'NoneType'

    def __repr__(self):
        return 'w_None'

    def str(self):
        return '<toy None>'

w_None = W_NoneType()
