import { useEffect, useRef, useCallback } from 'react';
import type { EpochMetrics } from '../types/metrics';

export function useWebSocket(
  runId: number | null,
  onMessage: (data: EpochMetrics) => void,
  onComplete?: () => void
) {
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!runId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/runs/${runId}/stream`);

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      if (msg.type === 'epoch') {
        onMessage(msg.data);
      } else if (msg.type === 'complete') {
        onComplete?.();
      }
    };

    ws.onclose = () => {
      // Reconnect after 2s if not intentionally closed
      setTimeout(() => {
        if (wsRef.current === ws) {
          connect();
        }
      }, 2000);
    };

    wsRef.current = ws;
  }, [runId, onMessage, onComplete]);

  useEffect(() => {
    connect();
    return () => {
      const ws = wsRef.current;
      wsRef.current = null;
      ws?.close();
    };
  }, [connect]);

  return wsRef;
}
