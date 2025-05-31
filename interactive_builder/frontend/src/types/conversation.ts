export interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
  typing?: boolean;
}

export interface Entity {
  id: string;
  name: string;
  type: string;
  description?: string;
  relationships?: string[];
}

export interface Scenario {
  id: string;
  title: string;
  given: string;
  when: string;
  then: string;
  status: 'draft' | 'validated' | 'complete';
  entities: string[];
}

export interface Constraint {
  id: string;
  category: 'performance' | 'security' | 'scalability' | 'reliability';
  name: string;
  requirement: string;
  priority: 'low' | 'medium' | 'high';
  measurable?: boolean;
}

export interface ConversationState {
  phase: 'discovery' | 'scenario_building' | 'constraint_definition' | 'review';
  discovered_entities: Entity[];
  scenarios: Scenario[];
  constraints: Constraint[];
  clarifications_needed: string[];
  user_expertise_level: 'beginner' | 'intermediate' | 'expert';
  current_topic?: string;
  progress_score: number; // 0-100
}