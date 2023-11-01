from toyvm.rainbow import peval
from toyvm.opcode import OpCode, CodeObject
from toyvm.objects import W_Int, W_Str

class TestRainbow:

    def test_simple(self):
        code = CodeObject('fn', [
            OpCode('load_local', 'a'),
            OpCode('load_local', 'b'),
            OpCode('add'),
        ])
        code2 = peval(code)
        assert code2.body == code.body
