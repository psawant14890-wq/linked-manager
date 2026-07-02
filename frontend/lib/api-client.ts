import axios from "axios";
import { getSession } from "next-auth/react";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const apiClient = axios.create({
  baseURL: API_URL,
});

// Every request picks up the backend JWT that NextAuth stored in the
// session (see lib/auth.ts) -- the FastAPI backend is a separate service
// from the Next.js app, so it verifies this token itself rather than
// trusting NextAuth's own session cookie.
apiClient.interceptors.request.use(async (config) => {
  const session = await getSession();
  const token = (session as { accessToken?: string } | null)?.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

/**
 * Opens an authenticated SSE stream via fetch (EventSource doesn't support
 * custom headers, so POST+stream endpoints are consumed manually here).
 * Calls onToken for each `token` event and resolves with the full text
 * once a `done` event arrives.
 */
export async function streamSSE(
  path: string,
  body: unknown,
  handlers: {
    onToken?: (text: string) => void;
    onEvent?: (event: string, data: any) => void;
    onError?: (message: string) => void;
  }
): Promise<void> {
  const session = await getSession();
  const token = (session as { accessToken?: string } | null)?.accessToken;

  const response = await fetch(`${API_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
  });

  if (!response.ok || !response.body) {
    handlers.onError?.(`Request failed with status ${response.status}`);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";

    for (const chunk of chunks) {
      const lines = chunk.split("\n");
      let event = "message";
      let data = "";
      for (const line of lines) {
        if (line.startsWith("event:")) event = line.slice(6).trim();
        if (line.startsWith("data:")) data = line.slice(5).trim();
      }
      if (!data) continue;

      let parsed: any;
      try {
        parsed = JSON.parse(data);
      } catch {
        parsed = data;
      }

      handlers.onEvent?.(event, parsed);
      if (event === "token" && parsed?.text) {
        handlers.onToken?.(parsed.text);
      }
      if (event === "error") {
        handlers.onError?.(parsed?.message ?? "Stream error");
      }
    }
  }
}
