from dataclasses import dataclass
from toyvm.objects import W_Object
from toyvm.opcode import CodeObject

def peval(code):
    """
    Perform partial evaluation on the given code object.

    Return a new code object where all green ops have been evaluated.  This is
    the main entry point for the rainbow interpreter.
    """
    interp = RainbowInterpreter(code)
    interp.run()
    return interp.out


class AbstractVar:
    color = None

@dataclass
class Green(AbstractVar):
    color = 'green'
    w_const: W_Object


class Red(AbstractVar):
    color = 'red'


class RainbowInterpreter:

    def __init__(self, code):
        self.code = code
        self.out = CodeObject(code.name + '<peval>', [])
        self.vstack = []

    def run(self):
        for op in self.code.body:
            meth = getattr(self, f'op_{op.name}')
            meth(op, *op.args)

    def push(self, var):
        self.vstack.append(var)

    def pop(self, expected_color):
        w_val = self.vstack.pop()
        assert w_val.color == expected_color
        return w_val

    def op_load_local(self, op, varname):
        self.push(Red())
        self.out.emit(op)

    def op_add(self, op):
        self.pop('red')
        self.pop('red')
        self.push(Red())
        self.out.emit(op)
