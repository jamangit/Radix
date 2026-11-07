import { describe, expect, it } from "vitest";
import { NO_STREAK, hintFor, levelDb, trackQuality, type AudioQuality } from "./audio-quality";

const quality = (verdict: AudioQuality["verdict"]): AudioQuality => ({
  level_db: -30,
  snr_db: 20,
  verdict,
});

describe("trackQuality", () => {
  it("stays quiet after a single weak phrase", () => {
    const streak = trackQuality(NO_STREAK, quality("too_quiet"), true);

    expect(hintFor(streak)).toBeNull();
  });

  it("warns after two weak phrases in a row", () => {
    let streak = trackQuality(NO_STREAK, quality("too_quiet"), true);
    streak = trackQuality(streak, quality("too_quiet"), true);

    expect(hintFor(streak)).toMatch(/closer to the microphone/);
  });

  it("starts counting again when the problem changes", () => {
    let streak = trackQuality(NO_STREAK, quality("too_quiet"), true);
    streak = trackQuality(streak, quality("noisy"), true);

    expect(hintFor(streak)).toBeNull();
  });

  it("clears the warning as soon as a phrase is good", () => {
    let streak = trackQuality(NO_STREAK, quality("too_quiet"), true);
    streak = trackQuality(streak, quality("too_quiet"), true);
    streak = trackQuality(streak, quality("ok"), true);

    expect(hintFor(streak)).toBeNull();
  });

  it("does not clear the warning for a phrase that sounded fine but produced no text", () => {
    let streak = trackQuality(NO_STREAK, quality("too_quiet"), true);
    streak = trackQuality(streak, quality("too_quiet"), true);
    streak = trackQuality(streak, quality("ok"), false);

    expect(hintFor(streak)).not.toBeNull();
  });

  it("counts a weak phrase even when it produced no text", () => {
    let streak = trackQuality(NO_STREAK, quality("too_quiet"), false);
    streak = trackQuality(streak, quality("too_quiet"), false);

    expect(hintFor(streak)).not.toBeNull();
  });
});

describe("levelDb", () => {
  it("is about -6 dB for half of full scale", () => {
    expect(levelDb(new Int16Array(160).fill(16384))).toBeCloseTo(-6.02, 1);
  });

  it("is very low for silence", () => {
    expect(levelDb(new Int16Array(160))).toBeLessThan(-80);
  });
});