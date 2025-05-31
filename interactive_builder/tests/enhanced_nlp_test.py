"""
Tests for Enhanced NLP Entity Extraction
"""

import asyncio
import sys
import os
import pytest

# Add backend to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from enhanced_nlp_extractor import EnhancedNLPExtractor

class TestEnhancedEntityExtraction:
    
    def setup_method(self):
        """Set up test fixtures"""
        self.extractor = EnhancedNLPExtractor()
    
    def test_basic_entity_extraction(self):
        """Test basic entity extraction functionality"""
        text = "The user creates an order in the database"
        entities = self.extractor.extract_entities_enhanced(text)
        
        # Should extract user, order, and database
        entity_names = [e.name.lower() for e in entities]
        assert any('user' in name for name in entity_names), f"User not found in {entity_names}"
        assert any('order' in name for name in entity_names), f"Order not found in {entity_names}"
        assert any('database' in name for name in entity_names), f"Database not found in {entity_names}"
    
    def test_domain_detection(self):
        """Test domain detection capability"""
        # Software development domain
        sw_text = "The developer commits code to the repository and triggers CI/CD pipeline"
        domain = self.extractor.detect_domain(sw_text)
        assert domain == 'software_development', f"Expected software_development, got {domain}"
        
        # Web application domain
        web_text = "The frontend sends requests to the backend API through middleware"
        domain = self.extractor.detect_domain(web_text)
        assert domain == 'web_application', f"Expected web_application, got {domain}"
        
        # AI/ML domain
        ai_text = "The model processes the dataset and generates predictions using inference"
        domain = self.extractor.detect_domain(ai_text)
        assert domain == 'ai_ml', f"Expected ai_ml, got {domain}"
    
    def test_entity_types_and_confidence(self):
        """Test entity type classification and confidence scoring"""
        text = "The admin user manages customer accounts through the API service"
        entities = self.extractor.extract_entities_enhanced(text, domain_hint='web_application')
        
        # Check that entities have appropriate types
        entity_dict = {e.name.lower(): e for e in entities}
        
        # Admin should be an actor
        admin_entities = [e for e in entities if 'admin' in e.name.lower() or 'user' in e.name.lower()]
        assert any(e.type == 'actor' for e in admin_entities), "Admin/User should be classified as actor"
        
        # API should be a system component
        api_entities = [e for e in entities if 'api' in e.name.lower()]
        assert any(e.type == 'system_component' for e in api_entities), "API should be classified as system_component"
        
        # All entities should have reasonable confidence scores
        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0, f"Invalid confidence {entity.confidence} for {entity.name}"
    
    def test_relationship_extraction(self):
        """Test relationship extraction between entities"""
        text = "The user authentication service validates credentials against the user database"
        entities = self.extractor.extract_entities_enhanced(text)
        
        # Should find relationships
        entities_with_relationships = [e for e in entities if e.relationships]
        assert len(entities_with_relationships) > 0, "Should extract some relationships"
        
        # Check relationship format
        for entity in entities_with_relationships:
            for rel in entity.relationships:
                assert ':' in rel, f"Relationship should have format 'type:target', got {rel}"
    
    def test_synonym_detection(self):
        """Test synonym and variation detection"""
        text = "The customer (also known as user or client) places an order"
        entities = self.extractor.extract_entities_enhanced(text)
        
        # Should extract customer/user/client with synonyms
        customer_entities = [e for e in entities if any(word in e.name.lower() 
                           for word in ['customer', 'user', 'client'])]
        
        # At least one should have synonyms
        entities_with_synonyms = [e for e in customer_entities if e.synonyms]
        assert len(entities_with_synonyms) > 0, "Should detect synonyms for customer/user/client"
    
    def test_context_enhancement(self):
        """Test context-based entity enhancement"""
        context = "We're building an e-commerce platform"
        text = "Users can add items to their cart and checkout"
        
        entities = self.extractor.extract_entities_enhanced(text, context=context)
        
        # Should extract e-commerce related entities
        entity_names = [e.name.lower() for e in entities]
        expected_entities = ['users', 'items', 'cart']
        
        for expected in expected_entities:
            assert any(expected in name for name in entity_names), f"{expected} not found in {entity_names}"
    
    def test_domain_specific_extraction(self):
        """Test domain-specific vocabulary extraction"""
        # Test AI/ML domain
        ai_text = "The machine learning model trains on the dataset and produces predictions"
        entities = self.extractor.extract_entities_enhanced(ai_text, domain_hint='ai_ml')
        
        ai_terms = ['model', 'dataset', 'prediction', 'train']
        entity_names = [e.name.lower() for e in entities]
        
        found_ai_terms = [term for term in ai_terms if any(term in name for name in entity_names)]
        assert len(found_ai_terms) >= 2, f"Should find AI/ML terms, found: {found_ai_terms}"
    
    def test_entity_canonicalization(self):
        """Test entity name canonicalization and deduplication"""
        text = "The User creates a user account. Users can manage their user profile."
        entities = self.extractor.extract_entities_enhanced(text)
        
        # Should deduplicate variations of "user"
        user_entities = [e for e in entities if 'user' in e.canonical_name.lower()]
        
        # Should have canonical forms
        for entity in user_entities:
            assert entity.canonical_name, f"Entity {entity.name} should have canonical name"
            assert '_' not in entity.canonical_name or entity.canonical_name.replace('_', '').isalnum(), \
                   f"Canonical name should be normalized: {entity.canonical_name}"
    
    def test_enhanced_vs_basic_extraction(self):
        """Test that enhanced extraction provides more information than basic"""
        text = "The admin user configures the API gateway to route requests to microservices"
        
        # Enhanced extraction
        enhanced_entities = self.extractor.extract_entities_enhanced(text, domain_hint='web_application')
        
        # Should have rich context information
        entities_with_context = [e for e in enhanced_entities if e.context.syntactic_role != 'unknown']
        assert len(entities_with_context) > 0, "Should have entities with syntactic context"
        
        # Should have semantic classes
        entities_with_semantics = [e for e in enhanced_entities if e.context.semantic_class != 'unknown']
        assert len(entities_with_semantics) > 0, "Should have entities with semantic classification"
    
    def test_confidence_scoring_factors(self):
        """Test that confidence scoring considers multiple factors"""
        # High confidence text with clear domain indicators
        high_conf_text = "The user authentication service in our web application"
        high_entities = self.extractor.extract_entities_enhanced(high_conf_text, domain_hint='web_application')
        
        # Low confidence text with ambiguous terms
        low_conf_text = "It does things with stuff"
        low_entities = self.extractor.extract_entities_enhanced(low_conf_text)
        
        if high_entities and low_entities:
            avg_high_conf = sum(e.confidence for e in high_entities) / len(high_entities)
            avg_low_conf = sum(e.confidence for e in low_entities) / len(low_entities)
            
            assert avg_high_conf > avg_low_conf, \
                   f"Clear domain text should have higher confidence: {avg_high_conf} vs {avg_low_conf}"

def run_interactive_test():
    """Run an interactive test to see extraction in action"""
    print("🧪 Enhanced NLP Entity Extraction Interactive Test\n")
    
    extractor = EnhancedNLPExtractor()
    
    test_cases = [
        {
            'text': "I want to build a web application where users can create accounts, login, and manage their profiles",
            'description': "E-commerce web application"
        },
        {
            'text': "The ML model will analyze customer behavior data and predict purchase likelihood using trained algorithms",
            'description': "AI/ML prediction system"
        },
        {
            'text': "Developers commit code to Git repositories which triggers automated CI/CD pipelines for deployment",
            'description': "Software development workflow"
        },
        {
            'text': "The API gateway routes incoming requests to appropriate microservices and handles authentication",
            'description': "Microservices architecture"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"📝 Test Case {i}: {test_case['description']}")
        print(f"   Input: {test_case['text']}")
        
        # Detect domain
        domain = extractor.detect_domain(test_case['text'])
        print(f"   🎯 Detected domain: {domain or 'generic'}")
        
        # Extract entities
        entities = extractor.extract_entities_enhanced(
            text=test_case['text'],
            domain_hint=domain
        )
        
        print(f"   🔍 Extracted {len(entities)} entities:")
        
        for entity in entities[:5]:  # Show top 5
            print(f"      • {entity.name} ({entity.type})")
            print(f"        Confidence: {entity.confidence:.2f}")
            if entity.relationships:
                print(f"        Relationships: {', '.join(entity.relationships[:2])}")
            if entity.synonyms:
                print(f"        Synonyms: {', '.join(list(entity.synonyms)[:2])}")
            if entity.context.syntactic_role != 'unknown':
                print(f"        Role: {entity.context.syntactic_role}")
        
        print()

if __name__ == "__main__":
    # Run pytest tests
    print("Running automated tests...")
    pytest.main([__file__, "-v"])
    
    print("\n" + "="*60)
    
    # Run interactive demonstration
    run_interactive_test()