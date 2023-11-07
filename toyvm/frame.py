import operator
from toyvm.objects import W_Object, W_Int, W_Str, W_Tuple, w_None

class Frame:

    def __init__(self, code):
        self.code = code
        self.locals = {}
        self.pc = 0
        self.stack = []

    def push(self, w_value):
        assert isinstance(w_value, W_Object)
        self.stack.append(w_value)

    def pop(self):
        return self.stack.pop()

    def popn(self, n):
        assert len(self.stack) >= n
        res = self.stack[-n:]
        self.stack[-n:] = []
        return res

    def run(self):
        while True:
            op = self.code.body[self.pc]
            # 'return' is special, handle it explicitly
            if op.name == 'return':
                n = len(self.stack)
                assert n == 1, f'Wrong stack size upon return: {n}'
                w_result = self.pop()
                return w_result
            else:
                self.run_op(op)
                self.pc += 1
                assert self.pc < len(self.code.body), 'no return?'

    def run_op(self, op):
        meth_name = f'op_{op.name}'
        meth = getattr(self, meth_name, None)
        if meth is None:
            raise NotImplementedError(meth_name)
        meth(*op.args)

    def op_load_const(self, w_value):
        self.push(w_value)

    def op_add(self):
        w_b = self.pop()
        w_a = self.pop()
        if w_a.type == w_b.type == 'int':
            w_c = W_Int(w_a.value + w_b.value)
        elif w_a.type == w_b.type == 'str':
            w_c = W_Str(w_a.value + w_b.value)
        else:
            assert False
        self.push(w_c)

    def op_mul(self):
        w_b = self.pop()
        w_a = self.pop()
        if w_a.type == w_b.type == 'int':
            w_c = W_Int(w_a.value * w_b.value)
        elif w_a.type == 'str' and w_b.type == 'int':
            w_c = W_Str(w_a.value * w_b.value)
        else:
            assert False
        self.push(w_c)

    def op_gt(self):
        self._op_compare(operator.gt)

    def op_lt(self):
        self._op_compare(operator.lt)

    def _op_compare(self, cmpfunc):
        w_b = self.pop()
        w_a = self.pop()
        if w_a.type == w_b.type:
            c = cmpfunc(w_a.value, w_b.value)
            w_c = W_Int(c)
        else:
            assert False
        self.push(w_c)

    def op_store_local(self, name):
        self.locals[name] = self.pop()

    def op_load_local(self, name):
        self.push(self.locals[name])

    op_store_local_green = op_store_local
    op_load_local_green = op_load_local

    def op_br(self, pc):
        self.pc = pc - 1

    def op_br_if(self, then_pc, else_pc, endif_pc):
        """
        branch if

        pop a value from the stack. If it's truthy, jump to then_pc, else
        jumpt to else_pc; endif_pc is not actually used at runtime, but it
        marks the end of the "else" branch: it's there only to make it easier
        to do static analysis on the bytecode (e.g. by the rainbow
        interpreter).
        """
        assert endif_pc >= else_pc
        w_cond = self.pop()
        assert w_cond.type == "int"
        if w_cond.value:
            self.pc = then_pc - 1
        else:
            self.pc = else_pc - 1

    def op_abort(self, msg):
        raise Exception(f"ABORT: {msg}")

    def op_make_tuple(self, n):
        items_w = self.popn(n)
        w_tuple = W_Tuple(items_w)
        self.push(w_tuple)

    def op_print(self, n):
        items_w = self.popn(n)
        strs = [w_item.str() for w_item in items_w]
        print(*strs)
        self.push(w_None)

    def op_pop(self):
        self.pop()

    def op_get_iter(self, itername):
        w_iterable = self.pop()
        w_iter = w_iterable.get_iter()
        self.locals[itername] = w_iter

    def op_for_iter(self, itername, targetname, endfor_pc):
        w_iter = self.locals[itername]
        w_value = w_iter.iter_next()
        if w_value == 'STOP':
            del self.locals[itername]
            self.pc = endfor_pc - 1
        else:
            self.locals[targetname] = w_value

    def op_unroll(self):
        w_value = self.pop()
        w_res = w_value.unroll()
        self.push(w_res)
