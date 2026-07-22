import type { RoleplayRequest, RoleplayResponse } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function sendMessage(
  payload: RoleplayRequest,
  signal?: AbortSignal,
): Promise<RoleplayResponse> {
  const response = await fetch(`${API_URL}/roleplay/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal,
  });

  if (!response.ok) {
    let detail = "Failed to get a response from the roleplay API.";
    try {
      const errorBody = (await response.json()) as { detail?: string };
      if (errorBody.detail) detail = errorBody.detail;
    } catch {
      // Keep the default message when the error body is not JSON.
    }
    throw new Error(detail);
  }

  return response.json() as Promise<RoleplayResponse>;
}
