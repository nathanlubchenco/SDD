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
from enhanced_nlp_extractor import EnhancedNLPExtractor, EnhancedEntity
from contextual_followup_engine import ContextualFollowupEngine, FollowUpQuestion
from scenario_builder import ScenarioBuilder
from visualization_engine import VisualizationEngine

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
        self.enhanced_extractor = EnhancedNLPExtractor()
        self.followup_engine = ContextualFollowupEngine()
        self.scenario_builder = ScenarioBuilder()
        self.visualization_engine = VisualizationEngine()
        self.conversation_history: List[Dict[str, str]] = []
        self.detected_domain = None
        
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
        
        # Generate enhanced contextual follow-up questions
        try:
            followup_questions = self.followup_engine.generate_followup_questions(
                conversation_state=self.state,
                recent_message=user_message,
                conversation_history=self.conversation_history,
                domain_hint=self.detected_domain
            )
            
            # Convert to suggested actions format
            response.suggested_actions = [
                {
                    "text": q.question,
                    "type": q.type.value,
                    "priority": q.priority,
                    "reasoning": q.reasoning
                }
                for q in followup_questions[:3]  # Limit to top 3
            ]
            
            print(f"🎯 Generated {len(followup_questions)} contextual follow-up questions")
            
        except Exception as e:
            print(f"⚠️ Contextual follow-up generation failed, using fallback: {e}")
            # Fallback to basic questions
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
        """Extract entities, scenarios, and constraints from the conversation using enhanced NLP"""
        
        print(f"🔍 Enhanced extraction from: {user_message[:100]}...")
        
        # Detect domain if not already detected
        if not self.detected_domain:
            self.detected_domain = self.enhanced_extractor.detect_domain(user_message)
            if self.detected_domain:
                print(f"🎯 Detected domain: {self.detected_domain}")
        
        # Build conversation context for better extraction
        full_context = " ".join([msg["content"] for msg in self.conversation_history[-3:]])
        
        # Extract entities using enhanced NLP
        try:
            enhanced_entities = self.enhanced_extractor.extract_entities_enhanced(
                text=user_message,
                context=full_context,
                domain_hint=self.detected_domain
            )
            
            # Convert enhanced entities to our format and add to state
            for enh_entity in enhanced_entities:
                # Check if entity already exists (by canonical name)
                existing_entity = None
                for e in self.state.discovered_entities:
                    if (e.name.lower() == enh_entity.canonical_name.lower() or 
                        e.name.lower() == enh_entity.name.lower()):
                        existing_entity = e
                        break
                
                if not existing_entity:
                    # Create rich description with enhanced information
                    description_parts = [enh_entity.description]
                    
                    if enh_entity.relationships:
                        description_parts.append(f"Relationships: {', '.join(enh_entity.relationships[:3])}")
                    
                    if enh_entity.synonyms:
                        description_parts.append(f"Also known as: {', '.join(list(enh_entity.synonyms)[:3])}")
                    
                    if enh_entity.context.syntactic_role != 'unknown':
                        description_parts.append(f"Role: {enh_entity.context.syntactic_role}")
                    
                    entity = Entity(
                        name=enh_entity.name,
                        type=enh_entity.type,
                        description=" | ".join(description_parts)
                    )
                    self.state.discovered_entities.append(entity)
                    print(f"✅ Enhanced entity: {enh_entity.name} ({enh_entity.type}, conf: {enh_entity.confidence:.2f})")
                    
                    # Log additional context for debugging
                    if enh_entity.relationships:
                        print(f"   🔗 Relationships: {enh_entity.relationships[:2]}")
                    if enh_entity.context.semantic_class != 'unknown':
                        print(f"   🏷️  Semantic class: {enh_entity.context.semantic_class}")
                        
        except Exception as e:
            print(f"⚠️ Enhanced extraction failed, falling back to basic: {e}")
            # Fallback to basic extraction
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
                    print(f"✅ Fallback entity: {ext_entity.name} ({ext_entity.type})")
        
        # Extract scenarios using enhanced real-time scenario builder
        try:
            entity_names = [e.name for e in self.state.discovered_entities]
            built_scenarios = self.scenario_builder.extract_scenarios_from_text(
                user_message, 
                entities=entity_names
            )
            
            for built_scenario in built_scenarios:
                # Convert scenario builder format to our models format
                scenario = Scenario(
                    title=built_scenario.title,
                    given=" | ".join([comp.content for comp in built_scenario.given]),
                    when=" | ".join([comp.content for comp in built_scenario.when]),
                    then=" | ".join([comp.content for comp in built_scenario.then]),
                    status=ScenarioStatus.DRAFT,
                    entities=list(set([ent for comp in built_scenario.given + built_scenario.when + built_scenario.then 
                                     for ent in comp.entities]))
                )
                self.state.scenarios.append(scenario)
                print(f"✅ Enhanced scenario: {built_scenario.title} (conf: {built_scenario.confidence:.2f})")
                
                # Log completion suggestions for debugging
                if built_scenario.completion_suggestions:
                    print(f"   💡 Suggestions: {len(built_scenario.completion_suggestions)} available")
                    for suggestion in built_scenario.completion_suggestions[:2]:
                        print(f"      - {suggestion.component_type}: {suggestion.suggestion[:50]}...")
                        
                # Log validation issues
                if built_scenario.validation_issues:
                    print(f"   ⚠️  Issues: {built_scenario.validation_issues}")
                        
        except Exception as e:
            print(f"⚠️ Enhanced scenario building failed, falling back to basic: {e}")
            # Fallback to basic extraction
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
                print(f"✅ Fallback scenario: {ext_scenario.title}")
        
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
    
    def generate_visualization(self, diagram_type: str = "auto") -> Dict[str, Any]:
        """Generate visualization based on current conversation state"""
        try:
            # Convert state to format expected by visualization engine
            entities = [
                {
                    'id': entity.id,
                    'name': entity.name,
                    'type': entity.type,
                    'description': entity.description
                }
                for entity in self.state.discovered_entities
            ]
            
            scenarios = [
                {
                    'id': scenario.id,
                    'title': scenario.title,
                    'given': scenario.given,
                    'when': scenario.when,
                    'then': scenario.then,
                    'status': scenario.status,
                    'entities': scenario.entities
                }
                for scenario in self.state.scenarios
            ]
            
            constraints = [
                {
                    'id': constraint.id,
                    'name': constraint.name,
                    'category': constraint.category,
                    'requirement': constraint.requirement,
                    'priority': constraint.priority
                }
                for constraint in self.state.constraints
            ]
            
            # Determine best diagram type based on current state
            if diagram_type == "auto":
                if len(scenarios) >= 2:
                    diagram_type = "scenario_flow"
                elif len(entities) >= 3:
                    diagram_type = "entity_relationship"
                elif len(entities) >= 1 and len(scenarios) >= 1:
                    diagram_type = "architecture"
                else:
                    diagram_type = "entity_relationship"
            
            # Generate appropriate diagram
            if diagram_type == "entity_relationship":
                diagram = self.visualization_engine.generate_entity_relationship_diagram(entities)
            elif diagram_type == "scenario_flow":
                diagram = self.visualization_engine.generate_scenario_flow_diagram(scenarios, entities)
            elif diagram_type == "architecture":
                diagram = self.visualization_engine.generate_system_architecture_diagram(entities, scenarios, constraints)
            else:
                # Fallback to entity relationship
                diagram = self.visualization_engine.generate_entity_relationship_diagram(entities)
            
            # Convert to dictionary for API response
            result = self.visualization_engine.to_dict(diagram)
            
            # Add metadata about the generation
            result['generation_metadata'] = {
                'entities_count': len(entities),
                'scenarios_count': len(scenarios),
                'constraints_count': len(constraints),
                'selected_type': diagram_type,
                'conversation_phase': self.state.phase.value,
                'domain': self.detected_domain
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Visualization generation failed: {e}")
            # Return minimal fallback diagram
            return {
                'id': 'fallback',
                'title': 'System Overview',
                'type': 'entity_relationship',
                'nodes': [],
                'edges': [],
                'layout': {'type': 'force', 'spacing': 150, 'center_x': 400, 'center_y': 300},
                'metadata': {'error': str(e), 'fallback': True}
            }