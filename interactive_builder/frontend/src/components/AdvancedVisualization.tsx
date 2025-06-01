import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { 
  RefreshCw, 
  Download, 
  ZoomIn, 
  ZoomOut, 
  Maximize2, 
  Settings,
  Network,
  GitBranch,
  Box,
  Workflow
} from 'lucide-react';
import { useConversationStore } from '../store/conversationStore';

interface DiagramNode {
  id: string;
  label: string;
  type: string;
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  shape: string;
  metadata?: any;
}

interface DiagramEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
  type: string;
  style: string;
  color: string;
  animated?: boolean;
  metadata?: any;
}

interface Diagram {
  id: string;
  title: string;
  type: string;
  nodes: DiagramNode[];
  edges: DiagramEdge[];
  layout: any;
  metadata?: any;
}

interface AdvancedVisualizationProps {
  className?: string;
}

export const AdvancedVisualization: React.FC<AdvancedVisualizationProps> = ({ 
  className = "" 
}) => {
  const { conversationState, connected } = useConversationStore();
  const [diagram, setDiagram] = useState<Diagram | null>(null);
  const [diagramType, setDiagramType] = useState<string>('auto');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableTypes, setAvailableTypes] = useState<any>({});
  const [viewMode, setViewMode] = useState<'fit' | 'zoom' | 'full'>('fit');
  const [selectedNode, setSelectedNode] = useState<DiagramNode | null>(null);

  // Load available visualization types
  useEffect(() => {
    loadVisualizationTypes();
  }, []);

  // Auto-refresh diagram when conversation state changes
  useEffect(() => {
    if (connected && (conversationState.discovered_entities.length > 0 || conversationState.scenarios.length > 0)) {
      generateVisualization();
    }
  }, [connected, conversationState.discovered_entities.length, conversationState.scenarios.length]);

  // Listen for real-time visualization updates via WebSocket
  useEffect(() => {
    if (typeof window !== 'undefined' && window.socket) {
      const handleVisualizationUpdate = (data: any) => {
        console.log('📊 Received real-time visualization update:', data);
        if (data.diagram) {
          setDiagram(data.diagram);
          setError(null);
        }
      };

      window.socket.on('visualization_update', handleVisualizationUpdate);

      return () => {
        window.socket.off('visualization_update', handleVisualizationUpdate);
      };
    }
  }, [connected]);

  const loadVisualizationTypes = async () => {
    try {
      const response = await fetch('/api/visualization/types');
      if (response.ok) {
        const data = await response.json();
        setAvailableTypes(data.types || {});
      }
    } catch (error) {
      console.error('Failed to load visualization types:', error);
    }
  };

  const generateVisualization = async () => {
    if (!connected) return;

    setIsLoading(true);
    setError(null);

    try {
      // Use session-based visualization API
      const sessionId = 'default'; // In real implementation, get from context
      const response = await fetch(`/api/visualization/${sessionId}?diagram_type=${diagramType}`);
      
      if (response.ok) {
        const data = await response.json();
        setDiagram(data.diagram);
        console.log('📊 Generated visualization:', data.diagram.type, 'with', data.diagram.nodes.length, 'nodes');
      } else {
        throw new Error(`Visualization failed: ${response.statusText}`);
      }
    } catch (error) {
      console.error('Visualization error:', error);
      setError(error instanceof Error ? error.message : 'Failed to generate visualization');
      
      // Create fallback diagram
      setDiagram({
        id: 'fallback',
        title: 'System Overview',
        type: 'entity_relationship',
        nodes: conversationState.discovered_entities.map((entity, index) => ({
          id: entity.id,
          label: entity.name,
          type: entity.type,
          x: 100 + (index % 3) * 200,
          y: 100 + Math.floor(index / 3) * 150,
          width: 120,
          height: 60,
          color: getEntityColor(entity.type),
          shape: 'rectangle'
        })),
        edges: [],
        layout: { type: 'grid' }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getEntityColor = (type: string): string => {
    const colorMap: { [key: string]: string } = {
      'actor': '#8b5cf6',
      'user': '#3b82f6', 
      'system': '#10b981',
      'service': '#059669',
      'database': '#f59e0b',
      'data': '#d97706',
      'process': '#ef4444',
      'entity': '#6b7280'
    };
    return colorMap[type] || '#6b7280';
  };

  const getShapeIcon = (shape: string) => {
    switch (shape) {
      case 'circle': return '●';
      case 'diamond': return '◆';
      case 'hexagon': return '⬢';
      case 'cylinder': return '🗃️';
      default: return '▭';
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'entity_relationship': return <Network className="w-4 h-4" />;
      case 'scenario_flow': return <GitBranch className="w-4 h-4" />;
      case 'architecture': return <Box className="w-4 h-4" />;
      default: return <Workflow className="w-4 h-4" />;
    }
  };

  const handleNodeClick = (node: DiagramNode) => {
    setSelectedNode(selectedNode?.id === node.id ? null : node);
  };

  const downloadDiagram = () => {
    if (!diagram) return;
    
    // Create SVG export (simplified version)
    const svgContent = generateSVG(diagram);
    const blob = new Blob([svgContent], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = `${diagram.title.replace(/\s+/g, '_')}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const generateSVG = (diagram: Diagram): string => {
    const width = 800;
    const height = 600;
    
    let svg = `<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">`;
    svg += `<rect width="100%" height="100%" fill="white"/>`;
    
    // Draw edges first (so they appear behind nodes)
    diagram.edges.forEach(edge => {
      const sourceNode = diagram.nodes.find(n => n.id === edge.source);
      const targetNode = diagram.nodes.find(n => n.id === edge.target);
      
      if (sourceNode && targetNode) {
        const x1 = sourceNode.x + sourceNode.width / 2;
        const y1 = sourceNode.y + sourceNode.height / 2;
        const x2 = targetNode.x + targetNode.width / 2;
        const y2 = targetNode.y + targetNode.height / 2;
        
        svg += `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${edge.color}" stroke-width="2"/>`;
        
        if (edge.label) {
          const midX = (x1 + x2) / 2;
          const midY = (y1 + y2) / 2;
          svg += `<text x="${midX}" y="${midY}" text-anchor="middle" fill="#374151" font-size="12">${edge.label}</text>`;
        }
      }
    });
    
    // Draw nodes
    diagram.nodes.forEach(node => {
      if (node.shape === 'circle') {
        const radius = Math.min(node.width, node.height) / 2;
        svg += `<circle cx="${node.x + node.width/2}" cy="${node.y + node.height/2}" r="${radius}" fill="${node.color}" stroke="#374151" stroke-width="2"/>`;
      } else {
        svg += `<rect x="${node.x}" y="${node.y}" width="${node.width}" height="${node.height}" fill="${node.color}" stroke="#374151" stroke-width="2" rx="4"/>`;
      }
      
      svg += `<text x="${node.x + node.width/2}" y="${node.y + node.height/2}" text-anchor="middle" dominant-baseline="middle" fill="white" font-size="14" font-weight="bold">${node.label}</text>`;
    });
    
    svg += '</svg>';
    return svg;
  };

  const diagramStats = useMemo(() => {
    if (!diagram) return null;
    
    const nodeTypes = diagram.nodes.reduce((acc, node) => {
      acc[node.type] = (acc[node.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
    
    return {
      totalNodes: diagram.nodes.length,
      totalEdges: diagram.edges.length,
      nodeTypes,
      complexity: diagram.nodes.length + diagram.edges.length * 0.5
    };
  }, [diagram]);

  if (!connected) {
    return (
      <div className={`flex items-center justify-center h-64 text-gray-500 ${className}`}>
        <div className="text-center">
          <Network className="w-12 h-12 mx-auto mb-2 opacity-50" />
          <p>Connect to start visualizing your system</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Controls */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              {diagram && getTypeIcon(diagram.type)}
              {diagram ? diagram.title : 'System Visualization'}
            </CardTitle>
            <div className="flex items-center gap-2">
              <select
                value={diagramType}
                onChange={(e) => setDiagramType(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded text-sm"
              >
                <option value="auto">Auto Select</option>
                {Object.entries(availableTypes).map(([key, type]: [string, any]) => (
                  <option key={key} value={key}>
                    {type.name}
                  </option>
                ))}
              </select>
              
              <Button
                variant="outline"
                size="sm"
                onClick={generateVisualization}
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
              
              {diagram && (
                <Button variant="outline" size="sm" onClick={downloadDiagram}>
                  <Download className="w-4 h-4" />
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        
        {diagramStats && (
          <CardContent className="pt-0">
            <div className="flex items-center gap-4 text-sm text-gray-600">
              <span>{diagramStats.totalNodes} nodes</span>
              <span>{diagramStats.totalEdges} connections</span>
              <span>Complexity: {diagramStats.complexity.toFixed(1)}</span>
              <div className="flex gap-1">
                {Object.entries(diagramStats.nodeTypes).map(([type, count]) => (
                  <Badge key={type} variant="secondary" className="text-xs">
                    {type}: {count}
                  </Badge>
                ))}
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* Diagram Display */}
      <Card className="min-h-[500px]">
        <CardContent className="p-0">
          {error && (
            <div className="p-6 text-center text-red-600">
              <p>⚠️ {error}</p>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={generateVisualization}
                className="mt-2"
              >
                Retry
              </Button>
            </div>
          )}
          
          {isLoading && (
            <div className="flex items-center justify-center h-64">
              <div className="text-center">
                <RefreshCw className="w-8 h-8 mx-auto mb-2 animate-spin text-blue-600" />
                <p className="text-gray-600">Generating visualization...</p>
              </div>
            </div>
          )}
          
          {diagram && !isLoading && (
            <div className="relative">
              {/* SVG Diagram */}
              <svg
                width="100%"
                height="500"
                viewBox="0 0 800 500"
                className="border-b border-gray-200"
              >
                {/* Background */}
                <rect width="100%" height="100%" fill="#fafafa" />
                
                {/* Grid */}
                <defs>
                  <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" strokeWidth="0.5"/>
                  </pattern>
                </defs>
                <rect width="100%" height="100%" fill="url(#grid)" />
                
                {/* Edges */}
                {diagram.edges.map(edge => {
                  const sourceNode = diagram.nodes.find(n => n.id === edge.source);
                  const targetNode = diagram.nodes.find(n => n.id === edge.target);
                  
                  if (!sourceNode || !targetNode) return null;
                  
                  const x1 = sourceNode.x + sourceNode.width / 2;
                  const y1 = sourceNode.y + sourceNode.height / 2;
                  const x2 = targetNode.x + targetNode.width / 2;
                  const y2 = targetNode.y + targetNode.height / 2;
                  
                  return (
                    <g key={edge.id}>
                      <line
                        x1={x1}
                        y1={y1}
                        x2={x2}
                        y2={y2}
                        stroke={edge.color}
                        strokeWidth="2"
                        strokeDasharray={edge.style === 'dashed' ? '5,5' : undefined}
                        markerEnd="url(#arrowhead)"
                      />
                      {edge.label && (
                        <text
                          x={(x1 + x2) / 2}
                          y={(y1 + y2) / 2 - 5}
                          textAnchor="middle"
                          fill="#374151"
                          fontSize="10"
                          className="pointer-events-none"
                        >
                          {edge.label}
                        </text>
                      )}
                    </g>
                  );
                })}
                
                {/* Arrow marker */}
                <defs>
                  <marker
                    id="arrowhead"
                    markerWidth="10"
                    markerHeight="7"
                    refX="9"
                    refY="3.5"
                    orient="auto"
                  >
                    <polygon
                      points="0 0, 10 3.5, 0 7"
                      fill="#6b7280"
                    />
                  </marker>
                </defs>
                
                {/* Nodes */}
                {diagram.nodes.map(node => (
                  <g 
                    key={node.id} 
                    className="cursor-pointer hover:opacity-80 transition-opacity"
                    onClick={() => handleNodeClick(node)}
                  >
                    {node.shape === 'circle' ? (
                      <circle
                        cx={node.x + node.width / 2}
                        cy={node.y + node.height / 2}
                        r={Math.min(node.width, node.height) / 2}
                        fill={node.color}
                        stroke={selectedNode?.id === node.id ? "#1f2937" : "#374151"}
                        strokeWidth={selectedNode?.id === node.id ? "3" : "2"}
                      />
                    ) : (
                      <rect
                        x={node.x}
                        y={node.y}
                        width={node.width}
                        height={node.height}
                        fill={node.color}
                        stroke={selectedNode?.id === node.id ? "#1f2937" : "#374151"}
                        strokeWidth={selectedNode?.id === node.id ? "3" : "2"}
                        rx="4"
                      />
                    )}
                    
                    <text
                      x={node.x + node.width / 2}
                      y={node.y + node.height / 2}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="white"
                      fontSize="12"
                      fontWeight="bold"
                      className="pointer-events-none"
                    >
                      {node.label.length > 15 ? `${node.label.slice(0, 12)}...` : node.label}
                    </text>
                    
                    <text
                      x={node.x + node.width / 2}
                      y={node.y + node.height / 2 + 12}
                      textAnchor="middle"
                      dominantBaseline="middle"
                      fill="white"
                      fontSize="9"
                      className="pointer-events-none"
                    >
                      {getShapeIcon(node.shape)} {node.type}
                    </text>
                  </g>
                ))}
              </svg>
              
              {/* Node Details Panel */}
              {selectedNode && (
                <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-4 max-w-xs border">
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-semibold text-gray-900">{selectedNode.label}</h4>
                    <button
                      onClick={() => setSelectedNode(null)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      ×
                    </button>
                  </div>
                  <div className="space-y-1 text-sm">
                    <div><span className="font-medium">Type:</span> {selectedNode.type}</div>
                    <div><span className="font-medium">Shape:</span> {selectedNode.shape}</div>
                    {selectedNode.metadata && (
                      <div className="mt-2">
                        <span className="font-medium">Details:</span>
                        <pre className="text-xs bg-gray-50 p-2 rounded mt-1 overflow-auto">
                          {JSON.stringify(selectedNode.metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {!diagram && !isLoading && !error && (
            <div className="flex items-center justify-center h-64 text-gray-500">
              <div className="text-center">
                <Workflow className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p>Start describing your system to see visualizations</p>
                <p className="text-sm mt-1">Add entities and scenarios to generate diagrams</p>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Diagram Type Info */}
      {diagram && availableTypes[diagram.type] && (
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-start gap-3">
              {getTypeIcon(diagram.type)}
              <div>
                <h4 className="font-medium text-gray-900">{availableTypes[diagram.type].name}</h4>
                <p className="text-sm text-gray-600 mt-1">{availableTypes[diagram.type].description}</p>
                <p className="text-xs text-gray-500 mt-2">
                  <span className="font-medium">Best for:</span> {availableTypes[diagram.type].best_for}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};