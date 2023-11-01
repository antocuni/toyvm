from toyvm.frame import Frame
from toyvm.opcode import OpCode, CodeObject
from toyvm.objects import W_Int, W_Str

class TestFrame:

    def test_simple(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Int(2)),
            OpCode('load_const', W_Int(4)),
            OpCode('add'),
            OpCode('return')
        ])
        frame = Frame(code)
        w_res = frame.run()
        assert w_res == W_Int(6)

    def test_locals(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Int(2)),
            OpCode('store_local', 'a'),
            OpCode('load_local', 'a'),
            OpCode('return')
        ])
        frame = Frame(code)
        w_res = frame.run()
        assert w_res == W_Int(2)

    def test_add_str(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Str('hello ')),
            OpCode('load_const', W_Str('world')),
            OpCode('add'),
            OpCode('return')
        ])
        frame = Frame(code)
        w_res = frame.run()
        assert w_res == W_Str('hello world')

    def test_mul_int(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Int(2)),
            OpCode('load_const', W_Int(4)),
            OpCode('mul'),
            OpCode('return')
        ])
        frame = Frame(code)
        w_res = frame.run()
        assert w_res == W_Int(8)

    def test_mul_str(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Str('x')),
            OpCode('load_const', W_Int(4)),
            OpCode('mul'),
            OpCode('return')
        ])
        frame = Frame(code)
        w_res = frame.run()
        assert w_res == W_Str('xxxx')
