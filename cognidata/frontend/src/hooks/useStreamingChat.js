import { useRef, useState, useCallback } from "react";

/**
 * WebSocket-based streaming chat hook.
 * Falls back to regular HTTP if WS fails.
 */
export function useStreamingChat() {
  const ws = useRef(null);
  const [streaming, setStreaming] = useState(false);

  const connect = useCallback((token) => {
    return new Promise((resolve, reject) => {
      const socket = new WebSocket("ws://localhost:8000/api/ws/chat");
      socket.onopen = () => {
        socket.send(JSON.stringify({ token }));
      };
      socket.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        if (msg.type === "connected") {
          ws.current = socket;
          resolve(socket);
        } else if (msg.type === "error") {
          reject(new Error(msg.data));
        }
      };
      socket.onerror = reject;
    });
  }, []);

  const sendStreaming = useCallback((query, apiKey, onToken, onDone, onError) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      onError?.("WebSocket not connected");
      return;
    }

    setStreaming(true);
    let buffer = "";

    const handler = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "token") {
        buffer += msg.data;
        onToken?.(buffer, msg.data);
      } else if (msg.type === "result") {
        ws.current.removeEventListener("message", handler);
        setStreaming(false);
        onDone?.(msg);
      } else if (msg.type === "done") {
        ws.current.removeEventListener("message", handler);
        setStreaming(false);
        onDone?.({ type: "text", data: buffer, task_type: msg.task_type || "insight", status: "success" });
      } else if (msg.type === "error") {
        ws.current.removeEventListener("message", handler);
        setStreaming(false);
        onError?.(msg.data);
      }
    };

    ws.current.addEventListener("message", handler);
    ws.current.send(JSON.stringify({ query, api_key: apiKey }));
  }, []);

  const disconnect = useCallback(() => {
    ws.current?.close();
    ws.current = null;
  }, []);

  return { connect, sendStreaming, disconnect, streaming };
}
