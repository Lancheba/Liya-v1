"""
Patch script: fix audio mime_type in main.py to include sample rate.

The Gemini Live API requires "audio/pcm;rate=16000" (with sample rate),
not bare "audio/pcm" -- the bare form now triggers a 1007 "Request
contains an invalid argument" error and disconnects the session.

Usage:
    python patch_audio_mimetype.py
"""
import io

path = "main.py"

with io.open(path, "r", encoding="utf-8") as f:
    content = f.read()

old = '{"data": data, "mime_type": "audio/pcm"}'
new = '{"data": data, "mime_type": f"audio/pcm;rate={SEND_SAMPLE_RATE}"}'

if old not in content:
    if new in content:
        print("Already patched -- no change needed.")
    else:
        raise SystemExit(
            "Pattern not found. main.py may already differ from what "
            "this patch expects -- open main.py and check the "
            "_listen_audio() callback manually."
        )
else:
    content = content.replace(old, new)
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Patched main.py: mime_type now includes sample rate.")
