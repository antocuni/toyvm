from toyvm.frame import Frame
from toyvm.opcode import OpCode, CodeObject
from toyvm.objects import W_Int, W_Str

def test_simple():
    code = CodeObject([
        OpCode('load_const', W_Int(2)),
        OpCode('load_const', W_Int(4)),
        OpCode('add'),
        OpCode('return')
    ])
    frame = Frame(code)
    w_res = frame.run()
    assert w_res == W_Int(6)

def test_locals():
    code = CodeObject([
        OpCode('load_const', W_Int(2)),
        OpCode('store_local', 'a'),
        OpCode('load_local', 'a'),
        OpCode('return')
    ])
    frame = Frame(code)
    w_res = frame.run()
    assert w_res == W_Int(2)

def test_str_add():
    code = CodeObject([
        OpCode('load_const', W_Str('hello ')),
        OpCode('load_const', W_Str('world')),
        OpCode('add'),
        OpCode('return')
    ])
    frame = Frame(code)
    w_res = frame.run()
    assert w_res == W_Str('hello world')
