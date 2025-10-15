import pytest
from types import SimpleNamespace

def test_dispatch_reentrancy_raises():
    """
    Ensure TokenWarehouse dispatch_all() is not reentrant.
    A collector that attempts to call wh.dispatch_all() inside on_token() should trigger RuntimeError.
    """
    try:
        import importlib
        wh_mod = importlib.import_module("doxstrux.markdown.utils.token_warehouse")
    except Exception:
        pytest.skip("token_warehouse module not importable")

    TokenWarehouse = getattr(wh_mod, "TokenWarehouse", None)
    if TokenWarehouse is None:
        pytest.skip("TokenWarehouse class not available")

    class Tok:
        type = "inline"
        nesting = 0
        tag = ""
        map = None
        info = None
        content = "x"
        def attrGet(self, name):
            return None

    tokens = [Tok()]
    wh = TokenWarehouse(tokens, tree=None)

    class ReentrantCollector:
        name = "reentrant"
        @property
        def interest(self):
            class I:
                types = {"inline"}
                tags = set()
                ignore_inside = set()
                predicate = None
            return I()
        def should_process(self, token, ctx, wh_local):
            return True
        def on_token(self, idx, token, ctx, wh_local):
            wh_local.dispatch_all()  # Reentrant call - should raise
        def finalize(self, wh_local):
            return {}

    try:
        wh.register_collector(ReentrantCollector())
    except Exception:
        try:
            wh._collectors.append(ReentrantCollector())
        except Exception:
            pytest.skip("unable to register collector")

    # The reentrancy error will be caught and recorded in _collector_errors
    # unless RAISE_ON_COLLECTOR_ERROR is set
    import doxstrux.markdown.utils.token_warehouse as wh_mod
    old_raise = getattr(wh_mod, 'RAISE_ON_COLLECTOR_ERROR', False)

    try:
        # Enable error raising for this test
        wh_mod.RAISE_ON_COLLECTOR_ERROR = True
        with pytest.raises(RuntimeError, match="already dispatching"):
            wh.dispatch_all()
    finally:
        wh_mod.RAISE_ON_COLLECTOR_ERROR = old_raise
