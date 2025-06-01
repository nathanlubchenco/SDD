"""
Real-time Scenario Builder

Provides intelligent Given/When/Then scenario recognition and completion,
transforming conversational descriptions into structured behavior specifications.
"""

import re
import json
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum

@dataclass
class ScenarioComponent:
    """Individual component of a scenario (Given/When/Then)"""
    type: str  # 'given', 'when', 'then'
    content: str
    confidence: float
    entities: List[str]
    relationships: List[str]

@dataclass
class ScenarioSuggestion:
    """Auto-completion suggestion for scenarios"""
    component_type: str
    suggestion: str
    reasoning: str
    confidence: float
    context_entities: List[str]

@dataclass
class Scenario:
    """Complete scenario structure"""
    id: str
    title: str
    given: List[ScenarioComponent]
    when: List[ScenarioComponent] 
    then: List[ScenarioComponent]
    confidence: float
    completion_suggestions: List[ScenarioSuggestion]
    validation_issues: List[str]

class ScenarioPatterns:
    """Pattern recognition for Given/When/Then components"""
    
    GIVEN_PATTERNS = [
        r"given\s+(.+)",
        r"assume\s+(.+)",
        r"suppose\s+(.+)", 
        r"starting\s+with\s+(.+)",
        r"with\s+(.+)",
        r"having\s+(.+)",
        r"when\s+(.+)\s+exists",
        r"if\s+(.+)\s+is\s+true",
        r"considering\s+(.+)",
        r"in\s+a\s+state\s+where\s+(.+)"
    ]
    
    WHEN_PATTERNS = [
        r"when\s+(.+)",
        r"if\s+(.+)",
        r"after\s+(.+)",
        r"once\s+(.+)",
        r"as\s+soon\s+as\s+(.+)",
        r"upon\s+(.+)",
        r"during\s+(.+)",
        r"while\s+(.+)",
        r"(.+)\s+happens",
        r"(.+)\s+occurs",
        r"(.+)\s+is\s+triggered"
    ]
    
    THEN_PATTERNS = [
        r"then\s+(.+)",
        r"should\s+(.+)",
        r"must\s+(.+)",
        r"will\s+(.+)",
        r"expect\s+(.+)",
        r"result\s+is\s+(.+)",
        r"outcome\s+is\s+(.+)",
        r"(.+)\s+should\s+happen",
        r"(.+)\s+is\s+expected",
        r"(.+)\s+occurs"
    ]

class ScenarioBuilder:
    """Real-time scenario building engine"""
    
    def __init__(self):
        self.patterns = ScenarioPatterns()
        self.scenario_templates = self._load_scenario_templates()
        self.domain_patterns = self._load_domain_patterns()
        
    def extract_scenarios_from_text(self, text: str, entities: List[str] = None) -> List[Scenario]:
        """Extract structured scenarios from conversational text"""
        entities = entities or []
        
        # Clean and normalize text
        text = self._normalize_text(text)
        
        # Detect scenario boundaries
        scenario_blocks = self._detect_scenario_blocks(text)
        
        scenarios = []
        for i, block in enumerate(scenario_blocks):
            scenario = self._parse_scenario_block(block, entities, f"scenario_{i}")
            if scenario:
                scenarios.append(scenario)
        
        return scenarios
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for better pattern matching"""
        # Convert to lowercase for pattern matching
        text = text.lower()
        
        # Replace common variations
        replacements = {
            "and then": "then",
            "after that": "then", 
            "as a result": "then",
            "provided that": "given",
            "assuming": "given",
            "in case": "when"
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
            
        return text
    
    def _detect_scenario_blocks(self, text: str) -> List[str]:
        """Detect individual scenario blocks in text"""
        # For now, treat the entire text as one scenario block
        # This preserves Given/When/Then relationships within the same scenario
        return [text.strip()]
    
    def _parse_scenario_block(self, block: str, entities: List[str], scenario_id: str) -> Optional[Scenario]:
        """Parse a text block into a structured scenario"""
        given_components = []
        when_components = []
        then_components = []
        
        sentences = self._split_into_sentences(block)
        
        for sentence in sentences:
            # Try to classify each sentence
            component = self._classify_sentence(sentence, entities)
            if component:
                if component.type == "given":
                    given_components.append(component)
                elif component.type == "when":
                    when_components.append(component)
                elif component.type == "then":
                    then_components.append(component)
        
        # Only create scenario if we have at least one component
        if not (given_components or when_components or then_components):
            return None
        
        # Generate title from first sentence or content
        title = self._generate_scenario_title(block, given_components, when_components, then_components)
        
        # Calculate overall confidence
        all_components = given_components + when_components + then_components
        confidence = sum(c.confidence for c in all_components) / len(all_components) if all_components else 0.0
        
        # Generate completion suggestions
        suggestions = self._generate_completion_suggestions(
            given_components, when_components, then_components, entities
        )
        
        # Validate scenario
        validation_issues = self._validate_scenario(given_components, when_components, then_components)
        
        return Scenario(
            id=scenario_id,
            title=title,
            given=given_components,
            when=when_components,
            then=then_components,
            confidence=confidence,
            completion_suggestions=suggestions,
            validation_issues=validation_issues
        )
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for analysis"""
        # Split on periods, exclamation marks, question marks, or newlines
        sentences = re.split(r'[.!?\n]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _classify_sentence(self, sentence: str, entities: List[str]) -> Optional[ScenarioComponent]:
        """Classify a sentence as Given/When/Then"""
        sentence = sentence.lower().strip()
        
        # Try each pattern type
        for pattern_type, patterns in [
            ("given", self.patterns.GIVEN_PATTERNS),
            ("when", self.patterns.WHEN_PATTERNS), 
            ("then", self.patterns.THEN_PATTERNS)
        ]:
            for pattern in patterns:
                match = re.search(pattern, sentence)
                if match:
                    content = match.group(1).strip()
                    confidence = self._calculate_pattern_confidence(sentence, pattern, pattern_type)
                    
                    # Extract entities from the content
                    content_entities = [e for e in entities if e.lower() in content.lower()]
                    
                    # Extract relationships
                    relationships = self._extract_relationships(content, entities)
                    
                    return ScenarioComponent(
                        type=pattern_type,
                        content=content,
                        confidence=confidence,
                        entities=content_entities,
                        relationships=relationships
                    )
        
        return None
    
    def _calculate_pattern_confidence(self, sentence: str, pattern: str, component_type: str) -> float:
        """Calculate confidence score for pattern match"""
        base_confidence = 0.7
        
        # Boost confidence for explicit keywords
        explicit_keywords = {
            "given": ["given", "assume", "suppose"],
            "when": ["when", "if", "after"],
            "then": ["then", "should", "must", "will"]
        }
        
        if any(keyword in sentence for keyword in explicit_keywords.get(component_type, [])):
            base_confidence += 0.2
        
        # Reduce confidence for ambiguous patterns
        if pattern.startswith(r"(.+)"):  # Catch-all patterns
            base_confidence -= 0.3
        
        return min(1.0, max(0.1, base_confidence))
    
    def _extract_relationships(self, content: str, entities: List[str]) -> List[str]:
        """Extract relationships from scenario content"""
        relationships = []
        
        # Common relationship patterns
        relationship_patterns = [
            r"(\w+)\s+(?:has|contains|includes)\s+(\w+)",
            r"(\w+)\s+(?:sends|receives|processes)\s+(\w+)",
            r"(\w+)\s+(?:is|becomes|remains)\s+(\w+)",
            r"(\w+)\s+(?:triggers|causes|initiates)\s+(\w+)"
        ]
        
        for pattern in relationship_patterns:
            matches = re.finditer(pattern, content.lower())
            for match in matches:
                rel = f"{match.group(1)} -> {match.group(2)}"
                if rel not in relationships:
                    relationships.append(rel)
        
        return relationships
    
    def _generate_scenario_title(self, block: str, given: List, when: List, then: List) -> str:
        """Generate a descriptive title for the scenario"""
        # Try to extract title from first sentence
        first_sentence = block.split('.')[0].strip()
        if len(first_sentence) < 80:
            return first_sentence.capitalize()
        
        # Generate from components
        if when:
            action = when[0].content[:50] + "..." if len(when[0].content) > 50 else when[0].content
            return f"When {action}"
        elif then:
            outcome = then[0].content[:50] + "..." if len(then[0].content) > 50 else then[0].content
            return f"Should {outcome}"
        elif given:
            context = given[0].content[:50] + "..." if len(given[0].content) > 50 else given[0].content
            return f"Given {context}"
        
        return "Untitled Scenario"
    
    def _generate_completion_suggestions(self, given: List, when: List, then: List, entities: List[str]) -> List[ScenarioSuggestion]:
        """Generate auto-completion suggestions for incomplete scenarios"""
        suggestions = []
        
        # Suggest missing components
        if not given:
            suggestions.extend(self._suggest_given_components(when, then, entities))
        
        if not when:
            suggestions.extend(self._suggest_when_components(given, then, entities))
            
        if not then:
            suggestions.extend(self._suggest_then_components(given, when, entities))
        
        # Suggest additional components for completeness
        if given and when and then:
            suggestions.extend(self._suggest_edge_cases(given, when, then, entities))
        
        return suggestions
    
    def _suggest_given_components(self, when: List, then: List, entities: List[str]) -> List[ScenarioSuggestion]:
        """Suggest Given components based on When/Then"""
        suggestions = []
        
        if when:
            action = when[0].content
            # Suggest preconditions for the action
            if "user" in action.lower():
                suggestions.append(ScenarioSuggestion(
                    component_type="given",
                    suggestion="user is authenticated and logged in",
                    reasoning="Most user actions require authentication",
                    confidence=0.8,
                    context_entities=["user", "auth"]
                ))
            
            if any(entity in action.lower() for entity in ["database", "db", "data"]):
                suggestions.append(ScenarioSuggestion(
                    component_type="given", 
                    suggestion="database is accessible and contains test data",
                    reasoning="Database operations need accessible data",
                    confidence=0.7,
                    context_entities=["database", "data"]
                ))
        
        return suggestions
    
    def _suggest_when_components(self, given: List, then: List, entities: List[str]) -> List[ScenarioSuggestion]:
        """Suggest When components based on Given/Then"""
        suggestions = []
        
        if then:
            outcome = then[0].content
            # Suggest triggers for the outcome
            if "error" in outcome.lower():
                suggestions.append(ScenarioSuggestion(
                    component_type="when",
                    suggestion="invalid input is provided",
                    reasoning="Errors typically result from invalid inputs",
                    confidence=0.8,
                    context_entities=["input", "validation"]
                ))
            
            if "notification" in outcome.lower() or "email" in outcome.lower():
                suggestions.append(ScenarioSuggestion(
                    component_type="when",
                    suggestion="important event occurs",
                    reasoning="Notifications are triggered by significant events",
                    confidence=0.7,
                    context_entities=["event", "trigger"]
                ))
        
        return suggestions
    
    def _suggest_then_components(self, given: List, when: List, entities: List[str]) -> List[ScenarioSuggestion]:
        """Suggest Then components based on Given/When"""
        suggestions = []
        
        if when:
            action = when[0].content
            # Suggest outcomes for the action
            if "submit" in action.lower() or "create" in action.lower():
                suggestions.append(ScenarioSuggestion(
                    component_type="then",
                    suggestion="success confirmation is displayed",
                    reasoning="Create/submit actions should provide feedback",
                    confidence=0.8,
                    context_entities=["feedback", "confirmation"]
                ))
            
            if "delete" in action.lower():
                suggestions.append(ScenarioSuggestion(
                    component_type="then",
                    suggestion="item is removed and confirmation shown",
                    reasoning="Delete operations need confirmation",
                    confidence=0.9,
                    context_entities=["removal", "confirmation"]
                ))
        
        return suggestions
    
    def _suggest_edge_cases(self, given: List, when: List, then: List, entities: List[str]) -> List[ScenarioSuggestion]:
        """Suggest edge cases and alternative scenarios"""
        suggestions = []
        
        # Suggest error cases
        suggestions.append(ScenarioSuggestion(
            component_type="when",
            suggestion="network connection fails during the operation",
            reasoning="Network failures are common edge cases",
            confidence=0.6,
            context_entities=["network", "error"]
        ))
        
        # Suggest boundary conditions
        if any("user" in comp.content.lower() for comp in given + when + then):
            suggestions.append(ScenarioSuggestion(
                component_type="given", 
                suggestion="user account has reached usage limits",
                reasoning="Boundary conditions test system limits",
                confidence=0.5,
                context_entities=["limits", "boundary"]
            ))
        
        return suggestions
    
    def _validate_scenario(self, given: List, when: List, then: List) -> List[str]:
        """Validate scenario completeness and quality"""
        issues = []
        
        # Check for missing components
        if not when:
            issues.append("Missing 'When' component - what triggers this scenario?")
        
        if not then:
            issues.append("Missing 'Then' component - what should happen?")
        
        # Check for vague language
        vague_words = ["something", "anything", "somehow", "maybe", "possibly"]
        all_content = " ".join([comp.content for comp in given + when + then])
        
        for word in vague_words:
            if word in all_content.lower():
                issues.append(f"Vague language detected: '{word}' - try to be more specific")
        
        # Check for testability
        untestable_phrases = ["user is happy", "system works well", "good performance"]
        for phrase in untestable_phrases:
            if phrase in all_content.lower():
                issues.append(f"Untestable outcome: '{phrase}' - specify measurable criteria")
        
        return issues
    
    def _load_scenario_templates(self) -> Dict[str, Any]:
        """Load pre-defined scenario templates for common patterns"""
        return {
            "user_authentication": {
                "given": "user has valid credentials",
                "when": "user attempts to log in",
                "then": "user is authenticated and redirected to dashboard"
            },
            "data_validation": {
                "given": "form with required fields",
                "when": "user submits incomplete form", 
                "then": "validation errors are displayed"
            },
            "api_request": {
                "given": "API endpoint is available",
                "when": "client makes valid request",
                "then": "response is returned with correct data"
            }
        }
    
    def _load_domain_patterns(self) -> Dict[str, List[str]]:
        """Load domain-specific patterns for better recognition"""
        return {
            "ecommerce": ["cart", "checkout", "payment", "order", "product"],
            "authentication": ["login", "password", "token", "session", "user"],
            "api": ["request", "response", "endpoint", "header", "status"],
            "database": ["query", "insert", "update", "delete", "record"]
        }
    
    def suggest_related_scenarios(self, scenario: Scenario, entities: List[str]) -> List[Dict[str, Any]]:
        """Suggest related scenarios based on current scenario"""
        suggestions = []
        
        # Extract key concepts from current scenario
        all_content = " ".join([
            comp.content for comp in scenario.given + scenario.when + scenario.then
        ])
        
        # Suggest error cases
        if "success" in all_content.lower():
            suggestions.append({
                "title": f"Error case for: {scenario.title}",
                "description": "What happens when the operation fails?",
                "suggested_when": "an error occurs during the process",
                "suggested_then": "appropriate error message is shown"
            })
        
        # Suggest boundary cases
        if any(entity in all_content.lower() for entity in ["user", "customer", "account"]):
            suggestions.append({
                "title": f"Boundary case for: {scenario.title}",
                "description": "What about edge cases or limits?", 
                "suggested_given": "user has reached account limits",
                "suggested_then": "appropriate limits message is displayed"
            })
        
        return suggestions

    def to_dict(self, scenario: Scenario) -> Dict[str, Any]:
        """Convert scenario to dictionary for API responses"""
        return asdict(scenario)