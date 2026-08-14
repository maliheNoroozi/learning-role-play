"use client";

import { useSyncExternalStore } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import ChatView from "@/components/Chat/ChatView";
import { loadRoleplaySetup } from "@/lib/session";

const emptySubscribe = () => () => {};

export default function RoleplayChatPage() {
  const params = useParams<{ id: string }>();
  const roleplayId = params.id;
  const hydrated = useSyncExternalStore(
    emptySubscribe,
    () => true,
    () => false,
  );

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-muted-foreground">
        Loading session…
      </div>
    );
  }

  const setup = loadRoleplaySetup(roleplayId);

  if (!setup) {
    return (
      <div className="mx-auto flex min-h-screen max-w-lg flex-col items-center justify-center gap-4 px-4 text-center">
        <h1 className="text-2xl font-semibold tracking-tight">
          Session not found
        </h1>
        <p className="text-muted-foreground">
          This roleplay setup is not available in this browser. Create a new
          roleplay to continue.
        </p>
        <Link href="/" className="text-sm underline underline-offset-4">
          Back to setup
        </Link>
      </div>
    );
  }

  return <ChatView roleplayId={roleplayId} setup={setup} />;
}
