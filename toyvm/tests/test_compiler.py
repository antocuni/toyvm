from toyvm.compiler import toy_compile

def test_simple():
    code = toy_compile("""
    def fn():
        return 42
    """)
    assert code.equals("""
    load_const W_Int(42)
    return
    """)
