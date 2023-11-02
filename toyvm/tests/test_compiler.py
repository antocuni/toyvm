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
