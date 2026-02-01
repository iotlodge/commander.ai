"use client";

import { useEffect, useState } from "react";
import { TaskWebSocketClient } from "@/lib/websocket";
import { WebSocketEvent } from "@/lib/types";

export function useWebSocket(userId: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [events, setEvents] = useState<WebSocketEvent[]>([]);
  const [client, setClient] = useState<TaskWebSocketClient | null>(null);

  useEffect(() => {
    const wsClient = new TaskWebSocketClient(
      userId,
      (event) => {
        setEvents((prev) => [...prev, event]);
      },
      () => setIsConnected(true),
      () => setIsConnected(false)
    );

    wsClient.connect();
    setClient(wsClient);

    return () => {
      wsClient.disconnect();
    };
  }, [userId]);

  return { isConnected, events, client };
}
