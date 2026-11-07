"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { components } from "@/lib/api/schema";
import { websocketUrl } from "@/lib/ws-url";
import { PCM_WORKLET_SOURCE } from "./pcm-worklet-source";

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

      const abort = (message: string, cause?: unknown) => {
        if (cause !== undefined) console.error(message, cause);
        stopAudio();
        socketRef.current?.close();
        socketRef.current = null;
        setError(message);
        setStatus("idle");
      };

      let stream: MediaStream;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: 1,
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        streamRef.current = stream;
      } catch (cause) {
        abort(microphoneMessage(cause), cause);
        return;
      }

      let ticket: string;
      try {
        const { data, response } = await api.POST("/auth/ws-ticket");
        if (!data) {
          abort(
            response.status === 401
              ? "Your session has expired. Please sign in again."
              : `The API refused the request (status ${response.status}).`,
          );
          return;
        }
        ticket = data.ticket;
      } catch (cause) {
        abort("Could not reach the API. Is it running?", cause);
        return;
      }

      let socket: WebSocket;
      try {
        socket = new WebSocket(
          websocketUrl(`/ws/transcribe?ticket=${encodeURIComponent(ticket)}`),
        );
      } catch (cause) {
        abort("The transcription server address is invalid.", cause);
        return;
      }
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

      socket.onerror = () =>
        setError(
          "Could not reach the transcription server. Check that the API is running and, in Codespaces, that port 8000 is public.",
        );

      socket.onclose = () => {
        stopAudio();
        socketRef.current = null;
        setSpeaking(false);
        setStatus("idle");
      };

      try {
        const context = new AudioContext();
        contextRef.current = context;
        await context.resume();

        const workletUrl = URL.createObjectURL(
          new Blob([PCM_WORKLET_SOURCE], { type: "text/javascript" }),
        );
        try {
          await context.audioWorklet.addModule(workletUrl);
        } finally {
          URL.revokeObjectURL(workletUrl);
        }

        const source = context.createMediaStreamSource(stream);
        const worklet = new AudioWorkletNode(context, "pcm-processor");
        worklet.port.onmessage = (event: MessageEvent<ArrayBuffer>) => {
          if (started && socket.readyState === WebSocket.OPEN) socket.send(event.data);
        };
        // The worklet only runs when connected to the output, so route it through a muted gain.
        const mute = new GainNode(context, { gain: 0 });
        source.connect(worklet);
        worklet.connect(mute);
        mute.connect(context.destination);
      } catch (cause) {
        const name = cause instanceof Error ? cause.name : "UnknownError";
        abort(`The audio processor could not be started (${name}).`, cause);
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