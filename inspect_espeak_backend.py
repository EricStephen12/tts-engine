import importlib
m = importlib.import_module('phonemizer.backend.espeak')
print('module:', m.__name__)
# print useful attributes
for name in dir(m):
    if 'lang' in name.lower() or 'support' in name.lower() or 'code' in name.lower():
        print(name)
import inspect
funcs = [n for n,f in inspect.getmembers(m) if inspect.isfunction(f)]
print('\nfunctions count:', len(funcs))
print('\nSample functions:', funcs[:20])
