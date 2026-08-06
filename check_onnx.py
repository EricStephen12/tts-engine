import onnx
import sys
p='models/weights/kokoro-v1.0.onnx'
try:
    m=onnx.load(p)
    print('onnx load OK. ir_version=', m.ir_version)
except Exception as e:
    print('onnx load failed:', type(e), e)
    sys.exit(1)
