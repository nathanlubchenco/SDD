"""
Advanced NLP extraction for entities, scenarios, and constraints from natural language
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class ExtractedEntity:
    name: str
    type: str
    description: str
    confidence: float
    context: str

@dataclass
class ExtractedScenario:
    title: str
    given: str
    when: str
    then: str
    confidence: float
    entities: List[str]

@dataclass
class ExtractedConstraint:
    category: str
    name: str
    requirement: str
    priority: str
    confidence: float

class NLPExtractor:
    """Advanced natural language processing for specification extraction"""
    
    def __init__(self):
        # Entity patterns with confidence scoring
        self.entity_patterns = {
            'actor': {
                'patterns': [
                    r'\b(user|customer|admin|administrator|manager|operator|guest|visitor|member)\b',
                    r'\b(client|customer|end[\s-]?user|system[\s-]?admin)\b',
                    r'\b(developer|analyst|stakeholder|owner|reviewer|maintainer)\b'
                ],
                'confidence': 0.9
            },
            'data_entity': {
                'patterns': [
                    r'\b(task|order|product|item|invoice|report|document|file|message|notification)\b',
                    r'\b(record|entry|transaction|request|response|log|event|session)\b',
                    r'\b(account|profile|setting|preference|configuration|data)\b',
                    r'\b(comment|review|rating|feedback|note|attachment)\b',
                    r'\b(history|output|input|result|analysis|pattern|suggestion|instruction)\b',
                    r'\b(command|functionality|usage|context|session[\s-]?history)\b'
                ],
                'confidence': 0.8
            },
            'system_component': {
                'patterns': [
                    r'\b(database|db|server|api|service|application|app|system|platform)\b',
                    r'\b(interface|ui|frontend|backend|endpoint|microservice)\b',
                    r'\b(queue|cache|storage|repository|gateway|proxy|load[\s-]?balancer)\b',
                    r'\b(authentication|auth|authorization|security|encryption)\b',
                    r'\b(cli|tool|analyzer|parser|processor|generator|extractor)\b',
                    r'\b(codex[\s-]?cli|claude[\s-]?code|ai[\s-]?tool)\b'
                ],
                'confidence': 0.7
            },
            'business_concept': {
                'patterns': [
                    r'\b(workflow|process|procedure|policy|rule|validation)\b',
                    r'\b(permission|role|access|privilege|scope|domain)\b',
                    r'\b(category|type|status|state|phase|stage)\b',
                    r'\b(improvement|optimization|enhancement|recommendation)\b',
                    r'\b(pattern[\s-]?recognition|analysis|monitoring|tracking)\b'
                ],
                'confidence': 0.6
            },
            'action_concept': {
                'patterns': [
                    r'\b(analyze|analyzes|analyzing|analysis)\b',
                    r'\b(recognize|recognizes|recognizing|recognition)\b',
                    r'\b(improve|improves|improving|improvement)\b',
                    r'\b(update|updates|updating|upgrade)\b',
                    r'\b(generate|generates|generating|creation)\b',
                    r'\b(process|processes|processing)\b',
                    r'\b(extract|extracts|extracting|extraction)\b',
                    r'\b(run|runs|running|execute|execution)\b'
                ],
                'confidence': 0.5
            }
        }
        
        # Scenario indicators
        self.scenario_patterns = {
            'given_indicators': [
                r'\bgiven\s+(.+?)(?=\bwhen\b|\bif\b|\.|$)',
                r'\bstarting\s+with\s+(.+?)(?=\bwhen\b|\bif\b|\.|$)',
                r'\bassuming\s+(.+?)(?=\bwhen\b|\bif\b|\.|$)',
                r'\bwith\s+(.+?)\s+in\s+place(?=\bwhen\b|\bif\b|\.|$)'
            ],
            'when_indicators': [
                r'\bwhen\s+(.+?)(?=\bthen\b|\bshould\b|\.|$)',
                r'\bif\s+(.+?)(?=\bthen\b|\bshould\b|\.|$)',
                r'\bupon\s+(.+?)(?=\bthen\b|\bshould\b|\.|$)',
                r'\bafter\s+(.+?)(?=\bthen\b|\bshould\b|\.|$)'
            ],
            'then_indicators': [
                r'\bthen\s+(.+?)(?=\.|$)',
                r'\bshould\s+(.+?)(?=\.|$)',
                r'\bmust\s+(.+?)(?=\.|$)',
                r'\bwill\s+(.+?)(?=\.|$)',
                r'\bexpected?\s+(.+?)(?=\.|$)'
            ]
        }
        
        # Constraint patterns
        self.constraint_patterns = {
            'performance': {
                'patterns': [
                    r'\b(fast|quick|slow|speed|latency|response\s+time|throughput|performance)\b',
                    r'\b(\d+(?:\.\d+)?)\s*(ms|milliseconds?|seconds?|minutes?)\b',
                    r'\b(concurrent|parallel|simultaneous|real[\s-]?time)\b',
                    r'\b(load|capacity|scalability|volume)\b'
                ],
                'priority': 'high'
            },
            'security': {
                'patterns': [
                    r'\b(secure|safe|protect|encrypt|decrypt|authentication|authorization)\b',
                    r'\b(password|token|certificate|ssl|tls|https)\b',
                    r'\b(privacy|confidential|sensitive|personal\s+data|pii)\b',
                    r'\b(access\s+control|permission|role|privilege)\b'
                ],
                'priority': 'high'
            },
            'reliability': {
                'patterns': [
                    r'\b(reliable|stable|robust|uptime|availability|downtime)\b',
                    r'\b(backup|recovery|failover|redundant|fault[\s-]?tolerant)\b',
                    r'\b(error\s+handling|exception|graceful|degrade)\b',
                    r'\b(\d+(?:\.\d+)?)\s*%\s*(uptime|availability)\b'
                ],
                'priority': 'medium'
            },
            'scalability': {
                'patterns': [
                    r'\b(scale|scaling|scalable|elastic|horizontal|vertical)\b',
                    r'\b(\d+(?:,\d{3})*|\d+k|\d+m)\s*(users?|requests?|transactions?)\b',
                    r'\b(distributed|cluster|microservice|load[\s-]?balance)\b',
                    r'\b(growth|expand|increase|volume)\b'
                ],
                'priority': 'medium'
            }
        }
    
    def extract_entities(self, text: str, context: str = "") -> List[ExtractedEntity]:
        """Extract entities from text with confidence scoring"""
        entities = []
        text_lower = text.lower()
        
        for entity_type, config in self.entity_patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    entity_name = match.group(1) if match.groups() else match.group(0)
                    entity_name = entity_name.strip().title()
                    
                    # Skip duplicates
                    if any(e.name.lower() == entity_name.lower() for e in entities):
                        continue
                    
                    # Extract surrounding context
                    start = max(0, match.start() - 20)
                    end = min(len(text), match.end() + 20)
                    local_context = text[start:end].strip()
                    
                    entities.append(ExtractedEntity(
                        name=entity_name,
                        type=entity_type,
                        description=f"Extracted from: \"{local_context}\"",
                        confidence=config['confidence'],
                        context=local_context
                    ))
        
        # Sort by confidence and remove low-confidence duplicates
        entities.sort(key=lambda x: x.confidence, reverse=True)
        return self._deduplicate_entities(entities)
    
    def extract_scenarios(self, text: str) -> List[ExtractedScenario]:
        """Extract scenario patterns from text"""
        scenarios = []
        
        # Look for explicit Given/When/Then patterns
        scenarios.extend(self._extract_explicit_scenarios(text))
        
        # Look for implicit scenarios (if/then, when/should patterns)
        scenarios.extend(self._extract_implicit_scenarios(text))
        
        return scenarios
    
    def _extract_explicit_scenarios(self, text: str) -> List[ExtractedScenario]:
        """Extract explicit Given/When/Then scenarios"""
        scenarios = []
        
        # Pattern for full Given/When/Then scenarios
        gvt_pattern = r'given\s+(.+?)when\s+(.+?)then\s+(.+?)(?=\.|given|$)'
        matches = re.finditer(gvt_pattern, text.lower(), re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            given = match.group(1).strip()
            when = match.group(2).strip()
            then = match.group(3).strip()
            
            scenarios.append(ExtractedScenario(
                title=f"Scenario: {when[:50]}...",
                given=given,
                when=when,
                then=then,
                confidence=0.95,
                entities=self._extract_entities_from_text(f"{given} {when} {then}")
            ))
        
        return scenarios
    
    def _extract_implicit_scenarios(self, text: str) -> List[ExtractedScenario]:
        """Extract implicit scenarios from natural language"""
        scenarios = []
        
        # Pattern for when/should, if/then patterns
        implicit_patterns = [
            r'when\s+(.+?)\s+(?:should|must|will)\s+(.+?)(?=\.|when|if|$)',
            r'if\s+(.+?)\s+(?:then|should|must|will)\s+(.+?)(?=\.|when|if|$)',
            r'(?:after|once)\s+(.+?)\s+(?:should|must|will)\s+(.+?)(?=\.|when|if|$)',
            # Goal-oriented patterns
            r'i(?:\'d like to|want to)\s+(.+?)\s+that\s+(.+?)(?=\.|for example|$)',
            r'(?:system|tool|application)\s+(?:that|should)\s+(.+?)\s+(?:so that|to)\s+(.+?)(?=\.|$)',
            # Process patterns
            r'something\s+(?:i can|that)\s+(.+?)\s+that\s+(.+?)(?=\.|$)'
        ]
        
        for pattern in implicit_patterns:
            matches = re.finditer(pattern, text.lower(), re.IGNORECASE | re.DOTALL)
            for match in matches:
                condition = match.group(1).strip()
                outcome = match.group(2).strip()
                
                scenarios.append(ExtractedScenario(
                    title=f"Scenario: {condition[:50]}...",
                    given="System is ready",
                    when=condition,
                    then=outcome,
                    confidence=0.8,
                    entities=self._extract_entities_from_text(f"{condition} {outcome}")
                ))
        
        return scenarios
    
    def extract_constraints(self, text: str) -> List[ExtractedConstraint]:
        """Extract performance, security, and other constraints"""
        constraints = []
        text_lower = text.lower()
        
        for category, config in self.constraint_patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, text_lower, re.IGNORECASE)
                for match in matches:
                    # Extract context around the match
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end].strip()
                    
                    constraint_name = f"{category.title()} requirement"
                    requirement = f"Based on: \"{context}\""
                    
                    constraints.append(ExtractedConstraint(
                        category=category,
                        name=constraint_name,
                        requirement=requirement,
                        priority=config['priority'],
                        confidence=0.7
                    ))
        
        return self._deduplicate_constraints(constraints)
    
    def _extract_entities_from_text(self, text: str) -> List[str]:
        """Quick entity extraction for scenario context"""
        entities = []
        for entity_type, config in self.entity_patterns.items():
            for pattern in config['patterns']:
                matches = re.finditer(pattern, text.lower(), re.IGNORECASE)
                for match in matches:
                    entity = match.group(1) if match.groups() else match.group(0)
                    entities.append(entity.strip().title())
        return list(set(entities))
    
    def _deduplicate_entities(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove duplicate entities, keeping highest confidence"""
        seen = {}
        for entity in entities:
            key = entity.name.lower()
            if key not in seen or entity.confidence > seen[key].confidence:
                seen[key] = entity
        return list(seen.values())
    
    def _deduplicate_constraints(self, constraints: List[ExtractedConstraint]) -> List[ExtractedConstraint]:
        """Remove duplicate constraints"""
        seen = set()
        unique_constraints = []
        for constraint in constraints:
            key = (constraint.category, constraint.name)
            if key not in seen:
                seen.add(key)
                unique_constraints.append(constraint)
        return unique_constraints
    
    def analyze_conversation_phase(self, text: str, current_entities: int, current_scenarios: int, current_constraints: int) -> str:
        """Determine appropriate conversation phase based on content and current state"""
        text_lower = text.lower()
        
        # Keywords that suggest different phases
        discovery_keywords = ['build', 'create', 'want', 'need', 'system', 'application', 'idea', 'project']
        scenario_keywords = ['when', 'if', 'should', 'behavior', 'action', 'flow', 'process', 'user does']
        constraint_keywords = ['fast', 'secure', 'performance', 'scale', 'requirement', 'must', 'need to']
        review_keywords = ['done', 'complete', 'finished', 'review', 'summary', 'export', 'generate']
        
        discovery_score = sum(1 for kw in discovery_keywords if kw in text_lower)
        scenario_score = sum(1 for kw in scenario_keywords if kw in text_lower)
        constraint_score = sum(1 for kw in constraint_keywords if kw in text_lower)
        review_score = sum(1 for kw in review_keywords if kw in text_lower)
        
        # Consider current state
        if current_entities >= 3 and current_scenarios >= 2 and current_constraints >= 1:
            if review_score > 0:
                return 'review'
        
        if current_entities >= 2 and scenario_score > discovery_score:
            if constraint_score > 0:
                return 'constraint_definition'
            return 'scenario_building'
        
        if current_entities >= 1 and scenario_score > 0:
            return 'scenario_building'
        
        return 'discovery'
    
    def generate_followup_questions(self, entities: List[ExtractedEntity], scenarios: List[ExtractedScenario], 
                                  constraints: List[ExtractedConstraint], phase: str) -> List[str]:
        """Generate contextual follow-up questions based on current state"""
        questions = []
        
        if phase == 'discovery':
            if len(entities) < 3:
                questions.append("What are the main types of users or actors in your system?")
                questions.append("What key data or objects will your system manage?")
            if len(entities) >= 2:
                questions.append("How do these components interact with each other?")
                questions.append("What's the main workflow or process you want to support?")
        
        elif phase == 'scenario_building':
            if len(scenarios) < 3:
                questions.append("What happens when a user first interacts with the system?")
                questions.append("Can you describe the most important user journey?")
            
            # Ask about specific entities
            entity_names = [e.name for e in entities if e.type == 'actor']
            if entity_names:
                questions.append(f"What can a {entity_names[0]} do with the system?")
            
            # Ask about edge cases
            if len(scenarios) >= 2:
                questions.append("What should happen if something goes wrong in this process?")
                questions.append("Are there any special cases or exceptions to consider?")
        
        elif phase == 'constraint_definition':
            if len(constraints) < 2:
                questions.append("How fast should the system respond to user actions?")
                questions.append("What are your security requirements?")
                questions.append("How many users do you expect to use this simultaneously?")
            
            if any(c.category == 'performance' for c in constraints):
                questions.append("What happens if the system gets overloaded?")
        
        elif phase == 'review':
            questions.append("Does this capture everything you wanted in your system?")
            questions.append("Are there any edge cases or scenarios we missed?")
            questions.append("Would you like to refine any of these requirements?")
        
        return questions[:3]  # Limit to 3 questions