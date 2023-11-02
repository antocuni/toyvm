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
        self.pc_to_skips = set()

    def run(self):
        for pc, op in enumerate(self.code.body):
            if pc in self.pc_to_skips:
                continue
            meth = getattr(self, f'op_{op.name}', self.op_default)
            meth(op, *op.args)

    def n_greens(self):
        return len(self.greenframe.stack)

    def flush(self):
        for w_value in self.greenframe.stack:
            self.out.emit(OpCode('load_const', w_value))
            self.stack_length += 1
        self.greenframe.stack = []

    def is_green(self, op):
        if not op.is_pure():
            return False
        pops = op.num_pops()
        return self.n_greens() >= pops

    def op_default(self, op, *args):
        if self.is_green(op):
            self.greenframe.run_op(op)
        else:
            self.flush()
            pops = op.num_pops()
            assert self.stack_length >= pops # sanity check
            self.stack_length -= pops
            self.stack_length += op.num_pushes()
            self.out.emit(op)

    def op_br_if(self, op, then_pc, else_pc, endif_pc):
        if self.n_greens() >= 1:
            # green case
            w_cond = self.greenframe.stack.pop()
            if w_cond.value:
                # skip the "else" branch
                self.pc_to_skips.update(range(else_pc, endif_pc))
            else:
                # skip the "then" branch
                self.pc_to_skips.update(range(then_pc, else_pc))
        else:
            # red case
            self.op_default(op, *op.args)
