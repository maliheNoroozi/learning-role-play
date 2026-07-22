import { sendMessage } from "@/lib/api";
import { DEFAULT_ROLEPLAY } from "@/lib/roleplay-defaults";
import { ChatMessage } from "@/lib/types";
import { createMessageId } from "@/lib/utils";
import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, RefObject, SubmitEvent } from "react";

interface UseChatData {
  input: string;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
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
};

export default function useChat(): UseChatReturn {
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
    if (!trimmedInput || data.isLoading) return;

    abortControllerRef.current?.abort();
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    const learnerMessage: ChatMessage = {
      id: createMessageId(),
      role: "learner",
      content: trimmedInput,
    };

    const nextMessages = [...data.messages, learnerMessage];
    setData({
      input: "",
      messages: nextMessages,
      isLoading: true,
      error: null,
    });

    try {
      const response = await sendMessage(
        {
          ...DEFAULT_ROLEPLAY,
          learner_message: trimmedInput,
          conversation_history: nextMessages.slice(0, -1).map((message) => ({
            role: message.role,
            content: message.content,
          })),
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
