from pathlib import Path
import sys
sys.path.insert(0, str(Path('.').resolve()))
from models.model_manager import get_model_manager

manager = get_model_manager()
manager.load()
voices = manager.list_voices()
print(f'voices_count={len(voices)}')
for v in voices:
    print(v)
