"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import type { WebSocketEvent } from "@/types";

export interface UseWebSocketOptions {
  url?: string;
  projectId?: string;
  onMessage?: (event: WebSocketEvent) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  enabled?: boolean;
}

export interface UseWebSocketReturn {
  isConnected: boolean;
  isConnecting: boolean;
  reconnectAttempts: number;
  lastEvent: WebSocketEvent | null;
  send: (data: Record<string, unknown>) => void;
  disconnect: () => void;
  reconnect: () => void;
}

export function useWebSocket(
  optionsOrParam?: string | UseWebSocketOptions
): UseWebSocketReturn {
  const options: UseWebSocketOptions =
    typeof optionsOrParam === "string"
      ? {
          url:
            optionsOrParam.startsWith("ws://") || optionsOrParam.startsWith("wss://")
              ? optionsOrParam
              : `ws://localhost:8000/ws/${optionsOrParam}`,
        }
      : optionsOrParam || {};

  const {
    url = "",
    onMessage,
    onOpen,
    onClose,
    onError,
    autoReconnect = true,
    reconnectDelay = 3000,
    maxReconnectAttempts = 5,
    enabled = true,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const isMountedRef = useRef(true);

  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null);

  const onMessageRef = useRef(onMessage);
  const onOpenRef = useRef(onOpen);
  const onCloseRef = useRef(onClose);
  const onErrorRef = useRef(onError);

  useEffect(() => {
    onMessageRef.current = onMessage;
    onOpenRef.current = onOpen;
    onCloseRef.current = onClose;
    onErrorRef.current = onError;
  });

  const connect = useCallback(() => {
    if (!enabled || !url || wsRef.current?.readyState === WebSocket.OPEN) return;

    setIsConnecting(true);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!isMountedRef.current) return;
        setIsConnected(true);
        setIsConnecting(false);
        reconnectAttemptsRef.current = 0;
        setReconnectAttempts(0);
        onOpenRef.current?.();
      };

      ws.onmessage = (event) => {
        if (!isMountedRef.current) return;
        try {
          const data: WebSocketEvent = JSON.parse(event.data);
          setLastEvent(data);
          onMessageRef.current?.(data);
        } catch {
          // non-JSON message
        }
      };

      ws.onclose = () => {
        if (!isMountedRef.current) return;
        setIsConnected(false);
        setIsConnecting(false);
        wsRef.current = null;
        onCloseRef.current?.();

        if (
          autoReconnect &&
          reconnectAttemptsRef.current < maxReconnectAttempts
        ) {
          reconnectAttemptsRef.current += 1;
          setReconnectAttempts(reconnectAttemptsRef.current);
          reconnectTimerRef.current = setTimeout(() => {
            if (isMountedRef.current) connect();
          }, reconnectDelay * Math.min(reconnectAttemptsRef.current, 3));
        }
      };

      ws.onerror = (error) => {
        if (!isMountedRef.current) return;
        setIsConnecting(false);
        onErrorRef.current?.(error);
      };
    } catch {
      setIsConnecting(false);
    }
  }, [url, enabled, autoReconnect, reconnectDelay, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    reconnectAttemptsRef.current = 0;
    setReconnectAttempts(0);
    setTimeout(connect, 100);
  }, [connect, disconnect]);

  const send = useCallback((data: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  useEffect(() => {
    isMountedRef.current = true;
    if (enabled && url) connect();
    return () => {
      isMountedRef.current = false;
      disconnect();
    };
  }, [url, enabled, connect, disconnect]);

  return {
    isConnected,
    isConnecting,
    reconnectAttempts,
    lastEvent,
    send,
    disconnect,
    reconnect,
  };
}
