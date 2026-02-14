import { useEffect, useRef, useState, useCallback } from 'react';
import { api } from '../services/api';

interface WsMessage {
  type: string;
  time?: string;
  total?: number;
  platforms?: string[];
}

export function useWebSocket(onMessage?: (msg: WsMessage) => void) {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const mountedRef = useRef(true);

  const connect = useCallback(() => {
    if (!mountedRef.current) return;
    try {
      const ws = new WebSocket(api.getWsUrl());
      wsRef.current = ws;

      ws.onopen = () => { setConnected(true); };
      ws.onclose = () => {
        setConnected(false);
        if (mountedRef.current) {
          reconnectTimer.current = setTimeout(connect, 5000);
        }
      };
      ws.onerror = () => { ws.close(); };
      ws.onmessage = (event) => {
        try {
          const msg: WsMessage = JSON.parse(event.data);
          setLastMessage(msg);
          onMessage?.(msg);
        } catch { /* ignore parse errors */ }
      };
    } catch { /* ignore connection errors */ }
  }, [onMessage]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected, lastMessage };
}
