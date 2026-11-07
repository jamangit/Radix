/**
 * Source of the AudioWorklet that turns microphone audio into 16 kHz, 16-bit PCM,
 * in packets of 100 ms. It is loaded from memory (see use-live-transcription.ts)
 * so it never depends on a file being served.
 */
export const PCM_WORKLET_SOURCE = `
const TARGET_RATE = 16000;
const CHUNK_SAMPLES = 1600;

class PcmProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.ratio = sampleRate / TARGET_RATE;
    this.sum = 0;
    this.count = 0;
    this.position = 0;
    this.chunk = new Int16Array(CHUNK_SAMPLES);
    this.filled = 0;
  }

  process(inputs) {
    const channel = inputs[0][0];
    if (!channel) return true;

    for (let i = 0; i < channel.length; i++) {
      this.sum += channel[i];
      this.count += 1;
      this.position += 1;
      if (this.position < this.ratio) continue;

      this.position -= this.ratio;
      const sample = Math.max(-1, Math.min(1, this.sum / this.count));
      this.sum = 0;
      this.count = 0;
      this.chunk[this.filled++] = sample < 0 ? sample * 0x8000 : sample * 0x7fff;

      if (this.filled === CHUNK_SAMPLES) {
        this.port.postMessage(this.chunk.buffer, [this.chunk.buffer]);
        this.chunk = new Int16Array(CHUNK_SAMPLES);
        this.filled = 0;
      }
    }
    return true;
  }
}

registerProcessor("pcm-processor", PcmProcessor);
`;