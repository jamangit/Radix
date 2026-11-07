export type QualityVerdict = "ok" | "too_quiet" | "noisy" | "too_loud";

export type AudioQuality = {
  level_db: number;
  snr_db: number;
  verdict: QualityVerdict;
};

/** Level reported for silence, in dB below full scale. */
export const SILENT_DB = -96;

/** Lowest level the meter displays. */
export const METER_FLOOR_DB = -60;

/** One weak phrase can be a fluke: wait for this many in a row before saying anything. */
export const WEAK_PHRASES_BEFORE_HINT = 2;

const HINTS: Record<Exclude<QualityVerdict, "ok">, string> = {
  too_quiet: "Your voice is faint. Move closer to the microphone or speak up a little.",
  noisy: "There is a lot of background noise. Try a quieter spot or move closer to the microphone.",
  too_loud: "The sound is distorting. Move back a little or lower the microphone volume.",
};

export type WeakStreak = { verdict: QualityVerdict; count: number };

export const NO_STREAK: WeakStreak = { verdict: "ok", count: 0 };

/**
 * Update the run of weak phrases after one more phrase.
 * `spoken` is false for a phrase that produced no text: it can add to a streak, but a good
 * measurement on such a phrase proves nothing, so it never clears one.
 */
export function trackQuality(
  streak: WeakStreak,
  quality: AudioQuality,
  spoken: boolean,
): WeakStreak {
  if (quality.verdict === "ok") return spoken ? NO_STREAK : streak;
  const count = streak.verdict === quality.verdict ? streak.count + 1 : 1;
  return { verdict: quality.verdict, count };
}

export function hintFor(streak: WeakStreak): string | null {
  if (streak.verdict === "ok" || streak.count < WEAK_PHRASES_BEFORE_HINT) return null;
  return HINTS[streak.verdict];
}

/** Loudness of a block of 16-bit samples, in dB below full scale (0 dB is the maximum). */
export function levelDb(samples: Int16Array): number {
  if (samples.length === 0) return SILENT_DB;
  let sum = 0;
  for (const sample of samples) sum += sample * sample;
  const rms = Math.sqrt(sum / samples.length);
  return 20 * Math.log10(Math.max(rms, 1) / 32768);
}