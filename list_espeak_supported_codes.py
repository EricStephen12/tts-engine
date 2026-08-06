from phonemizer.backend.espeak.wrapper import EspeakWrapper

wrapper = EspeakWrapper()
for voice in wrapper.available_voices():
    print(repr(voice.language), repr(voice.identifier), repr(voice.name))
