"use client";

import { useRef, useState } from "react";
import type { ChangeEvent, RefObject, SubmitEvent } from "react";
import { useSSE } from "@/hooks";
import { API_URL } from "@/lib/constants";
import { createRAFBuffer } from "@/lib/createRAFBuffer";
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

function isAbortError(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

function upsertAiMessage(
  messages: ChatMessage[],
  id: string,
  content: string,
  append = false,
): ChatMessage[] {
  const hasAiMessage = messages.some((item) => item.id === id);
  if (!hasAiMessage) {
    return [...messages, { id, role: "ai_character", content }];
  }

  return messages.map((item) =>
    item.id === id
      ? { ...item, content: append ? item.content + content : content }
      : item,
  );
}

export default function useChat(roleplayId: string): UseChatReturn {
  const [data, setData] = useState<UseChatData>(initialData);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const { start } = useSSE();

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

    let completed = false;
    let aborted = false;
    let streamError: string | null = null;

    const tokenBuffer = createRAFBuffer<string>((texts) => {
      const text = texts.join("");
      if (!text) return;

      setData((prev) => ({
        ...prev,
        messages: upsertAiMessage(prev.messages, aiMessageId, text, true),
      }));
    });

    try {
      await start({
        url: `${API_URL}/roleplays/chat/stream`,
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          roleplay_id: roleplayId,
          learner_message: trimmedInput,
        }),
        onMessage: (message) => {
          if (message.event === "token") {
            const payload = JSON.parse(message.data) as { text?: string };
            const text = payload.text ?? "";
            if (!text) return;

            tokenBuffer.push(text);
            return;
          }

          if (message.event === "done") {
            tokenBuffer.flushNow();
            const response = JSON.parse(message.data) as RoleplayChatResponse;
            completed = true;
            setData((prev) => ({
              ...prev,
              messages: upsertAiMessage(
                prev.messages,
                aiMessageId,
                response.ai_response,
              ),
              isLoading: false,
              error: null,
              shouldEnd: response.should_end,
              endingCondition: response.ending_condition,
              endingRationale: response.ending_rationale,
            }));
            return;
          }

          if (message.event === "error") {
            tokenBuffer.flushNow();
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
        tokenBuffer.flushNow();
        setData((prev) => ({
          ...prev,
          isLoading: false,
          error: prev.error ?? "The response stream ended unexpectedly.",
        }));
      }
    } catch (submitError) {
      if (isAbortError(submitError)) {
        aborted = true;
        return;
      }

      setData((prev) => ({
        ...prev,
        error:
          submitError instanceof Error
            ? submitError.message
            : "Something went wrong. Please try again.",
        isLoading: false,
      }));
    } finally {
      tokenBuffer.cancel();
      if (!aborted) {
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
