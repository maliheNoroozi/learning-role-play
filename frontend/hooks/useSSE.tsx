"use client";

import { useCallback, useEffect, useRef } from "react";

export type SSEMessage = {
  event: string;
  data: string;
  id?: string;
};

export type StartSSEOptions = {
  url: string;
  method?: string;
  headers?: HeadersInit;
  body?: BodyInit | null;
  signal?: AbortSignal;
  onMessage: (message: SSEMessage) => void;
};

/** Parse a fetch `text/event-stream` body and invoke `onMessage` per event.
 Take the raw streaming HTTP response and turn it into complete SSE messages.
**/
export async function consumeSSE(
  response: Response,
  onMessage: (message: SSEMessage) => void,
  signal?: AbortSignal,
): Promise<void> {
  if (!response.body) {
    throw new Error("No response body to stream.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let eventName = "message";
  let dataLines: string[] = [];
  let id: string | undefined;

  const dispatch = () => {
    if (dataLines.length === 0) {
      eventName = "message";
      id = undefined;
      return;
    }
    onMessage({
      event: eventName,
      data: dataLines.join("\n"),
      id,
    });
    eventName = "message";
    dataLines = [];
    id = undefined;
  };

  try {
    while (true) {
      if (signal?.aborted) {
        await reader.cancel();
        break;
      }

      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split(/\r?\n/);
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (line === "") {
          dispatch();
          continue;
        }
        if (line.startsWith(":")) continue;

        const colonIndex = line.indexOf(":");
        const field = colonIndex === -1 ? line : line.slice(0, colonIndex);
        let fieldValue = colonIndex === -1 ? "" : line.slice(colonIndex + 1);
        if (fieldValue.startsWith(" ")) fieldValue = fieldValue.slice(1);

        if (field === "event") eventName = fieldValue;
        else if (field === "data") dataLines.push(fieldValue);
        else if (field === "id") id = fieldValue;
      }
    }

    dispatch();
  } finally {
    reader.releaseLock();
  }
}

/**
 * Fetch-based SSE helper with abort-on-unmount.
 */
export default function useSSE() {
  const abortRef = useRef<AbortController | null>(null);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
  }, []);

  useEffect(() => stop, [stop]);

  const start = useCallback(
    async (options: StartSSEOptions): Promise<void> => {
      stop();
      const controller = new AbortController();
      abortRef.current = controller;

      const signal = options.signal
        ? AbortSignal.any([controller.signal, options.signal])
        : controller.signal;

      const response = await fetch(options.url, {
        method: options.method ?? "GET",
        headers: {
          Accept: "text/event-stream",
          ...options.headers,
        },
        body: options.body,
        signal,
      });

      if (!response.ok) {
        let detail = `Request failed (${response.status}).`;
        try {
          const errorBody = (await response.json()) as {
            detail?: string | { msg?: string }[];
          };
          if (typeof errorBody.detail === "string") detail = errorBody.detail;
          else if (
            Array.isArray(errorBody.detail) &&
            errorBody.detail[0]?.msg
          ) {
            detail = errorBody.detail[0].msg;
          }
        } catch {
          // keep fallback
        }
        throw new Error(detail);
      }

      await consumeSSE(response, options.onMessage, signal);
    },
    [stop],
  );

  return { start, stop };
}
