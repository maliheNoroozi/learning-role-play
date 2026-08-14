import type {
  CreateRoleplayRequest,
  CreateRoleplayResponse,
} from "@/lib/types";
import { apiFetch, parseError } from "@/lib/api/client";

export async function createRoleplay(
  payload: CreateRoleplayRequest,
  signal?: AbortSignal,
): Promise<CreateRoleplayResponse> {
  const response = await apiFetch("/roleplays", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    throw new Error(await parseError(response, "Failed to create a roleplay."));
  }

  return response.json() as Promise<CreateRoleplayResponse>;
}
