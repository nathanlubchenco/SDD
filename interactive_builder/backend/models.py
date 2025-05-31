from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"

class ConversationPhase(str, Enum):
    DISCOVERY = "discovery"
    SCENARIO_BUILDING = "scenario_building"
    CONSTRAINT_DEFINITION = "constraint_definition"
    REVIEW = "review"

class ExpertiseLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"

class ScenarioStatus(str, Enum):
    DRAFT = "draft"
    VALIDATED = "validated"
    COMPLETE = "complete"

class ConstraintCategory(str, Enum):
    PERFORMANCE = "performance"
    SECURITY = "security"
    SCALABILITY = "scalability"
    RELIABILITY = "reliability"

class ConstraintPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    content: str
    role: MessageRole
    timestamp: datetime = Field(default_factory=datetime.now)
    typing: bool = False

class Entity(BaseModel):
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    name: str
    type: str
    description: Optional[str] = None
    relationships: List[str] = Field(default_factory=list)

class Scenario(BaseModel):
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    title: str
    given: str
    when: str
    then: str
    status: ScenarioStatus = ScenarioStatus.DRAFT
    entities: List[str] = Field(default_factory=list)

class Constraint(BaseModel):
    id: str = Field(default_factory=lambda: str(datetime.now().timestamp()))
    category: ConstraintCategory
    name: str
    requirement: str
    priority: ConstraintPriority = ConstraintPriority.MEDIUM
    measurable: bool = False

class ConversationState(BaseModel):
    phase: ConversationPhase = ConversationPhase.DISCOVERY
    discovered_entities: List[Entity] = Field(default_factory=list)
    scenarios: List[Scenario] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    clarifications_needed: List[str] = Field(default_factory=list)
    user_expertise_level: ExpertiseLevel = ExpertiseLevel.INTERMEDIATE
    current_topic: Optional[str] = None
    progress_score: int = Field(default=0, ge=0, le=100)

class ConversationResponse(BaseModel):
    message: str
    state_updated: bool = False
    suggested_actions: List[str] = Field(default_factory=list)
    phase_transition: Optional[ConversationPhase] = None