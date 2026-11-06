/* global AudioWorkletProcessor, registerProcessor, sampleRate */

const TARGET_RATE = 16000;
const CHUNK_SAMPLES = 1600; // 100 ms

class PcmProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.ratio = sampleRate / TARGET_RATE; // browsers record at 44.1 or 48 kHz
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
      // Averaging the input samples that fall in one output sample is a cheap low-pass filter.
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