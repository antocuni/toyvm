from toyvm.rainbow import peval
from toyvm.opcode import OpCode, CodeObject
from toyvm.objects import W_Int, W_Str

class TestRainbow:

    def test_simple(self):
        code = CodeObject('fn', [
            OpCode('load_local', 'a'),
            OpCode('load_local', 'b'),
            OpCode('add'),
            OpCode('return'),
        ])
        code2 = peval(code)
        assert code2.body == code.body

    def test_green_op(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Int(1)),
            OpCode('load_const', W_Int(2)),
            OpCode('add'),
            OpCode('return'),
        ])
        code2 = peval(code)
        assert code2.body == [
            OpCode('load_const', W_Int(3)),
            OpCode('return'),
        ]

    def test_red_green_green(self):
        code = CodeObject('fn', [
            OpCode('load_local', 'a'),
            OpCode('load_const', W_Int(2)),
            OpCode('load_const', W_Int(3)),
            OpCode('mul'),
            OpCode('add'),
            OpCode('return'),
        ])
        code2 = peval(code)
        assert code2.body == [
            OpCode('load_local', 'a'),
            OpCode('load_const', W_Int(6)),
            OpCode('add'),
            OpCode('return'),
        ]

    def test_green_red_op(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Int(1)),
            OpCode('load_local', 'a'),
            OpCode('add'),
            OpCode('load_const', W_Int(2)),
            OpCode('mul'),
            OpCode('return'),
        ])
        code2 = peval(code)
        assert code2.body == code.body
