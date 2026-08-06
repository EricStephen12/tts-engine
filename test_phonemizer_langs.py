from phonemizer import phonemize
codes = ['en-us','en','en_US','en_us','en-gb','en_gb','en-uk','en']
for lang in codes:
    try:
        out = phonemize('hello', language=lang, backend='espeak', strip=True)
        print(f"{lang}: OK -> {out}")
    except Exception as e:
        print(f"{lang}: ERR -> {e}")
