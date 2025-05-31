"""
Contextual Follow-up Question Engine
Generates intelligent, targeted questions based on conversation context and extracted entities
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict, Counter

from models import ConversationState, ConversationPhase, Entity, Scenario, Constraint

class QuestionType(Enum):
    CLARIFICATION = "clarification"
    EXPLORATION = "exploration" 
    VALIDATION = "validation"
    EDGE_CASE = "edge_case"
    CONSTRAINT = "constraint"
    RELATIONSHIP = "relationship"
    SCENARIO = "scenario"

@dataclass
class FollowUpQuestion:
    question: str
    type: QuestionType
    priority: float  # 0.0 to 1.0
    context: str
    target_entities: List[str]
    reasoning: str
    expected_response_type: str  # "entity", "scenario", "constraint", "clarification"

class ContextualFollowupEngine:
    """Generate smart follow-up questions based on conversation context"""
    
    def __init__(self):
        # Question templates by type and context
        self.question_templates = {
            QuestionType.CLARIFICATION: {
                'vague_entity': [
                    "You mentioned '{entity}' - can you tell me more about what this represents in your system?",
                    "When you say '{entity}', what specific role does it play?",
                    "Could you elaborate on '{entity}'? What are its main responsibilities?"
                ],
                'ambiguous_relationship': [
                    "How does {entity1} interact with {entity2}?",
                    "What's the relationship between {entity1} and {entity2}?",
                    "When {entity1} and {entity2} work together, what happens?"
                ],
                'missing_details': [
                    "What specific information does {entity} need to work with?",
                    "What are the key properties or attributes of {entity}?",
                    "How is {entity} structured or organized?"
                ]
            },
            QuestionType.EXPLORATION: {
                'user_journey': [
                    "What happens before a {actor} {action}?",
                    "After a {actor} {action}, what's the next step?", 
                    "Walk me through what a {actor} experiences when they {action}"
                ],
                'system_boundaries': [
                    "What systems or services does {component} connect to?",
                    "What external dependencies does {component} rely on?",
                    "How does {component} communicate with other parts of the system?"
                ],
                'data_flow': [
                    "What data flows into {entity}?",
                    "What happens to the data after it's processed by {entity}?",
                    "How is {entity} data validated or transformed?"
                ]
            },
            QuestionType.EDGE_CASE: {
                'error_scenarios': [
                    "What happens if {entity} is unavailable or fails?",
                    "How should the system behave when {actor} provides invalid {data}?",
                    "What if {entity} is empty or doesn't exist?"
                ],
                'boundary_conditions': [
                    "What's the maximum number of {entity} the system should handle?",
                    "How should the system behave when there are too many {entity}?",
                    "What happens if {actor} tries to {action} without permission?"
                ],
                'timing_issues': [
                    "What if {action} takes longer than expected?",
                    "How should the system handle simultaneous {action} requests?",
                    "What if {actor} {action} while {other_action} is happening?"
                ]
            },
            QuestionType.CONSTRAINT: {
                'performance': [
                    "How fast should {action} complete for a good user experience?",
                    "How many {entity} should the system handle simultaneously?",
                    "What response time do {actor} expect for {action}?"
                ],
                'security': [
                    "Who should be allowed to {action} {entity}?",
                    "What sensitive information does {entity} contain?",
                    "How should {entity} be protected from unauthorized access?"
                ],
                'reliability': [
                    "How critical is {entity} to the overall system?", 
                    "What happens if {component} goes down?",
                    "How often can {action} fail before it becomes a problem?"
                ]
            },
            QuestionType.VALIDATION: [
                "Does this sound right: {scenario}?",
                "Is this what you had in mind: {entity} {relationship} {target}?",
                "Am I understanding correctly that {assumption}?"
            ],
            QuestionType.SCENARIO: {
                'happy_path': [
                    "Can you describe the ideal scenario where {actor} successfully {action}?",
                    "What's the most common way {actor} would {action}?",
                    "Walk me through a typical {entity} workflow"
                ],
                'alternative_paths': [
                    "Are there different ways {actor} might {action}?",
                    "What if {actor} wants to {action} differently?",
                    "What alternatives should {actor} have for {action}?"
                ],
                'integration_scenarios': [
                    "How does {entity} work with other parts of the system?",
                    "What needs to happen when {entity} is created/updated/deleted?",
                    "How do changes to {entity} affect other {related_entity}?"
                ]
            }
        }
        
        # Domain-specific question patterns
        self.domain_patterns = {
            'web_application': {
                'authentication': [
                    "How do users log in and manage their sessions?",
                    "What happens when a user forgets their password?",
                    "Should there be different types of user accounts?"
                ],
                'api_design': [
                    "What data format should the API use (JSON, XML)?",
                    "How should the API handle rate limiting?",
                    "What HTTP status codes should different operations return?"
                ],
                'frontend_ux': [
                    "How should the interface guide users through this process?",
                    "What feedback should users get during long operations?",
                    "How should errors be displayed to users?"
                ]
            },
            'data_processing': {
                'pipeline_design': [
                    "What should happen if data processing fails partway through?",
                    "How should the system handle data quality issues?",
                    "What monitoring is needed for data pipeline health?"
                ],
                'data_validation': [
                    "How should invalid or corrupted data be handled?",
                    "What data quality checks are essential?",
                    "How should data inconsistencies be resolved?"
                ]
            },
            'ai_ml': {
                'model_performance': [
                    "What accuracy or performance metrics are acceptable?",
                    "How should the system handle model predictions with low confidence?",
                    "What happens when the model needs to be retrained?"
                ],
                'data_requirements': [
                    "What training data is needed for good model performance?",
                    "How should biased or unrepresentative data be handled?",
                    "What data preprocessing steps are required?"
                ]
            }
        }
        
        # Context analysis patterns
        self.context_indicators = {
            'incomplete_workflow': [
                r'(\w+)\s+(?:can|will|should)\s+(\w+)',
                r'when\s+(\w+)\s+(\w+)',
                r'(\w+)\s+needs?\s+to\s+(\w+)'
            ],
            'missing_error_handling': [
                r'if\s+(\w+)\s+fails?',
                r'when\s+(\w+)\s+(?:is\s+)?(?:not\s+)?available',
                r'error|exception|failure'
            ],
            'vague_entities': [
                r'\b(system|service|component|thing|stuff|data|information)\b',
                r'\b(it|this|that)\b'
            ],
            'integration_gaps': [
                r'(\w+)\s+(?:connects?\s+to|integrates?\s+with|uses?)\s+(\w+)',
                r'(\w+)\s+(?:sends?\s+to|receives?\s+from)\s+(\w+)'
            ]
        }

    def generate_followup_questions(
        self,
        conversation_state: ConversationState,
        recent_message: str,
        conversation_history: List[Dict[str, str]],
        domain_hint: Optional[str] = None
    ) -> List[FollowUpQuestion]:
        """Generate contextual follow-up questions"""
        
        questions = []
        
        # 1. Analyze current conversation context
        context_analysis = self._analyze_conversation_context(
            conversation_state, recent_message, conversation_history
        )
        
        # 2. Generate phase-appropriate questions
        phase_questions = self._generate_phase_questions(
            conversation_state, context_analysis
        )
        questions.extend(phase_questions)
        
        # 3. Generate entity-based questions
        entity_questions = self._generate_entity_questions(
            conversation_state.discovered_entities, recent_message, context_analysis
        )
        questions.extend(entity_questions)
        
        # 4. Generate scenario completion questions
        scenario_questions = self._generate_scenario_questions(
            conversation_state.scenarios, context_analysis
        )
        questions.extend(scenario_questions)
        
        # 5. Generate constraint discovery questions
        constraint_questions = self._generate_constraint_questions(
            conversation_state, context_analysis, domain_hint
        )
        questions.extend(constraint_questions)
        
        # 6. Generate domain-specific questions
        if domain_hint and domain_hint in self.domain_patterns:
            domain_questions = self._generate_domain_questions(
                domain_hint, context_analysis
            )
            questions.extend(domain_questions)
        
        # 7. Score and rank questions
        scored_questions = self._score_and_rank_questions(
            questions, conversation_state, context_analysis
        )
        
        # Return top 3-5 questions
        return scored_questions[:5]
    
    def _analyze_conversation_context(
        self,
        state: ConversationState,
        recent_message: str,
        history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Analyze conversation context for question generation"""
        
        # Get recent conversation text
        recent_text = " ".join([msg["content"] for msg in history[-3:]] + [recent_message])
        
        analysis = {
            'mentioned_entities': self._extract_mentioned_entities(recent_message, state.discovered_entities),
            'incomplete_workflows': self._find_incomplete_workflows(recent_text),
            'missing_error_handling': self._check_error_handling_gaps(recent_text),
            'vague_references': self._find_vague_references(recent_text),
            'integration_gaps': self._find_integration_gaps(recent_text),
            'conversation_gaps': self._identify_conversation_gaps(state),
            'user_intent': self._analyze_user_intent(recent_message),
            'complexity_level': self._assess_complexity_level(state),
            'recent_topics': self._extract_recent_topics(history)
        }
        
        return analysis
    
    def _generate_phase_questions(
        self,
        state: ConversationState,
        context: Dict[str, Any]
    ) -> List[FollowUpQuestion]:
        """Generate questions appropriate for current conversation phase"""
        
        questions = []
        
        if state.phase == ConversationPhase.DISCOVERY:
            # Focus on understanding system purpose and main entities
            if len(state.discovered_entities) < 3:
                questions.append(FollowUpQuestion(
                    question="What are the main components or parts of your system?",
                    type=QuestionType.EXPLORATION,
                    priority=0.9,
                    context="discovery_entities",
                    target_entities=[],
                    reasoning="Need more entities for system understanding",
                    expected_response_type="entity"
                ))
            
            if not context.get('user_intent'):
                questions.append(FollowUpQuestion(
                    question="What's the main goal or purpose of this system?",
                    type=QuestionType.CLARIFICATION,
                    priority=0.8,
                    context="discovery_purpose",
                    target_entities=[],
                    reasoning="System purpose not clear",
                    expected_response_type="clarification"
                ))
        
        elif state.phase == ConversationPhase.SCENARIO_BUILDING:
            # Focus on workflows and user journeys
            if len(state.scenarios) < 2:
                questions.append(FollowUpQuestion(
                    question="Can you walk me through a typical user workflow or process?",
                    type=QuestionType.SCENARIO,
                    priority=0.9,
                    context="scenario_building",
                    target_entities=context.get('mentioned_entities', []),
                    reasoning="Need more scenarios for comprehensive coverage",
                    expected_response_type="scenario"
                ))
        
        elif state.phase == ConversationPhase.CONSTRAINT_DEFINITION:
            # Focus on non-functional requirements
            if len(state.constraints) < 2:
                questions.append(FollowUpQuestion(
                    question="What performance, security, or reliability requirements are important?",
                    type=QuestionType.CONSTRAINT,
                    priority=0.9,
                    context="constraint_definition",
                    target_entities=[],
                    reasoning="Need more constraints for complete specification",
                    expected_response_type="constraint"
                ))
        
        return questions
    
    def _generate_entity_questions(
        self,
        entities: List[Entity],
        recent_message: str,
        context: Dict[str, Any]
    ) -> List[FollowUpQuestion]:
        """Generate questions about specific entities"""
        
        questions = []
        mentioned_entities = context.get('mentioned_entities', [])
        
        for entity in mentioned_entities:
            # Check for vague or incomplete entity descriptions
            if not entity.description or len(entity.description) < 20:
                template = self._select_template(
                    self.question_templates[QuestionType.CLARIFICATION]['vague_entity']
                )
                question = template.format(entity=entity.name)
                
                questions.append(FollowUpQuestion(
                    question=question,
                    type=QuestionType.CLARIFICATION,
                    priority=0.7,
                    context=f"clarify_entity_{entity.name}",
                    target_entities=[entity.name],
                    reasoning=f"Entity {entity.name} needs more detail",
                    expected_response_type="entity"
                ))
            
            # Look for relationship opportunities
            related_entities = self._find_related_entities(entity, entities)
            if related_entities:
                other_entity = related_entities[0]
                template = self._select_template(
                    self.question_templates[QuestionType.CLARIFICATION]['ambiguous_relationship']
                )
                question = template.format(entity1=entity.name, entity2=other_entity.name)
                
                questions.append(FollowUpQuestion(
                    question=question,
                    type=QuestionType.RELATIONSHIP,
                    priority=0.6,
                    context=f"relationship_{entity.name}_{other_entity.name}",
                    target_entities=[entity.name, other_entity.name],
                    reasoning=f"Clarify relationship between {entity.name} and {other_entity.name}",
                    expected_response_type="clarification"
                ))
        
        return questions
    
    def _generate_edge_case_questions(
        self,
        entities: List[Entity],
        context: Dict[str, Any]
    ) -> List[FollowUpQuestion]:
        """Generate questions about edge cases and error handling"""
        
        questions = []
        
        # Look for entities that might fail or be unavailable
        critical_entities = [e for e in entities if e.type in ['system_component', 'data_entity']]
        
        for entity in critical_entities[:2]:  # Limit to avoid overwhelming
            template = self._select_template(
                self.question_templates[QuestionType.EDGE_CASE]['error_scenarios']
            )
            question = template.format(entity=entity.name)
            
            questions.append(FollowUpQuestion(
                question=question,
                type=QuestionType.EDGE_CASE,
                priority=0.5,
                context=f"edge_case_{entity.name}",
                target_entities=[entity.name],
                reasoning=f"Consider failure scenarios for {entity.name}",
                expected_response_type="scenario"
            ))
        
        return questions
    
    def _generate_constraint_questions(
        self,
        state: ConversationState,
        context: Dict[str, Any],
        domain_hint: Optional[str]
    ) -> List[FollowUpQuestion]:
        """Generate questions about constraints and non-functional requirements"""
        
        questions = []
        
        # Check for missing constraint categories
        existing_categories = set(c.category.value for c in state.constraints)
        missing_categories = {'performance', 'security', 'reliability', 'scalability'} - existing_categories
        
        if 'performance' in missing_categories and context.get('mentioned_entities'):
            entity = context['mentioned_entities'][0]
            template = self._select_template(
                self.question_templates[QuestionType.CONSTRAINT]['performance']
            )
            question = template.format(entity=entity.name, action="process")
            
            questions.append(FollowUpQuestion(
                question=question,
                type=QuestionType.CONSTRAINT,
                priority=0.6,
                context="performance_constraint",
                target_entities=[entity.name],
                reasoning="Need performance requirements",
                expected_response_type="constraint"
            ))
        
        return questions
    
    def _generate_domain_questions(
        self,
        domain: str,
        context: Dict[str, Any]
    ) -> List[FollowUpQuestion]:
        """Generate domain-specific questions"""
        
        questions = []
        
        if domain in self.domain_patterns:
            patterns = self.domain_patterns[domain]
            
            # Select relevant domain questions based on context
            for category, category_questions in patterns.items():
                if self._is_category_relevant(category, context):
                    question_text = self._select_template(category_questions)
                    
                    questions.append(FollowUpQuestion(
                        question=question_text,
                        type=QuestionType.EXPLORATION,
                        priority=0.4,
                        context=f"domain_{domain}_{category}",
                        target_entities=[],
                        reasoning=f"Domain-specific {category} question",
                        expected_response_type="clarification"
                    ))
        
        return questions
    
    def _score_and_rank_questions(
        self,
        questions: List[FollowUpQuestion],
        state: ConversationState,
        context: Dict[str, Any]
    ) -> List[FollowUpQuestion]:
        """Score and rank questions by relevance and importance"""
        
        for question in questions:
            # Base score is the priority
            score = question.priority
            
            # Boost questions about recently mentioned entities
            mentioned_entities = context.get('mentioned_entities', [])
            if any(entity.name in question.target_entities for entity in mentioned_entities):
                score += 0.2
            
            # Boost questions that fill conversation gaps
            if question.type == QuestionType.CLARIFICATION:
                score += 0.1
            
            # Boost phase-appropriate questions
            if ((state.phase == ConversationPhase.DISCOVERY and question.type == QuestionType.EXPLORATION) or
                (state.phase == ConversationPhase.SCENARIO_BUILDING and question.type == QuestionType.SCENARIO) or
                (state.phase == ConversationPhase.CONSTRAINT_DEFINITION and question.type == QuestionType.CONSTRAINT)):
                score += 0.15
            
            # Penalize redundant questions
            if self._is_redundant_question(question, state):
                score -= 0.3
            
            question.priority = min(score, 1.0)
        
        # Sort by priority (descending)
        return sorted(questions, key=lambda q: q.priority, reverse=True)
    
    # Helper methods
    def _extract_mentioned_entities(self, text: str, entities: List[Entity]) -> List[Entity]:
        """Find entities mentioned in the text"""
        mentioned = []
        text_lower = text.lower()
        
        for entity in entities:
            if entity.name.lower() in text_lower:
                mentioned.append(entity)
        
        return mentioned
    
    def _find_incomplete_workflows(self, text: str) -> List[str]:
        """Find indications of incomplete workflows"""
        workflows = []
        
        for pattern in self.context_indicators['incomplete_workflow']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                workflows.append(match.group(0))
        
        return workflows
    
    def _check_error_handling_gaps(self, text: str) -> bool:
        """Check if error handling is mentioned"""
        for pattern in self.context_indicators['missing_error_handling']:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _find_vague_references(self, text: str) -> List[str]:
        """Find vague entity references"""
        vague = []
        
        for pattern in self.context_indicators['vague_entities']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                vague.append(match.group(0))
        
        return vague
    
    def _find_integration_gaps(self, text: str) -> List[Tuple[str, str]]:
        """Find potential integration points"""
        integrations = []
        
        for pattern in self.context_indicators['integration_gaps']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match.groups()) >= 2:
                    integrations.append((match.group(1), match.group(2)))
        
        return integrations
    
    def _identify_conversation_gaps(self, state: ConversationState) -> List[str]:
        """Identify gaps in the conversation"""
        gaps = []
        
        if len(state.discovered_entities) < 3:
            gaps.append("insufficient_entities")
        
        if len(state.scenarios) < 1:
            gaps.append("no_scenarios")
        
        if len(state.constraints) < 1:
            gaps.append("no_constraints")
        
        # Check for entity types
        entity_types = set(e.type for e in state.discovered_entities)
        if 'actor' not in entity_types:
            gaps.append("no_actors")
        
        return gaps
    
    def _analyze_user_intent(self, message: str) -> Optional[str]:
        """Analyze user intent from message"""
        intent_patterns = {
            'create': r'\b(?:create|build|make|develop|implement)\b',
            'modify': r'\b(?:change|update|modify|alter|edit)\b',
            'understand': r'\b(?:explain|describe|tell|show|how)\b',
            'integrate': r'\b(?:connect|integrate|link|combine)\b'
        }
        
        for intent, pattern in intent_patterns.items():
            if re.search(pattern, message, re.IGNORECASE):
                return intent
        
        return None
    
    def _assess_complexity_level(self, state: ConversationState) -> str:
        """Assess the complexity level of the system being described"""
        entity_count = len(state.discovered_entities)
        scenario_count = len(state.scenarios)
        
        if entity_count < 3 and scenario_count < 2:
            return "simple"
        elif entity_count < 8 and scenario_count < 5:
            return "moderate"
        else:
            return "complex"
    
    def _extract_recent_topics(self, history: List[Dict[str, str]]) -> List[str]:
        """Extract recent conversation topics"""
        topics = []
        
        # Simple keyword extraction from recent messages
        recent_messages = [msg["content"] for msg in history[-3:]]
        all_text = " ".join(recent_messages).lower()
        
        # Common topic indicators
        topic_patterns = [
            r'\b(?:about|regarding|concerning)\s+(\w+)',
            r'\b(?:the|a|an)\s+(\w+(?:\s+\w+)?)\s+(?:is|will|should|can)',
            r'\b(\w+)\s+(?:feature|functionality|capability|component)'
        ]
        
        for pattern in topic_patterns:
            matches = re.finditer(pattern, all_text)
            for match in matches:
                topics.append(match.group(1))
        
        return list(set(topics))  # Remove duplicates
    
    def _find_related_entities(self, entity: Entity, all_entities: List[Entity]) -> List[Entity]:
        """Find entities that might be related to the given entity"""
        related = []
        
        for other in all_entities:
            if other.name != entity.name:
                # Check if they might be related based on type or context
                if ((entity.type == 'actor' and other.type == 'data_entity') or
                    (entity.type == 'system_component' and other.type == 'data_entity')):
                    related.append(other)
        
        return related[:2]  # Limit to avoid too many questions
    
    def _select_template(self, templates: List[str]) -> str:
        """Select a template from a list (could be randomized)"""
        return templates[0]  # For now, just return the first one
    
    def _is_category_relevant(self, category: str, context: Dict[str, Any]) -> bool:
        """Check if a domain category is relevant to current context"""
        # Simple relevance check - could be more sophisticated
        mentioned_entities = context.get('mentioned_entities', [])
        
        if category == 'authentication' and any('user' in e.name.lower() for e in mentioned_entities):
            return True
        
        if category == 'api_design' and any('api' in e.name.lower() for e in mentioned_entities):
            return True
        
        return False
    
    def _is_redundant_question(self, question: FollowUpQuestion, state: ConversationState) -> bool:
        """Check if the question is redundant given current state"""
        # Simple redundancy check - avoid asking about entities with detailed descriptions
        for entity_name in question.target_entities:
            entity = next((e for e in state.discovered_entities if e.name == entity_name), None)
            if entity and entity.description and len(entity.description) > 50:
                return True
        
        return False

    def _generate_scenario_questions(
        self,
        scenarios: List[Scenario],
        context: Dict[str, Any]
    ) -> List[FollowUpQuestion]:
        """Generate questions about scenario completeness"""
        questions = []
        
        # If we have scenarios but they seem incomplete
        for scenario in scenarios:
            if not scenario.then or len(scenario.then) < 10:
                questions.append(FollowUpQuestion(
                    question=f"For the scenario '{scenario.title}', what should be the expected outcome?",
                    type=QuestionType.SCENARIO,
                    priority=0.6,
                    context=f"complete_scenario_{scenario.title}",
                    target_entities=scenario.entities,
                    reasoning=f"Scenario {scenario.title} needs completion",
                    expected_response_type="scenario"
                ))
        
        return questions