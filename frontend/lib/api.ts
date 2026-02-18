const base = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function request(path: string, opts: RequestInit) {
  const res = await fetch(base + path, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(opts.headers ?? {})
    }
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export const api = {
  get: <T = any>(path: string) => request(path, { method: "GET" }) as Promise<T>,
  post: <T = any>(path: string, body: any) => request(path, { method: "POST", body: JSON.stringify(body) }) as Promise<T>,
  patch: <T = any>(path: string, body: any) => request(path, { method: "PATCH", body: JSON.stringify(body) }) as Promise<T>,
};
