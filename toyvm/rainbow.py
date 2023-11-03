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
    #interp.print_pcmap()
    return interp.out



class RainbowInterpreter:

    def __init__(self, code):
        self.code = code
        self.out = CodeObject(code.name + '<peval>', [])
        self.stack_length = 0
        self.greenframe = Frame(code)
        self.pc_to_skips = set()
        self.pcmap = {} # maps code PCs to out PCs

    def emit(self, op):
        self.pcmap[self.pc] = self.pc_out()
        self.out.emit(op)

    def print_pcmap(self):
        print('original')
        self.code.pp()
        print()
        print('peval')
        self.out.pp()
        print()
        print('pcmap')
        for a, b in self.pcmap.items():
            print(f'{a} -> {b}')

    def run(self):
        for pc, op in enumerate(self.code.body):
            if pc in self.pc_to_skips:
                continue
            self.pc = pc
            meth = getattr(self, f'op_{op.name}', self.op_default)
            meth(op, *op.args)
        self.fix_pcs()

    def fix_pcs(self):
        for i, op in enumerate(self.out.body):
            if op.name == 'br':
                import pdb;pdb.set_trace()
            elif op.name == 'br_if':
                then_pc, else_pc, endif_pc = op.args
                then_pc = self.pcmap[then_pc]
                else_pc = self.pcmap[else_pc]
                endif_pc = self.pcmap[endif_pc]
                newop = OpCode(op.name, then_pc, else_pc, endif_pc)
                self.out.body[i] = newop
            elif op.name == 'for_iter':
                import pdb;pdb.set_trace()

    def n_greens(self):
        return len(self.greenframe.stack)

    def pc_out(self):
        return len(self.out.body)

    def flush(self):
        for w_value in self.greenframe.stack:
            self.emit(OpCode('load_const', w_value))
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
            self.pcmap[self.pc] = self.pc_out()
        else:
            self.flush()
            pops = op.num_pops()
            assert self.stack_length >= pops # sanity check
            self.stack_length -= pops
            self.stack_length += op.num_pushes()
            self.emit(op)

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
