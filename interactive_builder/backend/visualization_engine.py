"""
Advanced Visualization Engine

Generates real-time interactive diagrams including:
- Entity relationship diagrams
- Scenario flow charts
- System architecture diagrams
- Interactive network graphs
"""

import json
import math
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class Node:
    """Visual node in a diagram"""
    id: str
    label: str
    type: str  # entity, actor, system, process, data
    x: float
    y: float
    width: float = 120
    height: float = 60
    color: str = "#3b82f6"
    shape: str = "rectangle"  # rectangle, circle, diamond, hexagon
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass 
class Edge:
    """Visual edge/connection in a diagram"""
    id: str
    source: str
    target: str
    label: str = ""
    type: str = "relationship"  # relationship, flow, dependency, inheritance
    style: str = "solid"  # solid, dashed, dotted
    color: str = "#6b7280"
    animated: bool = False
    bidirectional: bool = False
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class DiagramLayout:
    """Layout configuration for diagrams"""
    type: str  # force, hierarchical, circular, grid
    spacing: float = 150
    center_x: float = 400
    center_y: float = 300
    constraints: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.constraints is None:
            self.constraints = {}

@dataclass
class Diagram:
    """Complete diagram representation"""
    id: str
    title: str
    type: str  # entity_relationship, scenario_flow, architecture, network
    nodes: List[Node]
    edges: List[Edge]
    layout: DiagramLayout
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class DiagramType(Enum):
    ENTITY_RELATIONSHIP = "entity_relationship"
    SCENARIO_FLOW = "scenario_flow"
    SYSTEM_ARCHITECTURE = "architecture"
    NETWORK_GRAPH = "network"
    USER_JOURNEY = "user_journey"

class VisualizationEngine:
    """Main visualization engine for generating interactive diagrams"""
    
    def __init__(self):
        self.node_styles = self._load_node_styles()
        self.layout_algorithms = self._load_layout_algorithms()
        self.color_palettes = self._load_color_palettes()
        
    def generate_entity_relationship_diagram(self, entities: List[Dict], relationships: List[Dict] = None) -> Diagram:
        """Generate an entity relationship diagram from discovered entities"""
        relationships = relationships or []
        
        # Create nodes for entities
        nodes = []
        for i, entity in enumerate(entities):
            node = Node(
                id=f"entity_{entity.get('id', i)}",
                label=entity.get('name', 'Unknown'),
                type=entity.get('type', 'entity'),
                x=0, y=0,  # Will be positioned by layout
                **self._get_entity_style(entity.get('type', 'entity'))
            )
            node.metadata = {
                'description': entity.get('description', ''),
                'confidence': entity.get('confidence', 1.0),
                'source': 'conversation'
            }
            nodes.append(node)
        
        # Create edges for relationships
        edges = []
        for i, rel in enumerate(relationships):
            edge = Edge(
                id=f"rel_{i}",
                source=f"entity_{rel.get('source_id')}",
                target=f"entity_{rel.get('target_id')}",
                label=rel.get('type', 'relates to'),
                type="relationship",
                **self._get_relationship_style(rel.get('type', 'relates to'))
            )
            edges.append(edge)
        
        # Auto-detect relationships from entity descriptions
        auto_edges = self._detect_entity_relationships(entities)
        edges.extend(auto_edges)
        
        # Apply force-directed layout
        layout = DiagramLayout(
            type="force",
            spacing=180,
            constraints={"repulsion": 300, "attraction": 0.01}
        )
        
        # Position nodes using layout algorithm
        positioned_nodes = self._apply_layout(nodes, edges, layout)
        
        return Diagram(
            id="entity_relationship",
            title="Entity Relationships",
            type=DiagramType.ENTITY_RELATIONSHIP.value,
            nodes=positioned_nodes,
            edges=edges,
            layout=layout,
            metadata={"generated_from": "entities", "auto_relationships": len(auto_edges)}
        )
    
    def generate_scenario_flow_diagram(self, scenarios: List[Dict], entities: List[Dict] = None) -> Diagram:
        """Generate a scenario flow diagram showing user journeys and processes"""
        entities = entities or []
        
        nodes = []
        edges = []
        
        for scenario_idx, scenario in enumerate(scenarios):
            scenario_id = scenario.get('id', f'scenario_{scenario_idx}')
            
            # Create nodes for each scenario phase
            given_node = Node(
                id=f"{scenario_id}_given",
                label=f"Given: {scenario.get('given', '')[:30]}...",
                type="precondition",
                x=0, y=0,
                **self._get_scenario_style("given")
            )
            
            when_node = Node(
                id=f"{scenario_id}_when", 
                label=f"When: {scenario.get('when', '')[:30]}...",
                type="trigger",
                x=0, y=0,
                **self._get_scenario_style("when")
            )
            
            then_node = Node(
                id=f"{scenario_id}_then",
                label=f"Then: {scenario.get('then', '')[:30]}...",
                type="outcome",
                x=0, y=0,
                **self._get_scenario_style("then")
            )
            
            nodes.extend([given_node, when_node, then_node])
            
            # Create flow edges
            flow_style = self._get_flow_style()
            edges.append(Edge(
                id=f"{scenario_id}_flow_1",
                source=given_node.id,
                target=when_node.id,
                label="triggers",
                type="flow",
                color=flow_style.get('color', '#10b981'),
                style=flow_style.get('style', 'solid'),
                animated=True
            ))
            
            edges.append(Edge(
                id=f"{scenario_id}_flow_2", 
                source=when_node.id,
                target=then_node.id,
                label="results in",
                type="flow",
                color=flow_style.get('color', '#10b981'),
                style=flow_style.get('style', 'solid'),
                animated=True
            ))
        
        # Connect related scenarios
        scenario_connections = self._detect_scenario_relationships(scenarios)
        edges.extend(scenario_connections)
        
        # Apply hierarchical layout
        layout = DiagramLayout(
            type="hierarchical",
            spacing=200,
            constraints={"direction": "top-to-bottom", "levels": 3}
        )
        
        positioned_nodes = self._apply_layout(nodes, edges, layout)
        
        return Diagram(
            id="scenario_flow",
            title="Scenario Flow",
            type=DiagramType.SCENARIO_FLOW.value,
            nodes=positioned_nodes,
            edges=edges,
            layout=layout,
            metadata={"scenarios": len(scenarios), "auto_connections": len(scenario_connections)}
        )
    
    def generate_system_architecture_diagram(self, entities: List[Dict], scenarios: List[Dict], constraints: List[Dict] = None) -> Diagram:
        """Generate a system architecture diagram from the full specification"""
        constraints = constraints or []
        
        # Classify entities into architectural components
        actors = [e for e in entities if e.get('type') in ['actor', 'user', 'external_system']]
        systems = [e for e in entities if e.get('type') in ['system', 'service', 'component']]
        data = [e for e in entities if e.get('type') in ['data', 'database', 'storage']]
        
        nodes = []
        edges = []
        
        # Create architectural layers
        layers = {
            'presentation': {'y': 100, 'color': '#3b82f6'},
            'business': {'y': 250, 'color': '#10b981'}, 
            'data': {'y': 400, 'color': '#f59e0b'}
        }
        
        # Add actor nodes (external to system)
        for i, actor in enumerate(actors):
            node = Node(
                id=f"actor_{actor.get('id', i)}",
                label=actor.get('name', 'Unknown Actor'),
                type="actor",
                x=50 + i * 150,
                y=50,
                shape="circle",
                color="#8b5cf6",
                width=100,
                height=100
            )
            nodes.append(node)
        
        # Add system components
        for i, system in enumerate(systems):
            layer = self._classify_system_layer(system, scenarios)
            node = Node(
                id=f"system_{system.get('id', i)}",
                label=system.get('name', 'Unknown System'),
                type="system",
                x=200 + i * 180,
                y=layers[layer]['y'],
                color=layers[layer]['color'],
                shape="rectangle"
            )
            nodes.append(node)
        
        # Add data components
        for i, data_entity in enumerate(data):
            node = Node(
                id=f"data_{data_entity.get('id', i)}",
                label=data_entity.get('name', 'Unknown Data'),
                type="data",
                x=200 + i * 180,
                y=layers['data']['y'],
                color=layers['data']['color'],
                shape="cylinder"
            )
            nodes.append(node)
        
        # Analyze scenarios to create interactions
        interaction_edges = self._analyze_scenario_interactions(scenarios, nodes)
        edges.extend(interaction_edges)
        
        # Add constraint annotations
        constraint_nodes = self._create_constraint_annotations(constraints)
        nodes.extend(constraint_nodes)
        
        layout = DiagramLayout(
            type="layered",
            spacing=160,
            constraints={"preserve_layers": True, "layer_separation": 150}
        )
        
        return Diagram(
            id="system_architecture",
            title="System Architecture",
            type=DiagramType.SYSTEM_ARCHITECTURE.value,
            nodes=nodes,
            edges=edges,
            layout=layout,
            metadata={
                "layers": list(layers.keys()),
                "actors": len(actors),
                "systems": len(systems),
                "data_stores": len(data),
                "interactions": len(interaction_edges)
            }
        )
    
    def update_diagram_realtime(self, diagram: Diagram, new_entities: List[Dict] = None, 
                               new_scenarios: List[Dict] = None) -> Diagram:
        """Update an existing diagram with new information in real-time"""
        updated_diagram = diagram
        
        if new_entities:
            # Add new entity nodes
            for entity in new_entities:
                if not any(node.id.endswith(str(entity.get('id', ''))) for node in diagram.nodes):
                    new_node = Node(
                        id=f"entity_{entity.get('id')}",
                        label=entity.get('name', 'New Entity'),
                        type=entity.get('type', 'entity'),
                        x=0, y=0,  # Will be repositioned
                        **self._get_entity_style(entity.get('type', 'entity'))
                    )
                    updated_diagram.nodes.append(new_node)
        
        if new_scenarios:
            # Analyze new scenarios for relationships
            new_edges = self._extract_edges_from_scenarios(new_scenarios, updated_diagram.nodes)
            updated_diagram.edges.extend(new_edges)
        
        # Reapply layout with animation hints
        updated_diagram.nodes = self._apply_incremental_layout(updated_diagram.nodes, updated_diagram.edges)
        
        return updated_diagram
    
    def _load_node_styles(self) -> Dict[str, Dict]:
        """Load visual styles for different node types"""
        return {
            'actor': {'color': '#8b5cf6', 'shape': 'circle', 'width': 100, 'height': 100},
            'user': {'color': '#3b82f6', 'shape': 'circle', 'width': 90, 'height': 90},
            'system': {'color': '#10b981', 'shape': 'rectangle', 'width': 140, 'height': 80},
            'service': {'color': '#059669', 'shape': 'rectangle', 'width': 120, 'height': 70},
            'database': {'color': '#f59e0b', 'shape': 'cylinder', 'width': 100, 'height': 120},
            'data': {'color': '#d97706', 'shape': 'diamond', 'width': 100, 'height': 80},
            'process': {'color': '#ef4444', 'shape': 'hexagon', 'width': 110, 'height': 90},
            'entity': {'color': '#6b7280', 'shape': 'rectangle', 'width': 120, 'height': 60},
            'precondition': {'color': '#3b82f6', 'shape': 'rectangle', 'width': 160, 'height': 60},
            'trigger': {'color': '#10b981', 'shape': 'diamond', 'width': 140, 'height': 80},
            'outcome': {'color': '#f59e0b', 'shape': 'rectangle', 'width': 160, 'height': 60}
        }
    
    def _load_layout_algorithms(self) -> Dict[str, Any]:
        """Load different layout algorithm configurations"""
        return {
            'force': {'repulsion': 300, 'attraction': 0.01, 'iterations': 50},
            'hierarchical': {'direction': 'top-to-bottom', 'layer_separation': 150},
            'circular': {'radius_increment': 100, 'start_radius': 150},
            'grid': {'grid_size': 150, 'columns': 4}
        }
    
    def _load_color_palettes(self) -> Dict[str, List[str]]:
        """Load color palettes for different diagram themes"""
        return {
            'default': ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'],
            'modern': ['#6366f1', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6'],
            'corporate': ['#1f2937', '#374151', '#6b7280', '#9ca3af', '#d1d5db', '#e5e7eb'],
            'vibrant': ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#a855f7']
        }
    
    def _get_entity_style(self, entity_type: str) -> Dict[str, Any]:
        """Get visual style for an entity type"""
        return self.node_styles.get(entity_type, self.node_styles['entity']).copy()
    
    def _get_scenario_style(self, phase: str) -> Dict[str, Any]:
        """Get visual style for scenario phases"""
        return self.node_styles.get(phase, self.node_styles['entity']).copy()
    
    def _get_relationship_style(self, rel_type: str) -> Dict[str, Any]:
        """Get visual style for relationship edges"""
        styles = {
            'contains': {'color': '#10b981', 'style': 'solid'},
            'uses': {'color': '#3b82f6', 'style': 'dashed'},
            'inherits': {'color': '#8b5cf6', 'style': 'solid'},
            'depends_on': {'color': '#f59e0b', 'style': 'dotted'},
            'relates_to': {'color': '#6b7280', 'style': 'solid'}
        }
        return styles.get(rel_type, styles['relates_to'])
    
    def _get_flow_style(self) -> Dict[str, Any]:
        """Get visual style for flow edges"""
        return {'color': '#10b981', 'style': 'solid', 'animated': True}
    
    def _detect_entity_relationships(self, entities: List[Dict]) -> List[Edge]:
        """Automatically detect relationships between entities"""
        edges = []
        
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i >= j:
                    continue
                    
                # Simple heuristic: check if entity names appear in descriptions
                desc1 = entity1.get('description', '').lower()
                desc2 = entity2.get('description', '').lower()
                name1 = entity1.get('name', '').lower()
                name2 = entity2.get('name', '').lower()
                
                relationship = None
                if name2 in desc1:
                    if 'contains' in desc1 or 'has' in desc1:
                        relationship = 'contains'
                    elif 'uses' in desc1 or 'utilizes' in desc1:
                        relationship = 'uses'
                    else:
                        relationship = 'relates_to'
                elif name1 in desc2:
                    if 'contains' in desc2 or 'has' in desc2:
                        relationship = 'contains'
                    elif 'uses' in desc2 or 'utilizes' in desc2:
                        relationship = 'uses'
                    else:
                        relationship = 'relates_to'
                
                if relationship:
                    edge = Edge(
                        id=f"auto_rel_{i}_{j}",
                        source=f"entity_{entity1.get('id', i)}",
                        target=f"entity_{entity2.get('id', j)}",
                        label=relationship.replace('_', ' '),
                        type="auto_relationship",
                        **self._get_relationship_style(relationship)
                    )
                    edge.metadata = {'auto_detected': True, 'confidence': 0.7}
                    edges.append(edge)
        
        return edges
    
    def _detect_scenario_relationships(self, scenarios: List[Dict]) -> List[Edge]:
        """Detect relationships between scenarios"""
        edges = []
        
        for i, scenario1 in enumerate(scenarios):
            for j, scenario2 in enumerate(scenarios):
                if i >= j:
                    continue
                
                # Check if scenario1's outcome enables scenario2's precondition
                then1 = scenario1.get('then', '').lower()
                given2 = scenario2.get('given', '').lower()
                
                # Simple overlap detection
                words1 = set(then1.split())
                words2 = set(given2.split())
                overlap = len(words1.intersection(words2))
                
                if overlap > 2:  # Significant overlap
                    edge = Edge(
                        id=f"scenario_connection_{i}_{j}",
                        source=f"scenario_{i}_then",
                        target=f"scenario_{j}_given",
                        label="enables",
                        type="scenario_flow",
                        style="dashed",
                        color="#8b5cf6"
                    )
                    edge.metadata = {'overlap_score': overlap, 'auto_detected': True}
                    edges.append(edge)
        
        return edges
    
    def _classify_system_layer(self, system: Dict, scenarios: List[Dict]) -> str:
        """Classify a system component into architectural layers"""
        system_name = system.get('name', '').lower()
        system_desc = system.get('description', '').lower()
        
        # Check scenarios for usage patterns
        ui_keywords = ['ui', 'interface', 'frontend', 'web', 'mobile', 'app']
        business_keywords = ['service', 'logic', 'process', 'workflow', 'api']
        data_keywords = ['database', 'storage', 'data', 'repository', 'cache']
        
        all_text = f"{system_name} {system_desc}"
        
        if any(keyword in all_text for keyword in ui_keywords):
            return 'presentation'
        elif any(keyword in all_text for keyword in data_keywords):
            return 'data'
        else:
            return 'business'
    
    def _analyze_scenario_interactions(self, scenarios: List[Dict], nodes: List[Node]) -> List[Edge]:
        """Analyze scenarios to create system interaction edges"""
        edges = []
        
        # Create a mapping of entity names to node IDs
        node_map = {}
        for node in nodes:
            # Extract entity name from node label
            label_words = node.label.lower().split()
            for word in label_words:
                if len(word) > 3:  # Ignore short words
                    node_map[word] = node.id
        
        for i, scenario in enumerate(scenarios):
            scenario_text = f"{scenario.get('when', '')} {scenario.get('then', '')}".lower()
            
            # Find entities mentioned in this scenario
            mentioned_nodes = []
            for word, node_id in node_map.items():
                if word in scenario_text:
                    mentioned_nodes.append(node_id)
            
            # Create interaction edges between mentioned entities
            for j in range(len(mentioned_nodes)):
                for k in range(j + 1, len(mentioned_nodes)):
                    edge = Edge(
                        id=f"interaction_{i}_{j}_{k}",
                        source=mentioned_nodes[j],
                        target=mentioned_nodes[k],
                        label=f"interacts via {scenario.get('title', 'scenario')}",
                        type="interaction",
                        style="dashed",
                        color="#6b7280"
                    )
                    edge.metadata = {'scenario_id': scenario.get('id'), 'interaction_type': 'derived'}
                    edges.append(edge)
        
        return edges
    
    def _create_constraint_annotations(self, constraints: List[Dict]) -> List[Node]:
        """Create visual annotations for constraints"""
        annotation_nodes = []
        
        for i, constraint in enumerate(constraints):
            node = Node(
                id=f"constraint_{i}",
                label=f"⚡ {constraint.get('name', 'Constraint')}",
                type="constraint",
                x=600 + i * 100,
                y=50,
                width=120,
                height=40,
                color="#fbbf24",
                shape="rectangle"
            )
            node.metadata = {
                'constraint_type': constraint.get('category', 'performance'),
                'requirement': constraint.get('requirement', ''),
                'priority': constraint.get('priority', 'medium')
            }
            annotation_nodes.append(node)
        
        return annotation_nodes
    
    def _apply_layout(self, nodes: List[Node], edges: List[Edge], layout: DiagramLayout) -> List[Node]:
        """Apply layout algorithm to position nodes"""
        if layout.type == "force":
            return self._apply_force_layout(nodes, edges, layout)
        elif layout.type == "hierarchical":
            return self._apply_hierarchical_layout(nodes, edges, layout)
        elif layout.type == "circular":
            return self._apply_circular_layout(nodes, layout)
        else:
            return self._apply_grid_layout(nodes, layout)
    
    def _apply_force_layout(self, nodes: List[Node], edges: List[Edge], layout: DiagramLayout) -> List[Node]:
        """Apply force-directed layout algorithm"""
        # Simple force-directed layout implementation
        positioned_nodes = nodes.copy()
        
        # Initialize random positions
        import random
        for i, node in enumerate(positioned_nodes):
            angle = 2 * math.pi * i / len(nodes)
            radius = 200
            node.x = layout.center_x + radius * math.cos(angle) + random.uniform(-50, 50)
            node.y = layout.center_y + radius * math.sin(angle) + random.uniform(-50, 50)
        
        # Apply force iterations
        for iteration in range(layout.constraints.get('iterations', 30)):
            # Repulsion forces
            for i, node1 in enumerate(positioned_nodes):
                for j, node2 in enumerate(positioned_nodes):
                    if i != j:
                        dx = node1.x - node2.x
                        dy = node1.y - node2.y
                        distance = math.sqrt(dx*dx + dy*dy) + 0.1
                        
                        force = layout.constraints.get('repulsion', 300) / (distance * distance)
                        node1.x += force * dx / distance
                        node1.y += force * dy / distance
            
            # Attraction forces (for connected nodes)
            edge_map = {(edge.source, edge.target): True for edge in edges}
            for i, node1 in enumerate(positioned_nodes):
                for j, node2 in enumerate(positioned_nodes):
                    if i != j and (node1.id, node2.id) in edge_map:
                        dx = node2.x - node1.x
                        dy = node2.y - node1.y
                        distance = math.sqrt(dx*dx + dy*dy) + 0.1
                        
                        force = layout.constraints.get('attraction', 0.01) * distance
                        node1.x += force * dx / distance
                        node1.y += force * dy / distance
        
        return positioned_nodes
    
    def _apply_hierarchical_layout(self, nodes: List[Node], edges: List[Edge], layout: DiagramLayout) -> List[Node]:
        """Apply hierarchical layout for scenarios"""
        positioned_nodes = nodes.copy()
        
        # Group nodes by scenario
        scenarios = {}
        for node in positioned_nodes:
            if '_' in node.id:
                scenario_id = node.id.split('_')[0] + '_' + node.id.split('_')[1]
                if scenario_id not in scenarios:
                    scenarios[scenario_id] = []
                scenarios[scenario_id].append(node)
        
        # Position scenarios vertically and phases horizontally
        y_offset = 100
        for scenario_id, scenario_nodes in scenarios.items():
            # Sort by phase (given, when, then)
            phase_order = {'given': 0, 'when': 1, 'then': 2}
            scenario_nodes.sort(key=lambda n: phase_order.get(n.id.split('_')[-1], 3))
            
            x_offset = 150
            for node in scenario_nodes:
                node.x = x_offset
                node.y = y_offset
                x_offset += layout.spacing
            
            y_offset += layout.constraints.get('layer_separation', 150)
        
        return positioned_nodes
    
    def _apply_circular_layout(self, nodes: List[Node], layout: DiagramLayout) -> List[Node]:
        """Apply circular layout"""
        positioned_nodes = nodes.copy()
        
        radius = layout.constraints.get('start_radius', 150)
        for i, node in enumerate(positioned_nodes):
            angle = 2 * math.pi * i / len(nodes)
            node.x = layout.center_x + radius * math.cos(angle)
            node.y = layout.center_y + radius * math.sin(angle)
        
        return positioned_nodes
    
    def _apply_grid_layout(self, nodes: List[Node], layout: DiagramLayout) -> List[Node]:
        """Apply grid layout"""
        positioned_nodes = nodes.copy()
        
        columns = layout.constraints.get('columns', 4)
        grid_size = layout.constraints.get('grid_size', 150)
        
        for i, node in enumerate(positioned_nodes):
            row = i // columns
            col = i % columns
            node.x = layout.center_x + col * grid_size
            node.y = layout.center_y + row * grid_size
        
        return positioned_nodes
    
    def _apply_incremental_layout(self, nodes: List[Node], edges: List[Edge]) -> List[Node]:
        """Apply incremental layout updates for real-time changes"""
        # For now, just apply a simple force layout
        layout = DiagramLayout(type="force", spacing=150)
        return self._apply_force_layout(nodes, edges, layout)
    
    def _extract_edges_from_scenarios(self, scenarios: List[Dict], nodes: List[Node]) -> List[Edge]:
        """Extract new edges from scenario analysis"""
        # This would analyze new scenarios and create appropriate edges
        return []
    
    def to_dict(self, diagram: Diagram) -> Dict[str, Any]:
        """Convert diagram to dictionary for API responses"""
        return {
            'id': diagram.id,
            'title': diagram.title,
            'type': diagram.type,
            'nodes': [asdict(node) for node in diagram.nodes],
            'edges': [asdict(edge) for edge in diagram.edges],
            'layout': asdict(diagram.layout),
            'metadata': diagram.metadata
        }
    
    def get_diagram_statistics(self, diagram: Diagram) -> Dict[str, Any]:
        """Get statistics about a diagram"""
        node_types = {}
        edge_types = {}
        
        for node in diagram.nodes:
            node_types[node.type] = node_types.get(node.type, 0) + 1
        
        for edge in diagram.edges:
            edge_types[edge.type] = edge_types.get(edge.type, 0) + 1
        
        return {
            'total_nodes': len(diagram.nodes),
            'total_edges': len(diagram.edges),
            'node_types': node_types,
            'edge_types': edge_types,
            'layout_type': diagram.layout.type,
            'complexity_score': len(diagram.nodes) + len(diagram.edges) * 0.5
        }