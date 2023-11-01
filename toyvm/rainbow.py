from dataclasses import dataclass
from toyvm.objects import W_Object
from toyvm.opcode import CodeObject, OpCode
from toyvm.frame import Frame

def peval(code):
    """
    Perform partial evaluation on the given code object.

    Return a new code object where all green ops have been evaluated.  This is
    the main entry point for the rainbow interpreter.
    """
    interp = RainbowInterpreter(code)
    interp.run()
    return interp.out



class RainbowInterpreter:

    def __init__(self, code):
        self.code = code
        self.out = CodeObject(code.name + '<peval>', [])
        self.stack_length = 0
        self.greenframe = Frame(code)

    def run(self):
        for op in self.code.body:
            if self.is_green(op):
                self.greenframe.run_op(op)
            else:
                self.flush()
                pops = op.num_pops()
                assert self.stack_length >= pops # sanity check
                self.stack_length -= pops
                self.stack_length += op.num_pushes()
                self.out.emit(op)

    def flush(self):
        for w_value in self.greenframe.stack:
            self.out.emit(OpCode('load_const', w_value))
            self.stack_length += 1
        self.greenframe.stack = []

    def is_green(self, op):
        if not op.is_pure():
            return False
        pops = op.num_pops()
        return len(self.greenframe.stack) >= pops
