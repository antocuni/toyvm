from toyvm.frame import Frame
from toyvm.opcode import OpCode, CodeObject
from toyvm.objects import W_Int, W_Str, W_Function

def make_Frame(code):
    w_func = W_Function(code.name, [], code, {})
    return Frame(w_func)

class TestFrame:

    def test_simple(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Int(2)),
            OpCode('load_const', W_Int(4)),
            OpCode('add'),
            OpCode('return')
        ])
        frame = make_Frame(code)
        w_res = frame.run()
        assert w_res == W_Int(6)

    def test_locals(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Int(2)),
            OpCode('store_local', 'a'),
            OpCode('load_local', 'a'),
            OpCode('return')
        ])
        frame = make_Frame(code)
        w_res = frame.run()
        assert w_res == W_Int(2)

    def test_add_str(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Str('hello ')),
            OpCode('load_const', W_Str('world')),
            OpCode('add'),
            OpCode('return')
        ])
        frame = make_Frame(code)
        w_res = frame.run()
        assert w_res == W_Str('hello world')

    def test_mul_int(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Int(2)),
            OpCode('load_const', W_Int(4)),
            OpCode('mul'),
            OpCode('return')
        ])
        frame = make_Frame(code)
        w_res = frame.run()
        assert w_res == W_Int(8)

    def test_mul_str(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Str('x')),
            OpCode('load_const', W_Int(4)),
            OpCode('mul'),
            OpCode('return')
        ])
        frame = make_Frame(code)
        w_res = frame.run()
        assert w_res == W_Str('xxxx')

    def test_br_if(self):
        code = CodeObject('fn', [
            OpCode('load_local', 'a'),
            OpCode('load_const', W_Int(0)),
            OpCode('gt'),
            OpCode('br_if', 'then_0', 'else_0', 'endif_0'),
            OpCode('label', 'then_0'),
            OpCode('load_const', W_Int(3)),
            OpCode('return'),
            OpCode('label', 'else_0'),
            OpCode('load_const', W_Int(4)),
            OpCode('return'),
            OpCode('label', 'endif_0'),
            OpCode('abort', "unreachable"),
        ])
        frame = make_Frame(code)
        frame.locals['a'] = W_Int(10)
        w_res = frame.run()
        assert w_res == W_Int(3)
        #
        frame = make_Frame(code)
        frame.locals['a'] = W_Int(-10)
        w_res = frame.run()
        assert w_res == W_Int(4)
