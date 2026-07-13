"use client";

import { useChat } from "@/hooks";
import { DEFAULT_ROLEPLAY } from "@/lib/roleplay-defaults";
import { ChatForm, Messages } from "@/components/Chat";

export default function ChatView() {
  const { data, inputRef, onChange, onSubmit } = useChat();

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground px-10">
      <header className="border-b border-border bg-card px-4 py-4 sm:px-6">
        <p className="text-base font-medium text-muted-foreground">
          Roleplay chat
        </p>
        <h1 className="mt-1 text-3xl font-semibold tracking-tight">
          {DEFAULT_ROLEPLAY.ai_character_name}
        </h1>
        <p className="mt-1 text-base font-normal text-muted-foreground">
          {DEFAULT_ROLEPLAY.ai_character_role} · {DEFAULT_ROLEPLAY.scenario}
        </p>
      </header>

      <main className="flex-1 overflow-hidden">
        <Messages messages={data.messages} isLoading={data.isLoading} />
      </main>

      <footer className=" bg-card px-4 py-4 sm:px-6">
        <ChatForm
          input={data.input}
          isLoading={data.isLoading}
          error={data.error}
          isEmpty={data.messages.length === 0}
          inputRef={inputRef}
          onChange={onChange}
          onSubmit={onSubmit}
        />
      </footer>
    </div>
  );
}
