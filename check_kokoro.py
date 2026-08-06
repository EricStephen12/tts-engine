import sys, os
print('exe', sys.executable)
print('prefix', sys.prefix)
site_packages = os.path.join(sys.prefix, 'Lib', 'site-packages')
print('site_packages', site_packages)
print('exists', os.path.exists(site_packages))
if os.path.exists(site_packages):
    print('entries', sorted(os.listdir(site_packages))[:20])
    print('has kokoro_onnx', os.path.exists(os.path.join(site_packages, 'kokoro_onnx')))
    print('kokoro files', sorted(os.listdir(os.path.join(site_packages, 'kokoro_onnx'))))
try:
    import kokoro_onnx
    print('import ok', kokoro_onnx.__file__)
except Exception as e:
    print('import failed', type(e).__name__, e)
    raise
