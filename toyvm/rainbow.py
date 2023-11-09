from dataclasses import dataclass
from toyvm.objects import W_Object, W_Function
from toyvm.opcode import CodeObject, OpCode
from toyvm.frame import Frame

def peval(w_func):
    """
    Perform partial evaluation on the given function object.

    Return a new function object where all green ops have been evaluated.
    This is the main entry point for the rainbow interpreter.
    """
    interp = RainbowInterpreter(w_func)
    interp.run()
    code2 = interp.out
    return W_Function(
        name = w_func.name,
        argnames = w_func.argnames,
        code = code2,
        globals_w = w_func.globals_w)


class RainbowInterpreter:

    def __init__(self, w_func):
        self.w_func = w_func
        self.code = w_func.code
        self.out = CodeObject(self.code.name + '<peval>', [])
        self.stack_length = 0
        self.greenframe = Frame(w_func)
        #
        self.label_maps = []
        self.unique_id = 0

    def push_label_map(self, pc_start, pc_end):
        """
        Search for all 'label' opcodes inside the given range, and create a
        mapping to give them unique names. This is needed .g. to unroll a
        loop, because we need unique labels for each iteration.
        """
        newid = self.unique_id
        self.unique_id += 1
        m = {}
        for pc in range(pc_start, pc_end):
            op = self.code.body[pc]
            if op.name == 'label':
                label = op.args[0]
                m[label] = f'{label}#{newid}'
        self.label_maps.append(m)

    def pop_label_map(self):
        self.label_maps.pop()

    def emit(self, op):
        if self.label_maps:
            op = op.relabel(self.label_maps[-1])
        self.out.emit(op)

    def get_pc(self, label):
        """
        Get the PC corresponding to the given named label
        """
        return self.greenframe.labels[label]

    def get_pcs(self, *labels):
        """
        Same as get_pc, but for multiple labels
        """
        return [self.get_pc(l) for l in labels]

    def run(self):
        """
        Do abstract interpretation of the whole code
        """
        self.run_range(0, len(self.code.body))

    def run_range(self, pc_start, pc_end):
        """
        Do abstract interpretation of the given code range
        """
        pc = pc_start
        while pc < pc_end:
            pc = self.run_single_op(pc)
        self.flush()

    def run_single_op(self, pc):
        """
        Do abstract interpretation of the op at the given PC.

        Return the PC of the operation to execute next.
        """
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
            self.push_label_map(pc+1, pc_br)
            self.run_range(pc+1, pc_br)
            self.pop_label_map()
        #
        return pc_endfor+1
