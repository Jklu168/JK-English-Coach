from gtts import gTTS
import time
from pathlib import Path

words = [
    "ability","accept","account","action","beautiful",
    "computer","engineer","future","knowledge","success",
    "entrepreneur","environment","important","investment","management",
    "responsibility","technology","vocabulary","wonderful","yesterday"
]

out = Path("test_audio_gtts")
out.mkdir(exist_ok=True)

ok = 0
fail = 0
start = time.time()

for w in words:
    try:
        print("GEN:", w)
        gTTS(w, lang="en").save(out / f"{w}_gtts.mp3")
        ok += 1
        print("OK :", w)
        time.sleep(1.0)
    except Exception as e:
        fail += 1
        print("FAIL:", w, "->", e)
        time.sleep(3.0)

print(f"DONE ok={ok} fail={fail} sec={time.time()-start:.1f}")
