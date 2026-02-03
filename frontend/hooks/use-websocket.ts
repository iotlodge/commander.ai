"use client";

import { useEffect, useState, useRef } from "react";
import { TaskWebSocketClient } from "@/lib/websocket";
import { WebSocketEvent } from "@/lib/types";

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const clientRef = useRef<TaskWebSocketClient | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    let connectTimer: NodeJS.Timeout;

    // Small delay to prevent rapid connect/disconnect cycles
    connectTimer = setTimeout(() => {
      if (!mountedRef.current) return;

      const wsClient = new TaskWebSocketClient(
        userId,
        (event) => {
          if (mountedRef.current) {
            setEvents((prev) => [...prev, event]);
          }
        },
        () => {
          if (mountedRef.current) {
            setIsConnected(true);
          }
        },
        () => {
          if (mountedRef.current) {
            setIsConnected(false);
          }
        }
      );

      wsClient.connect();
      clientRef.current = wsClient;
    }, 150); // 150ms delay to stabilize mounting

    return () => {
      mountedRef.current = false;
      clearTimeout(connectTimer);

      // Disconnect the client
      if (clientRef.current) {
        clientRef.current.disconnect();
        clientRef.current = null;
      }
    };
  }, [userId]);

  return { isConnected, events, client: clientRef.current };
}
