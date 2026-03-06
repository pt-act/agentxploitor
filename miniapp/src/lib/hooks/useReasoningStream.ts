"use client";

import { useEffect, useState, useRef, useCallback } from 'react';

export type ReasoningLevel = 'minimal' | 'normal' | 'verbose';

export interface ReasoningEvent {
  id: string;
  timestamp: string;
  type: 'thought' | 'action' | 'observation' | 'decision' | 'error';
  content: string;
  metadata?: {
    step?: number;
    totalSteps?: number;
    analyzer?: string;
    confidence?: number;
    duration?: number;
  };
}

export interface UseReasoningStreamOptions {
  auditId: string;
  level?: ReasoningLevel;
  pollInterval?: number;
  useWebSocket?: boolean;
  maxEvents?: number;
  onError?: (error: Error) => void;
  onEvent?: (event: ReasoningEvent) => void;
}

export interface UseReasoningStreamReturn {
  events: ReasoningEvent[];
  connected: boolean;
  error: string | null;
  isLoading: boolean;
  clear: () => void;
  reconnect: () => void;
}

export function useReasoningStream({
  auditId,
  level = 'normal',
  pollInterval = 2000,
  useWebSocket = false,
  maxEvents = 500,
  onError,
  onEvent,
}: UseReasoningStreamOptions): UseReasoningStreamReturn {
  const [events, setEvents] = useState<ReasoningEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  const wsRef = useRef<WebSocket | null>(null);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastTimestampRef = useRef<string | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const addEvent = useCallback(
    (event: ReasoningEvent) => {
      setEvents((prev) => {
        if (prev.find((e) => e.id === event.id)) return prev;
        const newEvents = [...prev, event];
        if (newEvents.length > maxEvents) {
          return newEvents.slice(-maxEvents);
        }
        return newEvents;
      });
      onEvent?.(event);
    },
    [maxEvents, onEvent]
  );

  const connectWebSocket = useCallback(() => {
    if (typeof window === 'undefined') return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/ws/audit/${auditId}/reasoning`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnected(true);
        setError(null);
        setIsLoading(false);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (message) => {
        try {
          const event: ReasoningEvent = JSON.parse(message.data);
          addEvent(event);
          lastTimestampRef.current = event.timestamp;
        } catch (e) {
          console.error('Failed to parse reasoning event:', e);
        }
      };

      ws.onclose = (event) => {
        setConnected(false);
        
        if (
          event.code !== 1000 &&
          reconnectAttempts.current < maxReconnectAttempts
        ) {
          reconnectAttempts.current++;
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
          setTimeout(connectWebSocket, delay);
        }
      };

      ws.onerror = () => {
        setError('WebSocket connection error');
        setConnected(false);
        setIsLoading(false);
        onError?.(new Error('WebSocket connection error'));
      };

      wsRef.current = ws;
    } catch (e) {
      setError('Failed to create WebSocket');
      setIsLoading(false);
      onError?.(e instanceof Error ? e : new Error('Unknown error'));
    }
  }, [auditId, addEvent, onError]);

  const pollEvents = useCallback(async () => {
    try {
      const params = new URLSearchParams({
        limit: '50',
        ...(lastTimestampRef.current && { since: lastTimestampRef.current }),
      });

      const response = await fetch(
        `/api/reasoning/${auditId}?${params.toString()}`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();

      setConnected(true);
      setError(null);
      setIsLoading(false);

      if (data.events && Array.isArray(data.events)) {
        data.events.forEach((event: ReasoningEvent) => {
          addEvent(event);
          if (
            !lastTimestampRef.current ||
            new Date(event.timestamp) > new Date(lastTimestampRef.current)
          ) {
            lastTimestampRef.current = event.timestamp;
          }
        });
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Polling error');
      setConnected(false);
      setIsLoading(false);
      onError?.(e instanceof Error ? e : new Error('Polling error'));
    }
  }, [auditId, addEvent, onError]);

  const clear = useCallback(() => {
    setEvents([]);
    lastTimestampRef.current = null;
  }, []);

  const reconnect = useCallback(() => {
    reconnectAttempts.current = 0;
    if (useWebSocket) {
      connectWebSocket();
    } else {
      pollEvents();
    }
  }, [useWebSocket, connectWebSocket, pollEvents]);

  useEffect(() => {
    if (useWebSocket) {
      connectWebSocket();
    } else {
      pollEvents();
      pollIntervalRef.current = setInterval(pollEvents, pollInterval);
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, [useWebSocket, connectWebSocket, pollEvents, pollInterval]);

  const filteredEvents = events.filter((event) => {
    if (level === 'verbose') return true;
    if (level === 'minimal') {
      return event.type === 'action' || event.type === 'error';
    }
    return true;
  });

  return {
    events: filteredEvents,
    connected,
    error,
    isLoading,
    clear,
    reconnect,
  };
}

export default useReasoningStream;
