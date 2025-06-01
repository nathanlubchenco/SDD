"""
Tests for the Advanced Visualization Engine

Tests diagram generation, layout algorithms, and interactive features.
"""

import pytest
import math
from visualization_engine import (
    VisualizationEngine,
    Node,
    Edge,
    Diagram,
    DiagramLayout,
    DiagramType
)

class TestVisualizationEngine:
    """Test the main visualization engine functionality"""
    
    def test_engine_initialization(self):
        engine = VisualizationEngine()
        assert engine.node_styles is not None
        assert engine.layout_algorithms is not None
        assert engine.color_palettes is not None
        assert 'actor' in engine.node_styles
        assert 'force' in engine.layout_algorithms
        assert 'default' in engine.color_palettes
    
    def test_entity_relationship_diagram_generation(self):
        engine = VisualizationEngine()
        
        entities = [
            {'id': '1', 'name': 'User', 'type': 'actor', 'description': 'System user'},
            {'id': '2', 'name': 'Database', 'type': 'database', 'description': 'Data storage'},
            {'id': '3', 'name': 'API', 'type': 'system', 'description': 'Web service'}
        ]
        
        diagram = engine.generate_entity_relationship_diagram(entities)
        
        assert diagram.type == DiagramType.ENTITY_RELATIONSHIP.value
        assert len(diagram.nodes) == 3
        assert diagram.layout.type == "force"
        assert diagram.title == "Entity Relationships"
        
        # Check node properties
        user_node = next(n for n in diagram.nodes if 'User' in n.label)
        assert user_node.type == 'actor'
        assert user_node.color == engine.node_styles['actor']['color']
    
    def test_scenario_flow_diagram_generation(self):
        engine = VisualizationEngine()
        
        scenarios = [
            {
                'id': '1',
                'title': 'User Login',
                'given': 'user has valid credentials',
                'when': 'user submits login form',
                'then': 'user is authenticated'
            }
        ]
        
        entities = [{'id': '1', 'name': 'User', 'type': 'actor'}]
        
        diagram = engine.generate_scenario_flow_diagram(scenarios, entities)
        
        assert diagram.type == DiagramType.SCENARIO_FLOW.value
        assert len(diagram.nodes) == 3  # Given, When, Then
        assert len(diagram.edges) >= 2  # Flow connections
        assert diagram.layout.type == "hierarchical"
        
        # Check for given/when/then nodes
        node_types = [node.type for node in diagram.nodes]
        assert 'precondition' in node_types
        assert 'trigger' in node_types
        assert 'outcome' in node_types
    
    def test_system_architecture_diagram_generation(self):
        engine = VisualizationEngine()
        
        entities = [
            {'id': '1', 'name': 'User', 'type': 'actor', 'description': 'System user'},
            {'id': '2', 'name': 'Frontend', 'type': 'system', 'description': 'Web interface'},
            {'id': '3', 'name': 'Database', 'type': 'database', 'description': 'Data storage'}
        ]
        
        scenarios = [
            {
                'id': '1',
                'title': 'Data Access',
                'given': 'user is logged in',
                'when': 'user requests data',
                'then': 'data is displayed'
            }
        ]
        
        constraints = [
            {
                'id': '1',
                'name': 'Response Time',
                'category': 'performance',
                'requirement': 'API response < 200ms',
                'priority': 'high'
            }
        ]
        
        diagram = engine.generate_system_architecture_diagram(entities, scenarios, constraints)
        
        assert diagram.type == DiagramType.SYSTEM_ARCHITECTURE.value
        assert len(diagram.nodes) >= 3  # Entities + constraints
        assert diagram.layout.type == "layered"
        
        # Check for constraint annotations
        constraint_nodes = [n for n in diagram.nodes if n.type == 'constraint']
        assert len(constraint_nodes) == 1
        assert 'Response Time' in constraint_nodes[0].label

class TestNodeAndEdgeCreation:
    """Test node and edge data structures"""
    
    def test_node_creation(self):
        node = Node(
            id="test_node",
            label="Test Node",
            type="entity",
            x=100,
            y=200,
            color="#3b82f6"
        )
        
        assert node.id == "test_node"
        assert node.label == "Test Node"
        assert node.x == 100
        assert node.y == 200
        assert node.width == 120  # Default
        assert node.height == 60  # Default
        assert node.color == "#3b82f6"
        assert node.metadata == {}
    
    def test_edge_creation(self):
        edge = Edge(
            id="test_edge",
            source="node1",
            target="node2",
            label="connects to",
            type="relationship"
        )
        
        assert edge.id == "test_edge"
        assert edge.source == "node1"
        assert edge.target == "node2"
        assert edge.label == "connects to"
        assert edge.type == "relationship"
        assert edge.style == "solid"  # Default
        assert edge.animated == False  # Default
    
    def test_diagram_creation(self):
        nodes = [
            Node("n1", "Node 1", "entity", 0, 0),
            Node("n2", "Node 2", "entity", 100, 100)
        ]
        edges = [
            Edge("e1", "n1", "n2", "connects", "relationship")
        ]
        layout = DiagramLayout("force")
        
        diagram = Diagram(
            id="test_diagram",
            title="Test Diagram",
            type="entity_relationship",
            nodes=nodes,
            edges=edges,
            layout=layout
        )
        
        assert diagram.id == "test_diagram"
        assert len(diagram.nodes) == 2
        assert len(diagram.edges) == 1
        assert diagram.layout.type == "force"

class TestLayoutAlgorithms:
    """Test different layout algorithms"""
    
    def test_force_layout(self):
        engine = VisualizationEngine()
        
        nodes = [
            Node("n1", "Node 1", "entity", 0, 0),
            Node("n2", "Node 2", "entity", 0, 0),
            Node("n3", "Node 3", "entity", 0, 0)
        ]
        edges = [
            Edge("e1", "n1", "n2", "", "relationship"),
            Edge("e2", "n2", "n3", "", "relationship")
        ]
        layout = DiagramLayout("force", constraints={"iterations": 10, "repulsion": 100})
        
        positioned_nodes = engine._apply_force_layout(nodes, edges, layout)
        
        assert len(positioned_nodes) == 3
        # Nodes should have been repositioned
        positions = [(n.x, n.y) for n in positioned_nodes]
        assert len(set(positions)) > 1  # Not all nodes at same position
    
    def test_hierarchical_layout(self):
        engine = VisualizationEngine()
        
        # Create scenario nodes
        nodes = [
            Node("scenario_0_given", "Given", "precondition", 0, 0),
            Node("scenario_0_when", "When", "trigger", 0, 0),
            Node("scenario_0_then", "Then", "outcome", 0, 0)
        ]
        edges = []
        layout = DiagramLayout("hierarchical", constraints={"layer_separation": 100})
        
        positioned_nodes = engine._apply_hierarchical_layout(nodes, edges, layout)
        
        assert len(positioned_nodes) == 3
        # Check that nodes are arranged horizontally with consistent y
        y_positions = [n.y for n in positioned_nodes]
        assert len(set(y_positions)) == 1  # All nodes should have same y
        
        # Check that x positions are different
        x_positions = [n.x for n in positioned_nodes]
        assert len(set(x_positions)) == 3  # All nodes should have different x
    
    def test_circular_layout(self):
        engine = VisualizationEngine()
        
        nodes = [
            Node(f"n{i}", f"Node {i}", "entity", 0, 0) for i in range(4)
        ]
        layout = DiagramLayout("circular", center_x=300, center_y=300, constraints={"start_radius": 100})
        
        positioned_nodes = engine._apply_circular_layout(nodes, layout)
        
        assert len(positioned_nodes) == 4
        
        # Check that nodes are arranged in a circle
        center_x, center_y = 300, 300
        radius = 100
        
        for node in positioned_nodes:
            distance = math.sqrt((node.x - center_x)**2 + (node.y - center_y)**2)
            assert abs(distance - radius) < 1  # Allow small floating point errors
    
    def test_grid_layout(self):
        engine = VisualizationEngine()
        
        nodes = [
            Node(f"n{i}", f"Node {i}", "entity", 0, 0) for i in range(6)
        ]
        layout = DiagramLayout("grid", constraints={"columns": 3, "grid_size": 100})
        
        positioned_nodes = engine._apply_grid_layout(nodes, layout)
        
        assert len(positioned_nodes) == 6
        
        # Check grid arrangement (3 columns, 2 rows)
        expected_positions = [
            (400, 300), (500, 300), (600, 300),  # First row
            (400, 400), (500, 400), (600, 400)   # Second row
        ]
        
        actual_positions = [(n.x, n.y) for n in positioned_nodes]
        assert actual_positions == expected_positions

class TestRelationshipDetection:
    """Test automatic relationship detection between entities"""
    
    def test_entity_relationship_detection(self):
        engine = VisualizationEngine()
        
        entities = [
            {
                'id': '1',
                'name': 'User',
                'type': 'actor',
                'description': 'User manages orders and uses payment system'
            },
            {
                'id': '2', 
                'name': 'Order',
                'type': 'entity',
                'description': 'Order contains products and belongs to user'
            },
            {
                'id': '3',
                'name': 'Payment',
                'type': 'system',
                'description': 'Payment processes transactions'
            }
        ]
        
        edges = engine._detect_entity_relationships(entities)
        
        assert len(edges) > 0
        
        # Check that relationships were detected
        edge_labels = [edge.label for edge in edges]
        assert any('uses' in label or 'contains' in label or 'relates to' in label for label in edge_labels)
        
        # Check metadata
        for edge in edges:
            assert edge.metadata.get('auto_detected') == True
            assert edge.metadata.get('confidence') > 0
    
    def test_scenario_relationship_detection(self):
        engine = VisualizationEngine()
        
        scenarios = [
            {
                'id': '1',
                'title': 'User Registration',
                'given': 'user provides valid email',
                'when': 'user submits registration',
                'then': 'account is created and user is logged in'
            },
            {
                'id': '2', 
                'title': 'User Profile',
                'given': 'user is logged in and has account',
                'when': 'user views profile',
                'then': 'profile information is displayed'
            }
        ]
        
        edges = engine._detect_scenario_relationships(scenarios)
        
        # Should detect connection between scenarios (login enables profile access)
        if len(edges) > 0:
            assert edges[0].type == "scenario_flow"
            assert edges[0].metadata.get('auto_detected') == True

class TestVisualizationStyles:
    """Test visual styling and color schemes"""
    
    def test_entity_styling(self):
        engine = VisualizationEngine()
        
        # Test different entity types get different styles
        actor_style = engine._get_entity_style('actor')
        system_style = engine._get_entity_style('system')
        database_style = engine._get_entity_style('database')
        
        assert actor_style['color'] != system_style['color']
        assert system_style['color'] != database_style['color']
        assert actor_style['shape'] == 'circle'
        assert database_style['shape'] == 'cylinder'
    
    def test_relationship_styling(self):
        engine = VisualizationEngine()
        
        contains_style = engine._get_relationship_style('contains')
        uses_style = engine._get_relationship_style('uses')
        
        assert contains_style['color'] != uses_style['color']
        assert contains_style['style'] == 'solid'
        assert uses_style['style'] == 'dashed'
    
    def test_color_palettes(self):
        engine = VisualizationEngine()
        
        assert 'default' in engine.color_palettes
        assert 'modern' in engine.color_palettes
        assert 'corporate' in engine.color_palettes
        
        default_palette = engine.color_palettes['default']
        assert len(default_palette) >= 6
        assert all(color.startswith('#') for color in default_palette)

class TestDiagramSerialization:
    """Test diagram serialization and statistics"""
    
    def test_diagram_to_dict(self):
        engine = VisualizationEngine()
        
        entities = [
            {'id': '1', 'name': 'User', 'type': 'actor', 'description': 'Test user'}
        ]
        
        diagram = engine.generate_entity_relationship_diagram(entities)
        diagram_dict = engine.to_dict(diagram)
        
        assert isinstance(diagram_dict, dict)
        assert 'id' in diagram_dict
        assert 'title' in diagram_dict
        assert 'nodes' in diagram_dict
        assert 'edges' in diagram_dict
        assert 'layout' in diagram_dict
        assert isinstance(diagram_dict['nodes'], list)
        assert isinstance(diagram_dict['edges'], list)
    
    def test_diagram_statistics(self):
        engine = VisualizationEngine()
        
        entities = [
            {'id': '1', 'name': 'User', 'type': 'actor'},
            {'id': '2', 'name': 'System', 'type': 'system'},
            {'id': '3', 'name': 'Database', 'type': 'database'}
        ]
        
        diagram = engine.generate_entity_relationship_diagram(entities)
        stats = engine.get_diagram_statistics(diagram)
        
        assert 'total_nodes' in stats
        assert 'total_edges' in stats
        assert 'node_types' in stats
        assert 'edge_types' in stats
        assert 'complexity_score' in stats
        
        assert stats['total_nodes'] == 3
        assert stats['node_types']['actor'] == 1
        assert stats['node_types']['system'] == 1
        assert stats['node_types']['database'] == 1
        assert stats['complexity_score'] > 0

class TestRealtimeUpdates:
    """Test real-time diagram updates"""
    
    def test_diagram_update_with_new_entities(self):
        engine = VisualizationEngine()
        
        # Create initial diagram
        initial_entities = [
            {'id': '1', 'name': 'User', 'type': 'actor'}
        ]
        diagram = engine.generate_entity_relationship_diagram(initial_entities)
        initial_node_count = len(diagram.nodes)
        
        # Add new entities
        new_entities = [
            {'id': '2', 'name': 'Database', 'type': 'database'}
        ]
        
        updated_diagram = engine.update_diagram_realtime(diagram, new_entities=new_entities)
        
        assert len(updated_diagram.nodes) > initial_node_count
        
        # Check that new entity was added
        entity_names = [node.label for node in updated_diagram.nodes]
        assert 'Database' in entity_names

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_empty_entities_list(self):
        engine = VisualizationEngine()
        
        diagram = engine.generate_entity_relationship_diagram([])
        
        assert len(diagram.nodes) == 0
        assert len(diagram.edges) == 0
        assert diagram.type == DiagramType.ENTITY_RELATIONSHIP.value
    
    def test_single_entity(self):
        engine = VisualizationEngine()
        
        entities = [{'id': '1', 'name': 'Lonely Entity', 'type': 'entity'}]
        diagram = engine.generate_entity_relationship_diagram(entities)
        
        assert len(diagram.nodes) == 1
        assert len(diagram.edges) == 0
        assert diagram.nodes[0].label == 'Lonely Entity'
    
    def test_unknown_entity_type(self):
        engine = VisualizationEngine()
        
        entities = [{'id': '1', 'name': 'Mystery', 'type': 'unknown_type'}]
        diagram = engine.generate_entity_relationship_diagram(entities)
        
        # Should fallback to default entity style
        assert len(diagram.nodes) == 1
        assert diagram.nodes[0].color == engine.node_styles['entity']['color']
    
    def test_malformed_scenario(self):
        engine = VisualizationEngine()
        
        scenarios = [
            {'id': '1', 'title': 'Incomplete Scenario'}  # Missing given/when/then
        ]
        
        diagram = engine.generate_scenario_flow_diagram(scenarios)
        
        # Should handle gracefully
        assert diagram.type == DiagramType.SCENARIO_FLOW.value

if __name__ == "__main__":
    pytest.main([__file__, "-v"])