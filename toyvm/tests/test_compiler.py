from toyvm.compiler import toy_compile
from toyvm.objects import W_Int

def test_simple():
    w_func = toy_compile("""
    def foo():
        return 42
    """)
    assert w_func.code.equals("""
    load_const W_Int(42)
    return
    """)
    assert w_func.call() == W_Int(42)

def test_add_mul():
    w_func = toy_compile("""
    def foo():
        return 1 + 2 * 3
    """)
    assert w_func.code.equals("""
    load_const W_Int(1)
    load_const W_Int(2)
    load_const W_Int(3)
    mul
    add
    return
    """)
    assert w_func.call() == W_Int(7)
