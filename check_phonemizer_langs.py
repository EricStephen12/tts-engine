from phonemizer import phonemize

codes = [
    'a', 'en', 'en-us', 'en_US', 'en_us', 'en-US', 'en_gb', 'en-gb', 'en_GB',
    'en-us-nt', 'en-us-re', 'es', 'fr', 'pt-br', 'pt_BR', 'ru'
]

for lang in codes:
    try:
        out = phonemize('Hello world', language=lang, backend='espeak', strip=True)
        print(f"{lang}: OK -> {out}")
    except Exception as e:
        print(f"{lang}: ERR -> {e}")
