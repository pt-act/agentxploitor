"use client";

import { useState, useRef, useEffect, useCallback } from 'react';

export interface AttackPathNode {
  id: string;
  type: 'entry' | 'vulnerability' | 'exploit' | 'impact' | 'asset';
  label: string;
  severity?: 'critical' | 'high' | 'medium' | 'low';
  metadata?: Record<string, unknown>;
  x?: number;
  y?: number;
}

export interface AttackPathEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  animated?: boolean;
}

export interface AttackPathGraphProps {
  nodes: AttackPathNode[];
  edges: AttackPathEdge[];
  onNodeClick?: (node: AttackPathNode) => void;
  className?: string;
  height?: string;
}

const NODE_COLORS: Record<string, { fill: string; stroke: string; text: string }> = {
  entry: { fill: '#1e40af', stroke: '#3b82f6', text: '#93c5fd' },
  vulnerability: { fill: '#991b1b', stroke: '#ef4444', text: '#fca5a5' },
  exploit: { fill: '#92400e', stroke: '#f59e0b', text: '#fcd34d' },
  impact: { fill: '#7c2d12', stroke: '#f97316', text: '#fdba74' },
  asset: { fill: '#065f46', stroke: '#10b981', text: '#6ee7b7' },
};

const SEVERITY_GLOW: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#eab308',
  low: '#3b82f6',
};

export function AttackPathGraph({
  nodes,
  edges,
  onNodeClick,
  className = '',
  height = '500px',
}: AttackPathGraphProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({ width: rect.width, height: rect.height });
      }
    };

    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const layoutNodes = useCallback(() => {
    const { width, height } = dimensions;
    const padding = 60;
    const nodeWidth = width - padding * 2;
    const nodeHeight = height - padding * 2;

    const typeGroups: Record<string, AttackPathNode[]> = {
      entry: [],
      vulnerability: [],
      exploit: [],
      impact: [],
      asset: [],
    };

    nodes.forEach((node) => {
      if (typeGroups[node.type]) {
        typeGroups[node.type].push(node);
      }
    });

    const layoutOrder = ['entry', 'vulnerability', 'exploit', 'impact', 'asset'] as const;
    const result: AttackPathNode[] = [];

    layoutOrder.forEach((type, colIndex) => {
      const group = typeGroups[type];
      const x = padding + (colIndex / (layoutOrder.length - 1)) * nodeWidth;
      
      group.forEach((node, rowIndex) => {
        const spacing = nodeHeight / (group.length + 1);
        const y = padding + (rowIndex + 1) * spacing;
        result.push({ ...node, x, y });
      });
    });

    return result;
  }, [nodes, dimensions]);

  const positionedNodes = layoutNodes();

  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget || (e.target as SVGElement).tagName === 'svg') {
      setDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (dragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => {
    setDragging(false);
  };

  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setZoom((z) => Math.max(0.5, Math.min(2, z * delta)));
  };

  const handleNodeClick = (node: AttackPathNode) => {
    setSelectedNode(node.id);
    onNodeClick?.(node);
  };

  const renderEdge = (edge: AttackPathEdge) => {
    const source = positionedNodes.find((n) => n.id === edge.source);
    const target = positionedNodes.find((n) => n.id === edge.target);

    if (!source || !target || !source.x || !source.y || !target.x || !target.y) {
      return null;
    }

    const midX = (source.x + target.x) / 2;
    const midY = (source.y + target.y) / 2;

    return (
      <g key={edge.id}>
        <defs>
          <marker
            id={`arrow-${edge.id}`}
            viewBox="0 0 10 10"
            refX="8"
            refY="5"
            markerWidth="6"
            markerHeight="6"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="#6b7280" />
          </marker>
        </defs>
        <path
          d={`M ${source.x} ${source.y} Q ${midX} ${midY - 20} ${target.x} ${target.y}`}
          stroke="#4b5563"
          strokeWidth="2"
          fill="none"
          markerEnd={`url(#arrow-${edge.id})`}
          className={edge.animated ? 'animate-pulse' : ''}
        />
        {edge.label && (
          <text
            x={midX}
            y={midY - 25}
            textAnchor="middle"
            className="fill-gray-500 text-xs"
          >
            {edge.label}
          </text>
        )}
      </g>
    );
  };

  const renderNode = (node: AttackPathNode) => {
    if (!node.x || !node.y) return null;

    const colors = NODE_COLORS[node.type] || NODE_COLORS.vulnerability;
    const isSelected = selectedNode === node.id;
    const isHovered = hoveredNode === node.id;
    const radius = 30;
    const glowColor = node.severity ? SEVERITY_GLOW[node.severity] : null;

    return (
      <g
        key={node.id}
        transform={`translate(${node.x}, ${node.y})`}
        onClick={() => handleNodeClick(node)}
        onMouseEnter={() => setHoveredNode(node.id)}
        onMouseLeave={() => setHoveredNode(null)}
        className="cursor-pointer"
      >
        {glowColor && (
          <circle
            r={radius + 8}
            fill="none"
            stroke={glowColor}
            strokeWidth="2"
            opacity={isSelected || isHovered ? 0.5 : 0.2}
            className="animate-pulse"
          />
        )}
        <circle
          r={radius}
          fill={colors.fill}
          stroke={isSelected ? '#fff' : colors.stroke}
          strokeWidth={isSelected ? 3 : 2}
          className="transition-all duration-200"
        />
        <text
          textAnchor="middle"
          dy="0.35em"
          fill={colors.text}
          className="text-sm font-bold pointer-events-none"
        >
          {node.label.substring(0, 8)}
        </text>
        <text
          y={radius + 15}
          textAnchor="middle"
          className="fill-gray-400 text-xs"
        >
          {node.type}
        </text>
      </g>
    );
  };

  return (
    <div
      ref={containerRef}
      className={`bg-[#0a0e27] border border-gray-700 rounded-lg overflow-hidden ${className}`}
      style={{ height }}
    >
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
        <span className="font-mono text-sm text-gray-400">Attack Path Graph</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { setZoom(1); setPan({ x: 0, y: 0 }); }}
            className="text-xs text-gray-500 hover:text-gray-300"
          >
            Reset View
          </button>
          <span className="text-xs text-gray-500">Zoom: {Math.round(zoom * 100)}%</span>
        </div>
      </div>

      <svg
        width={dimensions.width}
        height={dimensions.height - 40}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
        className={dragging ? 'cursor-grabbing' : 'cursor-grab'}
      >
        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          {edges.map(renderEdge)}
          {positionedNodes.map(renderNode)}
        </g>
      </svg>

      {selectedNode && (
        <NodeDetailsPanel
          node={positionedNodes.find((n) => n.id === selectedNode)}
          onClose={() => setSelectedNode(null)}
        />
      )}
    </div>
  );
}

function NodeDetailsPanel({
  node,
  onClose,
}: {
  node: AttackPathNode | undefined;
  onClose: () => void;
}) {
  if (!node) return null;

  return (
    <div className="absolute bottom-4 left-4 right-4 bg-[#1a1f3a] border border-gray-700 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="text-lg font-bold text-white">{node.label}</h4>
          <p className="text-sm text-gray-400">{node.type}</p>
          {node.severity && (
            <span className={`text-xs uppercase font-bold text-${node.severity === 'critical' ? 'red' : node.severity === 'high' ? 'orange' : 'yellow'}-500`}>
              {node.severity}
            </span>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-gray-500 hover:text-gray-300"
        >
          ✕
        </button>
      </div>
      {node.metadata && (
        <div className="mt-2 text-sm text-gray-300">
          {Object.entries(node.metadata).map(([key, value]) => (
            <div key={key}>
              <span className="text-gray-500">{key}:</span> {String(value)}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AttackPathGraph;
