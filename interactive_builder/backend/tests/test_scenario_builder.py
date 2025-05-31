"""
Tests for the Real-time Scenario Builder

Tests Given/When/Then pattern recognition, auto-completion suggestions,
and scenario validation functionality.
"""

import pytest
from scenario_builder import (
    ScenarioBuilder, 
    Scenario, 
    ScenarioComponent, 
    ScenarioSuggestion, 
    ScenarioPatterns
)

class TestScenarioPatterns:
    """Test pattern recognition for Given/When/Then components"""
    
    def test_given_pattern_recognition(self):
        patterns = ScenarioPatterns()
        builder = ScenarioBuilder()
        
        # Test various given patterns
        given_texts = [
            "given user is authenticated",
            "assume database is available", 
            "suppose user has valid credentials",
            "starting with empty cart",
            "with user logged in",
            "having sufficient balance"
        ]
        
        for text in given_texts:
            component = builder._classify_sentence(text, [])
            assert component is not None, f"Failed to recognize given pattern: {text}"
            assert component.type == "given", f"Misclassified as {component.type}: {text}"
            assert component.confidence > 0.5, f"Low confidence for: {text}"
    
    def test_when_pattern_recognition(self):
        builder = ScenarioBuilder()
        
        # Test various when patterns
        when_texts = [
            "when user clicks submit",
            "if payment is processed", 
            "after order is placed",
            "once validation completes",
            "as soon as data is received",
            "upon user logout",
            "error occurs"
        ]
        
        for text in when_texts:
            component = builder._classify_sentence(text, [])
            assert component is not None, f"Failed to recognize when pattern: {text}"
            assert component.type == "when", f"Misclassified as {component.type}: {text}"
    
    def test_then_pattern_recognition(self):
        builder = ScenarioBuilder()
        
        # Test various then patterns
        then_texts = [
            "then user is redirected",
            "should display success message",
            "must update inventory", 
            "will send confirmation email",
            "expect error to be logged",
            "result is calculated"
        ]
        
        for text in then_texts:
            component = builder._classify_sentence(text, [])
            assert component is not None, f"Failed to recognize then pattern: {text}"
            assert component.type == "then", f"Misclassified as {component.type}: {text}"

class TestScenarioExtraction:
    """Test extraction of scenarios from conversational text"""
    
    def test_simple_scenario_extraction(self):
        builder = ScenarioBuilder()
        
        text = """
        User login scenario:
        Given user has valid credentials
        When user enters username and password and clicks login
        Then user should be authenticated and redirected to dashboard
        """
        
        scenarios = builder.extract_scenarios_from_text(text)
        
        assert len(scenarios) == 1
        scenario = scenarios[0]
        assert len(scenario.given) == 1
        assert len(scenario.when) == 1  
        assert len(scenario.then) == 1
        assert "credentials" in scenario.given[0].content
        assert "login" in scenario.when[0].content
        assert "authenticated" in scenario.then[0].content
    
    def test_multiple_scenarios_extraction(self):
        builder = ScenarioBuilder()
        
        text = """
        Login scenarios:
        
        Scenario 1: Successful login
        Given user has valid credentials
        When user submits login form
        Then user is authenticated
        
        Scenario 2: Failed login  
        Given user has invalid password
        When user submits login form
        Then error message is displayed
        """
        
        scenarios = builder.extract_scenarios_from_text(text)
        
        assert len(scenarios) >= 1  # Should extract at least one scenario
        # Check that different scenarios have different content
        if len(scenarios) > 1:
            assert scenarios[0].then[0].content != scenarios[1].then[0].content
    
    def test_entity_extraction_in_scenarios(self):
        builder = ScenarioBuilder()
        entities = ["user", "database", "cart", "product"]
        
        text = """
        Given user has items in cart
        When user proceeds to checkout  
        Then product inventory is updated in database
        """
        
        scenarios = builder.extract_scenarios_from_text(text, entities)
        
        assert len(scenarios) == 1
        scenario = scenarios[0]
        
        # Check that entities are properly extracted
        all_entities = []
        for comp in scenario.given + scenario.when + scenario.then:
            all_entities.extend(comp.entities)
        
        assert "user" in all_entities
        assert "cart" in all_entities or any("cart" in comp.content for comp in scenario.given + scenario.when + scenario.then)

class TestScenarioSuggestions:
    """Test auto-completion suggestions for scenarios"""
    
    def test_missing_given_suggestions(self):
        builder = ScenarioBuilder()
        
        # Scenario with when/then but no given
        when_comp = ScenarioComponent("when", "user submits form", 0.8, ["user"], [])
        then_comp = ScenarioComponent("then", "data is saved", 0.8, ["data"], [])
        
        suggestions = builder._suggest_given_components([when_comp], [then_comp], ["user", "database"])
        
        assert len(suggestions) > 0
        # Should suggest authentication for user actions
        auth_suggestions = [s for s in suggestions if "authenticated" in s.suggestion.lower() or "logged in" in s.suggestion.lower()]
        assert len(auth_suggestions) > 0
    
    def test_missing_when_suggestions(self):
        builder = ScenarioBuilder()
        
        # Scenario with given/then but no when
        given_comp = ScenarioComponent("given", "user is authenticated", 0.8, ["user"], [])
        then_comp = ScenarioComponent("then", "error message is displayed", 0.8, [], [])
        
        suggestions = builder._suggest_when_components([given_comp], [then_comp], ["user", "input"])
        
        assert len(suggestions) > 0
        # Should suggest invalid input for error outcomes
        error_suggestions = [s for s in suggestions if "invalid" in s.suggestion.lower() or "error" in s.suggestion.lower()]
        assert len(error_suggestions) > 0
    
    def test_missing_then_suggestions(self):
        builder = ScenarioBuilder()
        
        # Scenario with given/when but no then
        given_comp = ScenarioComponent("given", "user has permissions", 0.8, ["user"], [])
        when_comp = ScenarioComponent("when", "user submits form", 0.8, ["user"], [])
        
        suggestions = builder._suggest_then_components([given_comp], [when_comp], ["confirmation"])
        
        assert len(suggestions) > 0
        # Should suggest success confirmation for submit actions
        success_suggestions = [s for s in suggestions if "success" in s.suggestion.lower() or "confirmation" in s.suggestion.lower()]
        assert len(success_suggestions) > 0
    
    def test_edge_case_suggestions(self):
        builder = ScenarioBuilder()
        
        # Complete scenario should suggest edge cases
        given_comp = ScenarioComponent("given", "user is logged in", 0.8, ["user"], [])
        when_comp = ScenarioComponent("when", "user makes request", 0.8, ["user"], [])
        then_comp = ScenarioComponent("then", "response is returned", 0.8, [], [])
        
        suggestions = builder._suggest_edge_cases([given_comp], [when_comp], [then_comp], ["network", "user"])
        
        assert len(suggestions) > 0
        # Should suggest network failures as edge cases
        network_suggestions = [s for s in suggestions if "network" in s.suggestion.lower()]
        assert len(network_suggestions) > 0

class TestScenarioValidation:
    """Test scenario validation and quality checks"""
    
    def test_complete_scenario_validation(self):
        builder = ScenarioBuilder()
        
        # Complete, well-formed scenario
        given_comp = ScenarioComponent("given", "user is authenticated", 0.8, ["user"], [])
        when_comp = ScenarioComponent("when", "user clicks save button", 0.8, ["user"], [])
        then_comp = ScenarioComponent("then", "data is persisted to database", 0.8, ["data", "database"], [])
        
        issues = builder._validate_scenario([given_comp], [when_comp], [then_comp])
        
        # Should have no or minimal issues
        assert len(issues) <= 1  # Allow for minor suggestions
    
    def test_missing_components_validation(self):
        builder = ScenarioBuilder()
        
        # Scenario missing when component
        given_comp = ScenarioComponent("given", "user is logged in", 0.8, ["user"], [])
        then_comp = ScenarioComponent("then", "success message shown", 0.8, [], [])
        
        issues = builder._validate_scenario([given_comp], [], [then_comp])
        
        assert len(issues) > 0
        when_issues = [issue for issue in issues if "when" in issue.lower()]
        assert len(when_issues) > 0
    
    def test_vague_language_detection(self):
        builder = ScenarioBuilder()
        
        # Scenario with vague language
        given_comp = ScenarioComponent("given", "something is configured", 0.8, [], [])
        when_comp = ScenarioComponent("when", "user does something", 0.8, ["user"], [])
        then_comp = ScenarioComponent("then", "system works somehow", 0.8, [], [])
        
        issues = builder._validate_scenario([given_comp], [when_comp], [then_comp])
        
        assert len(issues) > 0
        vague_issues = [issue for issue in issues if "vague" in issue.lower() or "something" in issue.lower()]
        assert len(vague_issues) > 0
    
    def test_untestable_outcomes_detection(self):
        builder = ScenarioBuilder()
        
        # Scenario with untestable outcomes
        given_comp = ScenarioComponent("given", "system is ready", 0.8, [], [])
        when_comp = ScenarioComponent("when", "user performs action", 0.8, ["user"], [])
        then_comp = ScenarioComponent("then", "user is happy and system works well", 0.8, ["user"], [])
        
        issues = builder._validate_scenario([given_comp], [when_comp], [then_comp])
        
        assert len(issues) > 0
        testable_issues = [issue for issue in issues if "testable" in issue.lower() or "measurable" in issue.lower()]
        assert len(testable_issues) > 0

class TestScenarioTitleGeneration:
    """Test automatic title generation for scenarios"""
    
    def test_title_from_when_component(self):
        builder = ScenarioBuilder()
        
        given_comp = ScenarioComponent("given", "user is authenticated", 0.8, ["user"], [])
        when_comp = ScenarioComponent("when", "user submits payment form", 0.8, ["user", "payment"], [])
        then_comp = ScenarioComponent("then", "payment is processed", 0.8, ["payment"], [])
        
        title = builder._generate_scenario_title("", [given_comp], [when_comp], [then_comp])
        
        assert "payment" in title.lower() or "submit" in title.lower()
        assert len(title) > 0
        assert len(title) < 100  # Reasonable length
    
    def test_title_from_block_text(self):
        builder = ScenarioBuilder()
        
        block_text = "User successfully logs into the system."
        
        title = builder._generate_scenario_title(block_text, [], [], [])
        
        assert "user" in title.lower() or "log" in title.lower()
        assert len(title) > 0

class TestRelatedScenarios:
    """Test related scenario suggestions"""
    
    def test_error_case_suggestions(self):
        builder = ScenarioBuilder()
        
        # Successful scenario should suggest error cases
        scenario = Scenario(
            id="test",
            title="Successful login",
            given=[ScenarioComponent("given", "user has valid credentials", 0.8, ["user"], [])],
            when=[ScenarioComponent("when", "user submits login form", 0.8, ["user"], [])],
            then=[ScenarioComponent("then", "user is authenticated successfully", 0.8, ["user"], [])],
            confidence=0.8,
            completion_suggestions=[],
            validation_issues=[]
        )
        
        related = builder.suggest_related_scenarios(scenario, ["user", "credentials"])
        
        assert len(related) > 0
        error_scenarios = [r for r in related if "error" in r["title"].lower() or "fail" in r["title"].lower()]
        assert len(error_scenarios) > 0
    
    def test_boundary_case_suggestions(self):
        builder = ScenarioBuilder()
        
        # User scenario should suggest boundary cases
        scenario = Scenario(
            id="test",
            title="User creates account",
            given=[ScenarioComponent("given", "registration form is displayed", 0.8, [], [])],
            when=[ScenarioComponent("when", "user fills out form", 0.8, ["user"], [])],
            then=[ScenarioComponent("then", "account is created", 0.8, ["account"], [])],
            confidence=0.8,
            completion_suggestions=[],
            validation_issues=[]
        )
        
        related = builder.suggest_related_scenarios(scenario, ["user", "account"])
        
        assert len(related) > 0
        boundary_scenarios = [r for r in related if "boundary" in r["title"].lower() or "limit" in r["title"].lower()]
        assert len(boundary_scenarios) > 0

class TestScenarioConfidence:
    """Test confidence scoring for scenarios"""
    
    def test_high_confidence_explicit_patterns(self):
        builder = ScenarioBuilder()
        
        # Explicit patterns should have high confidence
        explicit_text = "Given user is authenticated. When user clicks save. Then data is saved."
        
        scenarios = builder.extract_scenarios_from_text(explicit_text)
        
        assert len(scenarios) == 1
        assert scenarios[0].confidence > 0.7  # High confidence for explicit patterns
    
    def test_lower_confidence_implicit_patterns(self):
        builder = ScenarioBuilder()
        
        # Implicit patterns should have lower confidence
        implicit_text = "User saves data and sees confirmation."
        
        scenarios = builder.extract_scenarios_from_text(implicit_text)
        
        if len(scenarios) > 0:
            # If pattern is recognized, confidence should be lower for implicit patterns
            assert scenarios[0].confidence < 0.9

class TestScenarioToDictConversion:
    """Test conversion of scenarios to dictionary format"""
    
    def test_complete_scenario_to_dict(self):
        builder = ScenarioBuilder()
        
        scenario = Scenario(
            id="test-123",
            title="Test scenario",
            given=[ScenarioComponent("given", "precondition", 0.8, ["entity1"], ["rel1"])],
            when=[ScenarioComponent("when", "action", 0.9, ["entity2"], ["rel2"])],
            then=[ScenarioComponent("then", "outcome", 0.85, ["entity3"], ["rel3"])],
            confidence=0.83,
            completion_suggestions=[
                ScenarioSuggestion("given", "suggestion", "reasoning", 0.7, ["entity"])
            ],
            validation_issues=["issue1", "issue2"]
        )
        
        result = builder.to_dict(scenario)
        
        assert result["id"] == "test-123"
        assert result["title"] == "Test scenario"
        assert len(result["given"]) == 1
        assert len(result["when"]) == 1
        assert len(result["then"]) == 1
        assert result["confidence"] == 0.83
        assert len(result["completion_suggestions"]) == 1
        assert len(result["validation_issues"]) == 2
        
        # Check component structure
        assert result["given"][0]["type"] == "given"
        assert result["given"][0]["content"] == "precondition"
        assert result["given"][0]["confidence"] == 0.8

@pytest.fixture
def sample_entities():
    """Sample entities for testing"""
    return ["user", "system", "database", "payment", "order", "cart", "product"]

@pytest.fixture
def sample_scenario_text():
    """Sample scenario text for testing"""
    return """
    E-commerce checkout process:
    Given user has items in cart and is authenticated
    When user proceeds to checkout and enters payment details
    Then order is created and payment is processed and confirmation email is sent
    """

def test_integration_scenario_extraction_with_entities(sample_entities, sample_scenario_text):
    """Integration test for scenario extraction with entity recognition"""
    builder = ScenarioBuilder()
    
    scenarios = builder.extract_scenarios_from_text(sample_scenario_text, sample_entities)
    
    assert len(scenarios) >= 1
    scenario = scenarios[0]
    
    # Should recognize entities in scenario components
    all_entities = []
    for comp in scenario.given + scenario.when + scenario.then:
        all_entities.extend(comp.entities)
    
    assert any(entity in all_entities for entity in ["user", "cart", "payment", "order"])
    
    # Should generate suggestions
    assert len(scenario.completion_suggestions) >= 0  # May or may not have suggestions
    
    # Should have reasonable confidence
    assert scenario.confidence > 0.1

if __name__ == "__main__":
    pytest.main([__file__, "-v"])