import importlib, os
m = importlib.import_module('phonemizer.backend.espeak')
path = m.__file__
print('path:', path)
print('exists:', os.path.exists(path))
d = os.path.dirname(path)
print('dir:', d)
try:
    print('listing:', os.listdir(d))
except Exception as e:
    print('list error', e)
