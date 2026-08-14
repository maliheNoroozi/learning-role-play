import { API_URL } from "@/lib/constants";

export async function parseError(
  response: Response,
  fallback: string,
): Promise<string> {
  try {
    const errorBody = (await response.json()) as {
      detail?: string | { msg?: string }[];
    };
    if (typeof errorBody.detail === "string") return errorBody.detail;
    if (Array.isArray(errorBody.detail) && errorBody.detail[0]?.msg) {
      return errorBody.detail[0].msg;
    }
  } catch {
    console.error(fallback);
  }
  return fallback;
}

export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  return fetch(`${API_URL}${path}`, init);
}
