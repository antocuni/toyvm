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

    def emit(self, op):
        self.out.emit(op)

    def run(self):
        self.run_range(0, len(self.code.body))

    def run_range(self, pc_start, pc_end):
        pc = pc_start
        while pc < pc_end:
            pc = self.run_single_op(pc)
        self.flush()

    def run_single_op(self, pc):
        op = self.code.body[pc].copy()
        meth = getattr(self, f'op_{op.name}', self.op_default)
        pc_next = meth(pc, op, *op.args)
        if pc_next is None:
            return pc + 1
        else:
            assert type(pc_next) is int
            return pc_next

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

    def op_default(self, pc, op, *args):
        if self.is_green(op):
            return self.op_green(pc, op, *args)
        else:
            return self.op_red(pc, op, *args)

    def op_green(self, pc, op, *args):
        self.greenframe.run_op(op)

    def op_red(self, pc, op, *args):
        self.flush()
        pops = op.num_pops()
        assert self.stack_length >= pops # sanity check
        self.stack_length -= pops
        self.stack_length += op.num_pushes()
        self.emit(op)

    def op_load_local_green(self, pc, op, varname):
        return self.op_green(pc, op, varname)

    def op_store_local_green(self, pc, op, varname):
        assert self.n_greens() >= 1, 'store_local_green called on a red'
        return self.op_green(pc, op, varname)

    def get_pc(self, label):
        return self.greenframe.labels[label]

    def get_pcs(self, *labels):
        return [self.get_pc(l) for l in labels]

    def op_br_if(self, pc, op, then, else_, endif):
        pc_then, pc_else, pc_endif = self.get_pcs(then, else_, endif)
        if self.n_greens() >= 1:
            # green case
            w_cond = self.greenframe.stack.pop()
            if w_cond.value:
                self.run_range(pc_then, pc_else)
            else:
                self.run_range(pc_else, pc_endif)
            return pc_endif
        else:
            self.op_red(pc, op, *op.args) # emit br_if
            self.run_range(pc_then, pc_endif)
            return pc_endif

    def op_get_iter(self, pc, op, itername):
        is_red = self.n_greens() < 1 or not self.greenframe.stack[-1].unroll
        if is_red:
            return self.op_red(pc, op, itername)
        else:
            return self.op_green(pc, op, itername)

    def op_unroll(self, pc, op):
        assert self.n_greens() >= 1, 'UNROLL() called on a red variable'
        return self.op_green(pc, op)

    def op_for_iter(self, pc, op, itername, targetname, endfor):
        pc_endfor = self.get_pc(endfor)
        w_iter = self.greenframe.locals.get(itername)
        if w_iter is None:
            self.op_red(pc, op, *op.args)
            self.run_range(pc+1, pc_endfor)
            return pc_endfor
        else:
            return self.op_unroll_for_iter(pc, op, itername, targetname,
                                           endfor, w_iter)

    def op_unroll_for_iter(self, pc, op, itername, targetname,
                           endfor, w_iter):
        pc_endfor = self.get_pc(endfor)
        assert w_iter.unroll
        assert targetname.isupper()
        pc_br = pc_endfor - 1
        assert self.code.body[pc_br].name == 'br' # op to loop back
        #
        for w_item in w_iter._iter:
            self.greenframe.locals[targetname] = w_item
            self.run_range(pc+1, pc_br)
        #
        return pc_endfor
