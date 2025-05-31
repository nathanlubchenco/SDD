import re
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from models import (
    ConversationState, ConversationResponse, ConversationPhase, 
    Entity, Scenario, Constraint, ConstraintCategory, ScenarioStatus,
    ExpertiseLevel, ConstraintPriority
)
from simple_ai_client_complete import SimpleAIClient as AIClient
from nlp_extractor import NLPExtractor, ExtractedEntity, ExtractedScenario, ExtractedConstraint

class ConversationEngine:
    """
    Core conversation engine that manages the dialog flow and extracts
    specification information from natural language conversations.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state = ConversationState()
        self.ai_client = AIClient()
        self.nlp_extractor = NLPExtractor()
        self.conversation_history: List[Dict[str, str]] = []
        
    async def process_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process a user message and return AI response with state updates
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate AI response based on current phase
        response = await self._generate_response(user_message)
        
        # Add AI response to history
        self.conversation_history.append({
            "role": "assistant", 
            "content": response.message,
            "timestamp": datetime.now().isoformat()
        })
        
        # Extract and update state from the conversation
        await self._extract_and_update_state(user_message)
        
        # Generate contextual follow-up questions
        response.suggested_actions = self.nlp_extractor.generate_followup_questions(
            self.state.discovered_entities,
            self.state.scenarios, 
            self.state.constraints,
            self.state.phase.value
        )
        
        return {
            "message": response.message,
            "state_updated": response.state_updated,
            "suggested_actions": response.suggested_actions,
            "phase_transition": response.phase_transition
        }
    
    async def _generate_response(self, user_message: str) -> ConversationResponse:
        """
        Generate appropriate AI response based on conversation phase and context
        """
        phase_prompts = {
            ConversationPhase.DISCOVERY: self._get_discovery_prompt(),
            ConversationPhase.SCENARIO_BUILDING: self._get_scenario_building_prompt(),
            ConversationPhase.CONSTRAINT_DEFINITION: self._get_constraint_prompt(),
            ConversationPhase.REVIEW: self._get_review_prompt()
        }
        
        system_prompt = phase_prompts[self.state.phase]
        
        # Build context from current state
        context = self._build_context()
        
        full_prompt = f"{system_prompt}\n\nCurrent Context:\n{context}\n\nUser Message: {user_message}"
        
        try:
            ai_response = await self.ai_client.generate_response(full_prompt, self.conversation_history)
            
            # Determine if we should transition phases
            new_phase = self._should_transition_phase(user_message, ai_response)
            
            # Check if state was updated
            state_updated = await self._will_state_update(user_message)
            
            return ConversationResponse(
                message=ai_response,
                state_updated=state_updated,
                phase_transition=new_phase
            )
            
        except Exception as e:
            print(f"Error generating AI response: {e}")
            return ConversationResponse(
                message="I apologize, but I'm having trouble processing that right now. Could you please rephrase your message?",
                state_updated=False
            )
    
    def _get_discovery_prompt(self) -> str:
        return """You are an expert system architect helping users discover and define their system requirements. 

Your role in the DISCOVERY phase:
1. Ask open-ended questions to understand what the user wants to build
2. Help them identify the main entities, actors, and high-level behaviors
3. Guide them toward describing concrete scenarios
4. Adapt your language to their expertise level
5. Be encouraging and make the process feel collaborative

Guidelines:
- Ask one focused question at a time
- Build on their previous answers to show understanding
- Use examples to clarify abstract concepts
- When you sense they have a clear picture, suggest moving to scenario building
- Keep responses conversational and engaging

Current expertise level: {expertise_level}
Entities discovered so far: {entity_count}
"""

    def _get_scenario_building_prompt(self) -> str:
        return """You are helping the user build concrete scenarios using Given/When/Then format.

Your role in SCENARIO BUILDING:
1. Guide them to describe specific behaviors and interactions
2. Help structure their descriptions into clear Given/When/Then scenarios
3. Ask clarifying questions to make scenarios more precise
4. Identify missing edge cases and alternative flows
5. Ensure scenarios are testable and complete

Guidelines:
- Focus on user-observable behaviors
- Make scenarios specific and measurable
- Ask about error cases and boundary conditions
- Suggest related scenarios they might have missed
- When you have enough scenarios, guide toward constraints

Current scenarios: {scenario_count}
"""

    def _get_constraint_prompt(self) -> str:
        return """You are helping define non-functional requirements and constraints.

Your role in CONSTRAINT DEFINITION:
1. Help identify performance, security, scalability, and reliability requirements
2. Make abstract quality attributes concrete and measurable
3. Help them understand trade-offs between different requirements
4. Guide them to realistic and achievable constraints

Guidelines:
- Ask about specific metrics (response time, throughput, etc.)
- Discuss user expectations and business needs
- Help prioritize constraints by importance
- Make requirements testable and verifiable
- Use industry standards and benchmarks as reference

Current constraints: {constraint_count}
"""

    def _get_review_prompt(self) -> str:
        return """You are helping review and finalize the specification.

Your role in REVIEW:
1. Summarize what has been captured
2. Identify any gaps or inconsistencies
3. Suggest improvements and optimizations
4. Prepare them for implementation
5. Celebrate what they've accomplished

Guidelines:
- Provide a comprehensive summary
- Ask if anything is missing
- Highlight the quality of their specification
- Suggest next steps for implementation
- Make them feel confident about their work

Total elements captured: {total_elements}
"""

    def _build_context(self) -> str:
        """Build contextual information for the AI prompt"""
        context_parts = []
        
        context_parts.append(f"Phase: {self.state.phase.value}")
        context_parts.append(f"Progress: {self.state.progress_score}%")
        context_parts.append(f"User expertise: {self.state.user_expertise_level.value}")
        
        if self.state.discovered_entities:
            entities = [e.name for e in self.state.discovered_entities]
            context_parts.append(f"Entities: {', '.join(entities)}")
        
        if self.state.scenarios:
            context_parts.append(f"Scenarios: {len(self.state.scenarios)} defined")
            
        if self.state.constraints:
            context_parts.append(f"Constraints: {len(self.state.constraints)} defined")
            
        if self.state.current_topic:
            context_parts.append(f"Current topic: {self.state.current_topic}")
            
        return "\n".join(context_parts)
    
    async def _extract_and_update_state(self, user_message: str):
        """Extract entities, scenarios, and constraints from the conversation using advanced NLP"""
        
        print(f"🔍 Extracting from: {user_message[:100]}...")
        
        # Extract entities using NLP
        extracted_entities = self.nlp_extractor.extract_entities(user_message)
        for ext_entity in extracted_entities:
            # Check if entity already exists
            if not any(e.name.lower() == ext_entity.name.lower() for e in self.state.discovered_entities):
                entity = Entity(
                    name=ext_entity.name,
                    type=ext_entity.type,
                    description=ext_entity.description
                )
                self.state.discovered_entities.append(entity)
                print(f"✅ New entity: {ext_entity.name} ({ext_entity.type})")
        
        # Extract scenarios using NLP
        extracted_scenarios = self.nlp_extractor.extract_scenarios(user_message)
        for ext_scenario in extracted_scenarios:
            scenario = Scenario(
                title=ext_scenario.title,
                given=ext_scenario.given,
                when=ext_scenario.when,
                then=ext_scenario.then,
                status=ScenarioStatus.DRAFT,
                entities=ext_scenario.entities
            )
            self.state.scenarios.append(scenario)
            print(f"✅ New scenario: {ext_scenario.title}")
        
        # Extract constraints using NLP
        extracted_constraints = self.nlp_extractor.extract_constraints(user_message)
        for ext_constraint in extracted_constraints:
            # Map string category to enum
            category_map = {
                'performance': ConstraintCategory.PERFORMANCE,
                'security': ConstraintCategory.SECURITY,
                'reliability': ConstraintCategory.RELIABILITY,
                'scalability': ConstraintCategory.SCALABILITY
            }
            
            # Map string priority to enum
            priority_map = {
                'low': ConstraintPriority.LOW,
                'medium': ConstraintPriority.MEDIUM,
                'high': ConstraintPriority.HIGH
            }
            
            constraint = Constraint(
                category=category_map.get(ext_constraint.category, ConstraintCategory.PERFORMANCE),
                name=ext_constraint.name,
                requirement=ext_constraint.requirement,
                priority=priority_map.get(ext_constraint.priority, ConstraintPriority.MEDIUM)
            )
            self.state.constraints.append(constraint)
            print(f"✅ New constraint: {ext_constraint.name} ({ext_constraint.category})")
        
        # Update progress score
        self._update_progress_score()
        
        # Check for phase transitions using NLP analysis
        new_phase_str = self.nlp_extractor.analyze_conversation_phase(
            user_message,
            len(self.state.discovered_entities),
            len(self.state.scenarios),
            len(self.state.constraints)
        )
        
        # Map string phase to enum
        phase_map = {
            'discovery': ConversationPhase.DISCOVERY,
            'scenario_building': ConversationPhase.SCENARIO_BUILDING,
            'constraint_definition': ConversationPhase.CONSTRAINT_DEFINITION,
            'review': ConversationPhase.REVIEW
        }
        
        new_phase = phase_map.get(new_phase_str)
        if new_phase and new_phase != self.state.phase:
            print(f"🔄 Phase transition: {self.state.phase.value} → {new_phase.value}")
            self.state.phase = new_phase
    
    def _update_progress_score(self):
        """Calculate and update progress score based on current state"""
        score = 0
        
        # Discovery phase scoring
        if self.state.discovered_entities:
            score += min(30, len(self.state.discovered_entities) * 10)
        
        # Scenario building scoring
        if self.state.scenarios:
            score += min(40, len(self.state.scenarios) * 8)
        
        # Constraint definition scoring
        if self.state.constraints:
            score += min(20, len(self.state.constraints) * 5)
        
        # Completion bonus
        if (self.state.discovered_entities and 
            self.state.scenarios and 
            self.state.constraints):
            score += 10
        
        self.state.progress_score = min(100, score)
    
    def _check_phase_transition(self) -> Optional[ConversationPhase]:
        """Check if we should transition to a new phase"""
        current_phase = self.state.phase
        
        if current_phase == ConversationPhase.DISCOVERY:
            if len(self.state.discovered_entities) >= 2:
                return ConversationPhase.SCENARIO_BUILDING
        
        elif current_phase == ConversationPhase.SCENARIO_BUILDING:
            if len(self.state.scenarios) >= 3:
                return ConversationPhase.CONSTRAINT_DEFINITION
        
        elif current_phase == ConversationPhase.CONSTRAINT_DEFINITION:
            if len(self.state.constraints) >= 2:
                return ConversationPhase.REVIEW
        
        return None
    
    def _should_transition_phase(self, user_message: str, ai_response: str) -> Optional[ConversationPhase]:
        """Determine if we should transition phases based on conversation content"""
        # Simple heuristics - in production, use more sophisticated analysis
        transition_keywords = {
            ConversationPhase.SCENARIO_BUILDING: ['scenario', 'behavior', 'what happens', 'how does'],
            ConversationPhase.CONSTRAINT_DEFINITION: ['performance', 'fast', 'secure', 'requirement'],
            ConversationPhase.REVIEW: ['done', 'complete', 'finished', 'review', 'summary']
        }
        
        for phase, keywords in transition_keywords.items():
            if any(keyword in user_message.lower() for keyword in keywords):
                if phase.value != self.state.phase.value:
                    return phase
        
        return None
    
    async def _will_state_update(self, user_message: str) -> bool:
        """Determine if the message will result in state updates"""
        # Simple check - in production, use more sophisticated analysis
        update_indicators = [
            'entity', 'scenario', 'constraint', 'requirement',
            'when', 'then', 'given', 'user', 'system'
        ]
        return any(indicator in user_message.lower() for indicator in update_indicators)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current conversation state as dictionary"""
        return self.state.model_dump()
    
    def reset_state(self):
        """Reset conversation state"""
        self.state = ConversationState()
        self.conversation_history.clear()