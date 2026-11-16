"use client";

import { useEffect, useState } from "react";

// Same-origin /api/hello. The ALB (and the local nginx stand-in) send
// /api/* to the API. This app does not implement that route.
export function HelloFromApi() {
  const [message, setMessage] = useState("loading");

  useEffect(() => {
    let cancelled = false;

    fetch("/api/hello")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        return response.json() as Promise<{ message?: string }>;
      })
      .then((body) => {
        if (!cancelled) {
          setMessage(body.message && body.message.length > 0 ? body.message : "unavailable");
        }
      })
      .catch(() => {
        if (!cancelled) {
          setMessage("unavailable");
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <p>
      API says: <span id="api-message">{message}</span>
    </p>
  );
}
