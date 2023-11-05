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
        self.pcmap = {} # maps code PCs to out PCs

    def emit(self, op):
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

    def skip_pcs(self, start, end):
        for pc in range(start, end):
            self.pcmap[pc] = 'SKIP'

    def should_skip(self, pc):
        return self.pcmap.get(pc) == 'SKIP'

    def run(self):
        for pc, op in enumerate(self.code.body):
            if self.should_skip(pc):
                continue
            # find the appropriate op_* method
            meth = getattr(self, f'op_{op.name}', None)
            if meth is None:
                if self.is_green(op):
                    meth = self.op_default_green
                else:
                    meth = self.op_default_red
            #
            is_green = meth(op, *op.args)
            assert type(is_green) is bool
            pc_out = len(self.out.body)
            if is_green:
                # op was optimized away, so it's not present in outcode. It's
                # pc corresponds to the pc of the NEXT non-green op which will
                # be emitted
                self.pcmap[pc] = pc_out
            else:
                # op emitted to outcode, just use its PC.
                self.pcmap[pc] = pc_out - 1
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

    def op_default_green(self, op, *args):
        self.greenframe.run_op(op)
        return True

    def op_default_red(self, op, *args):
        self.flush()
        pops = op.num_pops()
        assert self.stack_length >= pops # sanity check
        self.stack_length -= pops
        self.stack_length += op.num_pushes()
        self.emit(op)
        return False

    def op_load_local_green(self, op, varname):
        return self.op_default_green(op, varname)

    def op_store_local_green(self, op, varname):
        assert self.n_greens() >= 1, 'store_local_green called on a red'
        return self.op_default_green(op, varname)

    def op_br_if(self, op, then_pc, else_pc, endif_pc):
        if self.n_greens() >= 1:
            # green case
            w_cond = self.greenframe.stack.pop()
            if w_cond.value:
                self.skip_pcs(else_pc, endif_pc) # skip the "else" branch
            else:
                self.skip_pcs(then_pc, else_pc)  # skip the "then" branch
            return True
        else:
            return self.op_default_red(op, *op.args)
