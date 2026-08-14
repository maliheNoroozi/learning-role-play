"use client";

import Link from "next/link";
import { useChat } from "@/hooks";
import { ChatForm, Messages } from "@/components/Chat";
import type { RoleplaySetup } from "@/lib/types";

type ChatViewProps = {
  roleplayId: string;
  setup: RoleplaySetup;
};

export default function ChatView({ roleplayId, setup }: ChatViewProps) {
  const { data, inputRef, onChange, onSubmit } = useChat(roleplayId);

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <header className="border-b border-border bg-card px-4 py-4 sm:px-6">
        <div className="mx-auto flex max-w-3xl items-start justify-between gap-4">
          <div>
            <p className="text-base font-medium text-muted-foreground">
              Roleplay chat
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight">
              {setup.ai_character_name}
            </h1>
            <p className="mt-1 text-base font-normal text-muted-foreground">
              {setup.ai_character_role} · {setup.scenario}
            </p>
          </div>
          <Link
            href="/"
            className="shrink-0 text-sm text-muted-foreground underline-offset-4 hover:underline"
          >
            New roleplay
          </Link>
        </div>
      </header>

      <main className="flex-1 overflow-hidden">
        <Messages
          messages={data.messages}
          isLoading={data.isLoading}
          aiCharacterName={setup.ai_character_name}
        />
      </main>

      <footer className="bg-card px-4 py-4 sm:px-6">
        {data.shouldEnd ? (
          <p className="mx-auto mb-3 max-w-3xl text-sm text-muted-foreground">
            Roleplay ended
            {data.endingCondition && data.endingCondition !== "none"
              ? ` (${data.endingCondition.replaceAll("_", " ")})`
              : ""}
            {data.endingRationale ? `: ${data.endingRationale}` : "."}
          </p>
        ) : null}
        <ChatForm
          input={data.input}
          isLoading={data.isLoading}
          error={data.error}
          isEmpty={data.messages.length === 0}
          shouldEnd={data.shouldEnd}
          learnerRole={setup.learner_role}
          inputRef={inputRef}
          onChange={onChange}
          onSubmit={onSubmit}
        />
      </footer>
    </div>
  );
}
