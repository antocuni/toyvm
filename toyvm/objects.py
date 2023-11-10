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
        return f'W_Str({self.value!r})'

    def str(self):
        return self.value


class Closure:

    def __init__(self, scopes):
        self.scopes = scopes

    def copy_and_append(self, ns_w):
        new_scopes = self.scopes + [ns_w]
        return Closure(new_scopes)

    def lookup(self, name):
        for ns_w in reversed(self.scopes):
            if name in ns_w:
                return ns_w[name]
        raise KeyError(name)

@dataclass
class W_Function(W_Object):
    type = 'function'
    is_green = False
    #
    name: str
    code: CodeObject
    closure: Closure

    def call(self, *args_w):
        from toyvm.frame import Frame
        frame = Frame(self)
        # setup parameters
        assert len(self.code.argnames) == len(args_w)
        for varname, w_arg in zip(self.code.argnames, args_w):
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

    def get_iter(self):
        return W_TupleIterator(self, unroll=False)

    def unroll(self):
        return W_TupleIterator(self, unroll=True)

@dataclass
class W_TupleIterator(W_Object):
    type = 'tuple_iterator'
    w_tuple: W_Tuple
    unroll: bool

    def __post_init__(self):
        self._iter = iter(self.w_tuple.items_w)

    def get_iter(self):
        return self

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


@dataclass
class W_Module(W_Object):
    type = 'module'
    globals_w: dict[str, W_Object]

    def get_closure(self):
        return Closure([self.globals_w])
