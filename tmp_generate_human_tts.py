from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from models.model_manager import get_model_manager
from inference.engine import TTSEngine
from audio.encoder import to_wav_bytes

manager = get_model_manager()
manager.load()
engine = TTSEngine(model_manager=manager)
text = (
    "Hello there. Welcome to Eixora. This should sound calm and natural. "
    "[pause:500ms] I am speaking like a real person with a subtle warm tone."
)
result = engine.synthesize(
    text,
    voice='af_heart',
    emotion='neutral',
    speed=1.0,
    lang='en',
    background_noise=0.0,
)
out_path = Path('sample_af_heart_clear.wav')
out_path.write_bytes(to_wav_bytes(result.audio, result.sample_rate))
print('wrote', out_path.resolve())
