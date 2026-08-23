"use client";

import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, RefObject, SubmitEvent } from "react";
import { useSSE } from "@/hooks";
import { API_URL } from "@/lib/constants";
import type {
  ChatMessage,
  EndingCondition,
  RoleplayChatResponse,
} from "@/lib/types";
import { createMessageId } from "@/lib/utils";

interface UseChatData {
  input: string;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  shouldEnd: boolean;
  endingCondition: EndingCondition | null;
  endingRationale: string | null;
}

interface UseChatReturn {
  data: UseChatData;
  inputRef: RefObject<HTMLTextAreaElement | null>;
  onChange: (event: ChangeEvent<HTMLTextAreaElement>) => void;
  onSubmit: (event: SubmitEvent<HTMLFormElement>) => Promise<void>;
}

const initialData: UseChatData = {
  input: "",
  messages: [],
  isLoading: false,
  error: null,
  shouldEnd: false,
  endingCondition: null,
  endingRationale: null,
};

export default function useChat(roleplayId: string): UseChatReturn {
  const [data, setData] = useState<UseChatData>(initialData);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const { start, stop } = useSSE();

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
      stop();
    };
  }, [stop]);

  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setData((prev) => ({ ...prev, input: event.target.value }));
  };

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedInput = data.input.trim();
    if (!trimmedInput || data.isLoading || data.shouldEnd) return;

    const learnerMessageId = createMessageId();
    const aiMessageId = createMessageId();

    const learnerMessage: ChatMessage = {
      id: learnerMessageId,
      role: "learner",
      content: trimmedInput,
    };

    setData((prev) => ({
      ...prev,
      input: "",
      messages: [...prev.messages, learnerMessage],
      isLoading: true,
      error: null,
    }));

    abortControllerRef.current?.abort();
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    let receivedToken = false;
    let completed = false;
    let streamError: string | null = null;

    try {
      await start({
        url: `${API_URL}/roleplays/chat/stream`,
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roleplay_id: roleplayId,
          learner_message: trimmedInput,
        }),
        signal: abortController.signal,
        onMessage: (message) => {
          if (message.event === "token") {
            const payload = JSON.parse(message.data) as { text?: string };
            const text = payload.text ?? "";
            if (!text) return;

            const isFirstToken = !receivedToken;
            receivedToken = true;

            setData((prev) => {
              if (isFirstToken) {
                return {
                  ...prev,
                  messages: [
                    ...prev.messages,
                    {
                      id: aiMessageId,
                      role: "ai_character",
                      content: text,
                    },
                  ],
                };
              }

              return {
                ...prev,
                messages: prev.messages.map((item) =>
                  item.id === aiMessageId
                    ? { ...item, content: item.content + text }
                    : item,
                ),
              };
            });
            return;
          }

          if (message.event === "done") {
            const response = JSON.parse(message.data) as RoleplayChatResponse;
            completed = true;
            setData((prev) => {
              const hasAiMessage = prev.messages.some(
                (item) => item.id === aiMessageId,
              );
              return {
                ...prev,
                messages: hasAiMessage
                  ? prev.messages.map((item) =>
                      item.id === aiMessageId
                        ? { ...item, content: response.ai_response }
                        : item,
                    )
                  : [
                      ...prev.messages,
                      {
                        id: aiMessageId,
                        role: "ai_character",
                        content: response.ai_response,
                      },
                    ],
                isLoading: false,
                error: null,
                shouldEnd: response.should_end,
                endingCondition: response.ending_condition,
                endingRationale: response.ending_rationale,
              };
            });
            return;
          }

          if (message.event === "error") {
            const payload = JSON.parse(message.data) as { detail?: string };
            streamError =
              payload.detail ?? "Something went wrong. Please try again.";
          }
        },
      });

      if (streamError) {
        throw new Error(streamError);
      }

      if (!completed) {
        setData((prev) => ({
          ...prev,
          isLoading: false,
          error: prev.error ?? "The response stream ended unexpectedly.",
        }));
      }
    } catch (submitError) {
      if (abortController.signal.aborted) return;

      setData((prev) => ({
        ...prev,
        error:
          submitError instanceof Error
            ? submitError.message
            : "Something went wrong. Please try again.",
        isLoading: false,
      }));
    } finally {
      if (!abortController.signal.aborted) {
        inputRef.current?.focus();
      }
    }
  }

  return {
    data,
    inputRef,
    onChange: handleChange,
    onSubmit: handleSubmit,
  };
}

export type { UseChatData, UseChatReturn };
