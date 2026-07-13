import { useEffect, useRef } from "react";
import { DEFAULT_ROLEPLAY } from "@/lib/roleplay-defaults";
import type { ChatMessage } from "@/lib/types";

type MessagesProps = {
  messages: ChatMessage[];
  isLoading: boolean;
};

export default function Messages({ messages, isLoading }: MessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
      <div className="mx-auto flex max-w-3xl flex-col gap-4">
        {messages.length > 0 ? (
          <div className="flex flex-col gap-4">
            {messages.map((message) => {
              const isLearner = message.role === "learner";

              return (
                <div
                  key={message.id}
                  className={`flex ${isLearner ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={
                      isLearner
                        ? "max-w-[85%] rounded-lg bg-[#f4f4f4] px-4 py-3 text-base leading-6 text-foreground dark:bg-[#303030]"
                        : "w-full rounded-2xl bg-transparent px-4 py-3 text-sm leading-6 text-foreground"
                    }
                  >
                    <p className="whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              );
            })}
          </div>
        ) : null}

        {isLoading ? (
          <div className="flex justify-start">
            <div className="w-full rounded-2xl bg-transparent px-4 py-3 text-sm text-muted-foreground">
              <p className="text-xs font-medium uppercase tracking-wide opacity-70">
                {DEFAULT_ROLEPLAY.ai_character_name}
              </p>
              <p className="mt-1">Typing...</p>
            </div>
          </div>
        ) : null}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
