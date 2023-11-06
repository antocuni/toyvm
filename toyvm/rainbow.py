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

    @property
    def out_pc(self):
        return len(self.out.body)

    def record_pcmap(self, in_pc):
        self.pcmap[in_pc] = self.out_pc

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

    def run(self):
        self.run_range(0, len(self.code.body))
        self.fix_pcs()

    def run_range(self, pc_start, pc_end):
        pc = pc_start
        while pc < pc_end:
            pc = self.run_single_op(pc)
        self.flush()

    def run_single_op(self, pc):
        op = self.code.body[pc].copy()
        meth = getattr(self, f'op_{op.name}', self.op_default)
        pc_next = meth(op, *op.args)
        if pc_next is None:
            return pc + 1
        else:
            assert type(pc_next) is int
            return pc_next

    def fix_pcs(self):
        def tr(*pcs):
            return map(self.pcmap.__getitem__, pcs)

        for i, op in enumerate(self.out.body):
            if op.name == 'br':
                import pdb;pdb.set_trace()
            elif op.name == 'br_if':
                then_pc, else_pc, endif_pc = tr(*op.args)
                op.replace_args(then_pc, else_pc, endif_pc)
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

    def op_default(self, op, *args):
        if self.is_green(op):
            return self.op_green(op, *args)
        else:
            return self.op_red(op, *args)

    def op_green(self, op, *args):
        self.greenframe.run_op(op)

    def op_red(self, op, *args):
        self.flush()
        pops = op.num_pops()
        assert self.stack_length >= pops # sanity check
        self.stack_length -= pops
        self.stack_length += op.num_pushes()
        self.emit(op)

    def op_load_local_green(self, op, varname):
        return self.op_green(op, varname)

    def op_store_local_green(self, op, varname):
        assert self.n_greens() >= 1, 'store_local_green called on a red'
        return self.op_green(op, varname)

    def op_br_if(self, op, then_pc, else_pc, endif_pc):
        if self.n_greens() >= 1:
            # green case
            w_cond = self.greenframe.stack.pop()
            if w_cond.value:
                self.run_range(then_pc, else_pc)
            else:
                self.run_range(else_pc, endif_pc)
            return endif_pc
        else:
            self.op_red(op, *op.args) # emit br_if
            self.record_pcmap(then_pc)
            #
            self.run_range(then_pc, else_pc)
            self.record_pcmap(else_pc)
            #
            self.run_range(else_pc, endif_pc)
            self.record_pcmap(endif_pc)
            #
            return endif_pc

    def op_get_iter(self, op, itername):
        is_red = self.n_greens() < 1 or not self.greenframe.stack[-1].unroll
        if is_red:
            return self.op_red(op, itername)
        else:
            return self.op_green(op, itername)

    def op_for_iter(self, op, itername, targetname, endfor_pc):
        w_iter = self.greenframe.locals.get(itername)
        if w_iter is None:
            # this is a non-unrolling for
            # XXX implement me
            import pdb;pdb.set_trace()
        else:
            return self.op_unroll_for_iter(op, itername, targetname, endfor_pc,
                                           w_iter)

    def op_unroll_for_iter(self, op, itername, targetname, endfor_pc, w_iter):
        assert w_iter.unroll
        assert targetname.isupper()
        PC = 5 # XXX this is hardcoded
        #
        br_pc = endfor_pc - 1
        assert self.code.body[br_pc].name == 'br' # op to loop back
        #
        for w_item in w_iter._iter:
            self.greenframe.locals[targetname] = w_item
            self.run_range(PC+1, br_pc)

        return endfor_pc
