import importlib, os, sys
import types

# Make src importable
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(THIS_DIR, '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
SRC_DIR = os.path.join(PROJECT_ROOT, 'src')
if SRC_DIR not in sys.path:
    sys.path.append(SRC_DIR)


def test_step17_imports_smoke():
    mod = importlib.import_module('src.step17_augment_recommendations')
    # Ensure critical imports resolved
    assert hasattr(mod, 'os')
    assert hasattr(mod, 'pd')
    assert hasattr(mod, 'np')
    # Helpers we reference
    assert hasattr(mod, 'get_period_label')
    assert hasattr(mod, 'register_step_output')
