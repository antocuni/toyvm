from toyvm.rainbow import peval
from toyvm.opcode import OpCode, CodeObject
from toyvm.objects import W_Int, W_Str
from toyvm.compiler import toy_compile

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

    def test_green_br_if(self):
        code = CodeObject('fn', [
            OpCode('load_const', W_Int(1)),  # 0
            OpCode('br_if', 2, 4, 6),        # 1
            OpCode('load_const', W_Int(2)),  # 2 "then"
            OpCode('return'),                # 3
            OpCode('load_const', W_Int(3)),  # 4 "else"
            OpCode('return'),                # 5
            OpCode('abort', 'unreachable')   # 6 "endif"
        ])
        code2 = peval(code)
        assert code2.body == [
            OpCode('load_const', W_Int(2)),
            OpCode('return'),
            OpCode('abort', 'unreachable'),
        ]

    def test_red_br_if(self):
        code = CodeObject('fn', [
            OpCode('load_local', 'a'),       # 0
            OpCode('br_if', 2, 4, 6),        # 1
            OpCode('load_const', W_Int(2)),  # 2 "then"
            OpCode('return'),                # 3
            OpCode('load_const', W_Int(3)),  # 4 "else"
            OpCode('return'),                # 5
            OpCode('abort', 'unreachable')   # 6 "endif"
        ])
        code2 = peval(code)
        assert code2.body == code.body
