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

interface ReasoningStreamProps {
  auditId: string;
  level?: ReasoningLevel;
  maxHeight?: string;
  className?: string;
  onEvent?: (event: ReasoningEvent) => void;
  onLevelChange?: (level: ReasoningLevel) => void;
}

export function ReasoningStream({
  auditId,
  level = 'normal',
  maxHeight = '400px',
  className = '',
  onEvent,
  onLevelChange,
}: ReasoningStreamProps) {
  const [events, setEvents] = useState<ReasoningEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [currentLevel, setCurrentLevel] = useState<ReasoningLevel>(level);
  const containerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const prefersReducedMotion = useRef(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    prefersReducedMotion.current = mediaQuery.matches;
    
    const handler = (e: MediaQueryListEvent) => {
      prefersReducedMotion.current = e.matches;
    };
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  const scrollToBottom = useCallback(() => {
    if (containerRef.current && !prefersReducedMotion.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/api/ws/audit/${auditId}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (message) => {
        try {
          const event: ReasoningEvent = JSON.parse(message.data);
          
          setEvents((prev) => {
            if (prev.find((e) => e.id === event.id)) return prev;
            return [...prev, event];
          });
          
          onEvent?.(event);
        } catch (e) {
          console.error('Failed to parse reasoning event:', e);
        }
      };

      ws.onclose = (event) => {
        setConnected(false);
        
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          const delay = Math.min(1000 * 2 ** reconnectAttempts.current, 30000);
          setTimeout(connect, delay);
        }
      };

      ws.onerror = () => {
        setError('Connection error');
        setConnected(false);
      };

      wsRef.current = ws;
    } catch (e) {
      setError('Failed to connect');
    }
  }, [auditId, onEvent]);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounted');
      }
    };
  }, [connect]);

  useEffect(() => {
    scrollToBottom();
  }, [events, scrollToBottom]);

  const handleLevelChange = (newLevel: ReasoningLevel) => {
    setCurrentLevel(newLevel);
    onLevelChange?.(newLevel);
  };

  const getEventIcon = (type: ReasoningEvent['type']) => {
    switch (type) {
      case 'thought': return '💭';
      case 'action': return '⚡';
      case 'observation': return '👁';
      case 'decision': return '🎯';
      case 'error': return '❌';
      default: return '•';
    }
  };

  const getEventColor = (type: ReasoningEvent['type']) => {
    switch (type) {
      case 'thought': return 'text-blue-400';
      case 'action': return 'text-yellow-400';
      case 'observation': return 'text-green-400';
      case 'decision': return 'text-purple-400';
      case 'error': return 'text-red-400';
      default: return 'text-gray-400';
    }
  };

  const shouldShowEvent = (event: ReasoningEvent): boolean => {
    if (currentLevel === 'verbose') return true;
    if (currentLevel === 'minimal') {
      return event.type === 'action' || event.type === 'error';
    }
    return true;
  };

  const filteredEvents = events.filter(shouldShowEvent);

  return (
    <div 
      className={`bg-[#0a0e27] border border-gray-700 rounded-lg ${className}`}
      role="region"
      aria-label="AI Reasoning Stream"
    >
      <div 
        className="flex flex-col sm:flex-row items-start sm:items-center justify-between px-4 py-2 border-b border-gray-700 gap-2"
        role="toolbar"
        aria-label="Reasoning Stream Controls"
      >
        <div className="flex items-center gap-2">
          <span className="font-mono text-sm text-gray-400">Reasoning Stream</span>
          <ConnectionIndicator connected={connected} />
        </div>
        <div className="flex items-center gap-2">
          <LevelSelector level={currentLevel} onChange={handleLevelChange} />
          <span className="text-xs text-gray-500" aria-live="polite">
            {filteredEvents.length} events
          </span>
        </div>
      </div>

      <div
        ref={containerRef}
        className="font-mono text-sm overflow-y-auto p-4"
        style={{ maxHeight }}
        role="log"
        aria-label="Reasoning Events"
        aria-live="polite"
        aria-atomic="false"
        tabIndex={0}
      >
        {error && (
          <div className="text-red-400 mb-2" role="alert">
            <span className="sr-only">Error: </span>⚠ {error}
          </div>
        )}
        
        {!connected && events.length === 0 && (
          <div className="text-gray-500 animate-pulse" aria-busy="true">
            Connecting to reasoning stream...
          </div>
        )}
        
        {filteredEvents.map((event, index) => (
          <div
            key={event.id}
            className={`mb-2 ${getEventColor(event.type)}`}
            role="article"
            aria-label={`${event.type}: ${event.content}`}
          >
            <span className="opacity-50 text-xs mr-2" aria-hidden="true">
              {new Date(event.timestamp).toLocaleTimeString()}
            </span>
            <span className="mr-2" aria-hidden="true">{getEventIcon(event.type)}</span>
            <span>{event.content}</span>
            {event.metadata?.analyzer && (
              <span className="ml-2 text-xs text-gray-500" aria-label={`Analyzer: ${event.metadata.analyzer}`}>
                [{event.metadata.analyzer}]
              </span>
            )}
            {event.metadata?.confidence !== undefined && (
              <span className="ml-2 text-xs text-gray-500" aria-label={`Confidence: ${Math.round(event.metadata.confidence * 100)}%`}>
                ({Math.round(event.metadata.confidence * 100)}%)
              </span>
            )}
          </div>
        ))}
        
        {connected && (
          <div 
            className={`text-[#00ff41] ${!prefersReducedMotion.current ? 'animate-pulse' : ''}`} 
            aria-hidden="true"
          >
            ▊
          </div>
        )}
      </div>
    </div>
  );
}

function ConnectionIndicator({ connected }: { connected: boolean }) {
  return (
    <div
      className={`w-2 h-2 rounded-full ${
        connected ? 'bg-green-500' : 'bg-red-500'
      }`}
      title={connected ? 'Connected' : 'Disconnected'}
      role="status"
      aria-label={connected ? 'Connected to reasoning stream' : 'Disconnected from reasoning stream'}
    >
      <span className="sr-only">
        {connected ? 'Connected' : 'Disconnected'}
      </span>
    </div>
  );
}

function LevelSelector({ level, onChange }: { level: ReasoningLevel; onChange: (level: ReasoningLevel) => void }) {
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleKeyDown = (event: React.KeyboardEvent, option: ReasoningLevel) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onChange(option);
      setIsOpen(false);
    }
    if (event.key === 'Escape') {
      setIsOpen(false);
    }
  };

  return (
    <div 
      ref={containerRef}
      className="relative"
    >
      <button
        type="button"
        className="flex gap-1 text-xs px-2 py-1 rounded border border-gray-600 hover:border-gray-500 focus:outline-none focus:ring-2 focus:ring-[#00ff41] focus:ring-offset-1 focus:ring-offset-[#0a0e27]"
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Detail level: ${level}`}
      >
        {level}
        <span aria-hidden="true">▼</span>
      </button>
      
      {isOpen && (
        <div 
          className="absolute right-0 top-full mt-1 bg-[#0a1627] border border-gray-600 rounded shadow-lg z-10"
          role="listbox"
          aria-label="Select detail level"
        >
          {(['minimal', 'normal', 'verbose'] as ReasoningLevel[]).map((l) => (
            <button
              key={l}
              type="button"
              className={`block w-full text-left px-3 py-1.5 text-xs focus:outline-none focus:bg-[#00ff41]/20 ${
                l === level ? 'text-[#00ff41]' : 'text-gray-400 hover:text-gray-200'
              }`}
              role="option"
              aria-selected={l === level}
              onClick={() => {
                onChange(l);
                setIsOpen(false);
              }}
              onKeyDown={(e) => handleKeyDown(e, l)}
            >
              {l}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default ReasoningStream;
