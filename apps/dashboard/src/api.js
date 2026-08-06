// fetch wrapper: attaches Clerk token, JSON, structured errors, 401 handling.
// Dev: vite proxy /api → localhost:8000 (strips /api). Prod: same base.

import { useAuth } from "@clerk/clerk-react";

const BASE = import.meta.env.VITE_API_BASE ?? "/api";

export class ApiError extends Error {
  constructor(status, message, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

function payload(r) {
  return r.status === 204 ? null : r.json();
}

async function request(token, method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: body == null ? undefined : JSON.stringify(body),
  });

  const data = await payload(res).catch(() => null);
  if (!res.ok) {
    const msg = data?.error?.message ?? `Request failed (${res.status})`;
    throw new ApiError(res.status, msg, data?.error?.details);
  }
  return data;
}

// React hook — only usable inside components under ClerkProvider
export function useApi() {
  const mock = import.meta.env.VITE_MOCK_AUTH === "true";
  const { getToken } = mock ? { getToken: async () => "mock-token" } : useAuth();

  const call = async (method, path, body) => {
    const token = await getToken();
    return request(token, method, path, body);
  };

  return {
    get: (p) => call("GET", p),
    post: (p, b) => call("POST", p, b),
    patch: (p, b) => call("PATCH", p, b),
    put: (p, b) => call("PUT", p, b),
    del: (p) => call("DELETE", p),
  };
}
