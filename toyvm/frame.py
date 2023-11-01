from toyvm.objects import W_Object, W_Int, W_Str

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

    def op_store_local(self, name):
        self.locals[name] = self.pop()

    def op_load_local(self, name):
        self.push(self.locals[name])
