import type { RoleplayChatRequest, RoleplayChatResponse } from "@/lib/types";
import { apiFetch, parseError } from "@/lib/api/client";

export async function sendMessage(
  payload: RoleplayChatRequest,
  signal?: AbortSignal,
): Promise<RoleplayChatResponse> {
  const response = await apiFetch("/roleplays/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Failed to send the message."));
  }

  return response.json() as Promise<RoleplayChatResponse>;
}
