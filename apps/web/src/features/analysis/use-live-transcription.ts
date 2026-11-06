"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { websocketUrl } from "@/lib/ws-url";

export type LiveStatus = "idle" | "connecting" | "listening" | "finishing";
export type LiveLanguage = "auto" | "fr" | "en";
type AnalyzeResponse = components["schemas"]["AnalyzeResponse"];

export type LiveResult = Pick<
  AnalyzeResponse,
  "language" | "total_words" | "unique_words" | "lexical_diversity" | "top_words" | "rare_words"
> & {
  transcript: string;
  audio_seconds: number;
};

type ServerMessage =
  | { type: "ready" }
  | { type: "speech"; active: boolean }
  | { type: "segment"; text: string; words: number; total_words: number }
  | ({ type: "final" } & LiveResult)
  | { type: "error"; code: string; message: string };

function microphoneMessage(error: unknown): string {
  const name = error instanceof DOMException ? error.name : "";
  switch (name) {
    case "NotAllowedError":
      return "Microphone access is blocked. Allow it in your browser's site settings, and open the app in a normal browser tab (not an embedded preview).";
    case "NotFoundError":
      return "No microphone was found on this device.";
    case "NotReadableError":
      return "The microphone is being used by another application.";
    default:
      return "The microphone could not be started.";
  }
}

export function useLiveTranscription() {
  const queryClient = useQueryClient();
  const [status, setStatus] = useState<LiveStatus>("idle");
  const [speaking, setSpeaking] = useState(false);
  const [segments, setSegments] = useState<string[]>([]);
  const [totalWords, setTotalWords] = useState(0);
  const [result, setResult] = useState<LiveResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const socketRef = useRef<WebSocket | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const contextRef = useRef<AudioContext | null>(null);

  const stopAudio = useCallback(() => {
    streamRef.current?.getTracks().forEach((track) => track.stop());
    streamRef.current = null;
    void contextRef.current?.close();
    contextRef.current = null;
  }, []);

  const start = useCallback(
    async (language: LiveLanguage) => {
      setError(null);
      setResult(null);
      setSegments([]);
      setTotalWords(0);
      setSpeaking(false);
      setStatus("connecting");

      const abort = (message: string) => {
        stopAudio();
        socketRef.current?.close();
        socketRef.current = null;
        setError(message);
        setStatus("idle");
      };

      try {
        streamRef.current = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
      } catch (cause) {
        abort(microphoneMessage(cause));
        return;
      }

      try {
        const { data } = await api.POST("/auth/ws-ticket");
        if (!data) throw new Error("No ticket");

        const socket = new WebSocket(
          websocketUrl(`/ws/transcribe?ticket=${encodeURIComponent(data.ticket)}`),
        );
        socket.binaryType = "arraybuffer";
        socketRef.current = socket;
        let started = false;

        socket.onopen = () => {
          socket.send(
            JSON.stringify({ type: "start", language: language === "auto" ? null : language }),
          );
          started = true;
        };

        socket.onmessage = (event: MessageEvent<string>) => {
          const message = JSON.parse(event.data) as ServerMessage;
          switch (message.type) {
            case "ready":
              setStatus("listening");
              break;
            case "speech":
              setSpeaking(message.active);
              break;
            case "segment":
              setSegments((previous) => [...previous, message.text]);
              setTotalWords(message.total_words);
              break;
            case "final":
              setResult(message);
              void queryClient.invalidateQueries({ queryKey: ["stats"] });
              break;
            case "error":
              setError(message.message);
              break;
          }
        };

        socket.onerror = () => setError("Could not reach the transcription server.");

        socket.onclose = () => {
          stopAudio();
          socketRef.current = null;
          setSpeaking(false);
          setStatus("idle");
        };

        const context = new AudioContext();
        contextRef.current = context;
        await context.audioWorklet.addModule("/pcm-worklet.js");
        const source = context.createMediaStreamSource(streamRef.current);
        const worklet = new AudioWorkletNode(context, "pcm-processor");
        worklet.port.onmessage = (event: MessageEvent<ArrayBuffer>) => {
          if (started && socket.readyState === WebSocket.OPEN) socket.send(event.data);
        };
        // The worklet only runs when connected to the output, so route it through a muted gain.
        const mute = new GainNode(context, { gain: 0 });
        source.connect(worklet);
        worklet.connect(mute);
        mute.connect(context.destination);
      } catch {
        abort("Could not start the live transcription.");
      }
    },
    [queryClient, stopAudio],
  );

  const stop = useCallback(() => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return;
    stopAudio();
    socket.send(JSON.stringify({ type: "stop" }));
    setStatus("finishing");
  }, [stopAudio]);

  useEffect(() => {
    return () => {
      stopAudio();
      socketRef.current?.close();
    };
  }, [stopAudio]);

  return { status, speaking, segments, totalWords, result, error, start, stop };
}