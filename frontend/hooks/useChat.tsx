"use client";

import { sendMessage } from "@/lib/api";
import type { ChatMessage, EndingCondition } from "@/lib/types";
import { createMessageId } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, RefObject, SubmitEvent } from "react";

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

  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);

  const handleChange = (event: ChangeEvent<HTMLTextAreaElement>) => {
    setData((prev) => ({ ...prev, input: event.target.value }));
  };

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();

    const trimmedInput = data.input.trim();
    if (!trimmedInput || data.isLoading || data.shouldEnd) return;

    const learnerMessage: ChatMessage = {
      id: createMessageId(),
      role: "learner",
      content: trimmedInput,
    };

    const nextMessages = [...data.messages, learnerMessage];
    setData({
      ...data,
      input: "",
      messages: nextMessages,
      isLoading: true,
      error: null,
    });

    abortControllerRef.current?.abort();
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      const response = await sendMessage(
        {
          roleplay_id: roleplayId,
          learner_message: trimmedInput,
        },
        abortController.signal,
      );

      setData((prev) => ({
        ...prev,
        messages: [
          ...nextMessages,
          {
            id: createMessageId(),
            role: "ai_character",
            content: response.ai_response,
          },
        ],
        isLoading: false,
        error: null,
        shouldEnd: response.should_end,
        endingCondition: response.ending_condition,
        endingRationale: response.ending_rationale,
      }));
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
