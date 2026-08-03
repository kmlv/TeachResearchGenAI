import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const project = path.resolve(here, "../..");

const inputs = [
  {
    id: "capacidades",
    script: "deliverables/dialogue-01-capacidades-productivas-script.md",
    sidecar: "deliverables/dialogue-01-capacidades-productivas.audio.json",
    timings: "deliverables/dialogue-01-capacidades-productivas.turns.json",
  },
  {
    id: "hipotesis",
    script: "deliverables/dialogue-02-hipotesis-refutable-script.md",
    sidecar: "deliverables/dialogue-02-hipotesis-refutable.audio.json",
    timings: "deliverables/dialogue-02-hipotesis-refutable.turns.json",
  },
];

const parseTurns = (source) => source
  .split(/\r?\n/)
  .map((line) => line.match(/^\s*(Host|Guest):\s*(.+)$/))
  .filter(Boolean)
  .map((match) => ({
    speaker: match[1] === "Host" ? "Kristian" : "IA",
    text: match[2].trim(),
  }));

const buildTrack = ({ id, script, sidecar, timings }) => {
  const scriptPath = path.join(project, script);
  const sidecarPath = path.join(project, sidecar);
  const turns = parseTurns(fs.readFileSync(scriptPath, "utf8"));
  const metadata = JSON.parse(fs.readFileSync(sidecarPath, "utf8"));
  const timing = new Map();
  const segments = metadata.sync?.segments;
  if (Array.isArray(segments) && segments.length) {
    for (const segment of segments) {
      const index = Number(segment.part_index);
      const current = timing.get(index) || {
        start: Number.POSITIVE_INFINITY,
        end: 0,
      };
      current.start = Math.min(current.start, Number(segment.start_s));
      current.end = Math.max(current.end, Number(segment.end_s));
      timing.set(index, current);
    }
  } else {
    const fallbackPath = path.join(project, timings);
    const fallback = JSON.parse(fs.readFileSync(fallbackPath, "utf8"));
    const fallbackScale = Number(metadata.duration_s) / Number(fallback.duration);
    if (!Number.isFinite(fallbackScale) || fallbackScale <= 0) {
      throw new Error(`${id}: invalid fallback duration in ${timings}`);
    }
    for (const turn of fallback.turns || []) {
      timing.set(Number(turn.part_index), {
        start: Number(turn.start) * fallbackScale,
        end: Number(turn.end) * fallbackScale,
      });
    }
  }

  if (turns.length !== timing.size) {
    throw new Error(`${id}: ${turns.length} transcript turns but ${timing.size} timed parts`);
  }

  return [id, {
    duration: metadata.duration_s,
    turns: turns.map((turn, index) => {
      const times = timing.get(index);
      if (!times || !Number.isFinite(times.start)) {
        throw new Error(`${id}: missing timing for turn ${index}`);
      }
      return { ...turn, start: times.start, end: times.end };
    }),
  }];
};

const tracks = Object.fromEntries(inputs.map(buildTrack));
const output = `window.DIALOGUE_TRACKS = ${JSON.stringify(tracks, null, 2)};\n`;
fs.writeFileSync(path.join(here, "dialogue-data.js"), output, "utf8");
console.log(`Wrote ${path.join(here, "dialogue-data.js")}`);
