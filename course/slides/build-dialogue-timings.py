"""Build turn-level timing when Edge omits sentence-boundary metadata.

AudioExplainer deliberately drops an incomplete sync track. For these unusually
long dialogues we still need reliable turn following, so this script repeats
the same neural synthesis per turn, measures the decoded WAV duration, and
aligns the resulting timeline to the final AudioExplainer MP3.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import subprocess
import tempfile
import wave
from pathlib import Path

import edge_tts


TURN = re.compile(r"^\s*(Host|Guest):\s*(.+)$")
VOICE = {"Host": "es-MX-JorgeNeural", "Guest": "es-PE-CamilaNeural"}
RATE = "-2%"
SAMPLE_RATE = 24_000
PAUSE_S = 0.4


def parse_turns(script: Path) -> list[tuple[str, str]]:
    turns = []
    for line in script.read_text(encoding="utf-8").splitlines():
        match = TURN.match(line)
        if match:
            turns.append((match.group(1), match.group(2).strip()))
    if not turns:
        raise RuntimeError(f"No dialogue turns in {script}")
    return turns


async def synthesise(index: int, speaker: str, text: str, directory: Path, gate: asyncio.Semaphore) -> tuple[int, float]:
    mp3 = directory / f"turn-{index:03d}.mp3"
    wav = directory / f"turn-{index:03d}.wav"
    last_error: Exception | None = None
    async with gate:
        for attempt in range(3):
            try:
                await edge_tts.Communicate(text, voice=VOICE[speaker], rate=RATE).save(str(mp3))
                break
            except Exception as error:  # network service can fail transiently
                last_error = error
                if attempt == 2:
                    raise
                await asyncio.sleep(1.5 * (attempt + 1))
    if not mp3.exists() or mp3.stat().st_size == 0:
        raise RuntimeError(f"No audio for turn {index}: {last_error}")

    subprocess.run(
        [
            "ffmpeg", "-loglevel", "error", "-y", "-i", str(mp3),
            "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "wav", str(wav),
        ],
        check=True,
    )
    with wave.open(str(wav), "rb") as handle:
        duration = handle.getnframes() / handle.getframerate()
    return index, duration


def media_duration(audio: Path) -> float:
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=nw=1:nk=1", str(audio),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return float(result.stdout.strip())


async def build(script: Path, audio: Path, output: Path, workers: int) -> None:
    turns = parse_turns(script)
    gate = asyncio.Semaphore(workers)
    with tempfile.TemporaryDirectory(prefix="dialogue-timings-") as temporary:
        directory = Path(temporary)
        measured = await asyncio.gather(*[
            synthesise(index, speaker, text, directory, gate)
            for index, (speaker, text) in enumerate(turns)
        ])

    durations = [0.0] * len(turns)
    for index, duration in measured:
        durations[index] = duration

    constructed = sum(durations) + PAUSE_S * (len(turns) - 1)
    final_duration = media_duration(audio)
    scale = final_duration / constructed
    timeline = 0.0
    timed_turns = []
    for index, duration in enumerate(durations):
        start = timeline * scale
        timeline += duration
        end = timeline * scale
        timed_turns.append({"part_index": index, "start": start, "end": end})
        if index != len(durations) - 1:
            timeline += PAUSE_S

    output.write_text(
        json.dumps(
            {
                "duration": final_duration,
                "constructed_duration": constructed,
                "scale": scale,
                "turns": timed_turns,
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output} ({len(turns)} turns, scale={scale:.6f})")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--script", type=Path, required=True)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=3)
    args = parser.parse_args()
    asyncio.run(build(args.script, args.audio, args.output, max(1, args.workers)))


if __name__ == "__main__":
    main()
