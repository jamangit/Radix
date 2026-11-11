"""Exercise every bundled dependency once.

Run by CI against the packaged program: a missing file or library then fails the build
instead of surprising someone on their own computer.
"""


def run() -> None:
    import ctranslate2
    import faster_whisper
    import onnxruntime

    from wordmeter_api.analysis import analyze_detailed
    from wordmeter_api.analysis.language import detect_language
    from wordmeter_api.security import hash_password, verify_password
    from wordmeter_api.speech.vad import create_voice_detector

    result, _ = analyze_detailed("Le chat mange la souris.", "fr")
    if result.total_words != 5:
        raise SystemExit("selftest failed: word analysis")
    if detect_language("Le chat mange la souris et il dort.")[0] != "fr":
        raise SystemExit("selftest failed: language detection")
    if create_voice_detector()(bytes(1024)) > 0.5:
        raise SystemExit("selftest failed: voice detector")
    if not verify_password("secret", hash_password("secret")):
        raise SystemExit("selftest failed: password hashing")

    print(
        "selftest ok"
        f" (faster-whisper {faster_whisper.__version__},"
        f" ctranslate2 {ctranslate2.__version__},"
        f" onnxruntime {onnxruntime.__version__})"
    )
