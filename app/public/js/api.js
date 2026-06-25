export async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  const payload = await response.json().catch(() => ({
    status: "failed",
    data: null,
    error: {
      code: "INVALID_JSON_RESPONSE",
      message: "Server tidak mengembalikan JSON valid.",
    },
  }));

  if (!response.ok || payload.status === "failed") {
    const message = payload?.error?.message || `Request gagal: HTTP ${response.status}`;
    const error = new Error(message);
    error.payload = payload;
    throw error;
  }

  return payload.data;
}

export function postJson(url, body) {
  return requestJson(url, {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getJson(url) {
  return requestJson(url, { method: "GET" });
}
