import { create } from 'zustand';
import { ConversationState, Message, Entity, Scenario, Constraint } from '@/types/conversation';

interface ConversationStore {
  // Messages
  messages: Message[];
  addMessage: (message: Omit<Message, 'id' | 'timestamp'>) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  
  // Conversation state
  conversationState: ConversationState;
  updateConversationState: (updates: Partial<ConversationState>) => void;
  
  // Entities
  addEntity: (entity: Omit<Entity, 'id'>) => void;
  updateEntity: (id: string, updates: Partial<Entity>) => void;
  
  // Scenarios
  addScenario: (scenario: Omit<Scenario, 'id'>) => void;
  updateScenario: (id: string, updates: Partial<Scenario>) => void;
  
  // Constraints
  addConstraint: (constraint: Omit<Constraint, 'id'>) => void;
  updateConstraint: (id: string, updates: Partial<Constraint>) => void;
  
  // WebSocket connection
  connected: boolean;
  setConnected: (connected: boolean) => void;
  
  // UI state
  activeTab: 'chat' | 'visualization' | 'preview';
  setActiveTab: (tab: 'chat' | 'visualization' | 'preview') => void;
  
  // Reset functions
  reset: () => void;
}

const initialConversationState: ConversationState = {
  phase: 'discovery',
  discovered_entities: [],
  scenarios: [],
  constraints: [],
  clarifications_needed: [],
  user_expertise_level: 'intermediate',
  progress_score: 0,
};

export const useConversationStore = create<ConversationStore>((set, get) => ({
  messages: [],
  conversationState: initialConversationState,
  connected: false,
  activeTab: 'chat',

  addMessage: (message) => {
    const newMessage: Message = {
      ...message,
      id: crypto.randomUUID(),
      timestamp: new Date(),
    };
    set((state) => ({
      messages: [...state.messages, newMessage],
    }));
  },

  updateMessage: (id, updates) => {
    set((state) => ({
      messages: state.messages.map((msg) =>
        msg.id === id ? { ...msg, ...updates } : msg
      ),
    }));
  },

  updateConversationState: (updates) => {
    set((state) => ({
      conversationState: { ...state.conversationState, ...updates },
    }));
  },

  addEntity: (entity) => {
    const newEntity: Entity = {
      ...entity,
      id: crypto.randomUUID(),
    };
    set((state) => ({
      conversationState: {
        ...state.conversationState,
        discovered_entities: [...state.conversationState.discovered_entities, newEntity],
      },
    }));
  },

  updateEntity: (id, updates) => {
    set((state) => ({
      conversationState: {
        ...state.conversationState,
        discovered_entities: state.conversationState.discovered_entities.map((entity) =>
          entity.id === id ? { ...entity, ...updates } : entity
        ),
      },
    }));
  },

  addScenario: (scenario) => {
    const newScenario: Scenario = {
      ...scenario,
      id: crypto.randomUUID(),
    };
    set((state) => ({
      conversationState: {
        ...state.conversationState,
        scenarios: [...state.conversationState.scenarios, newScenario],
      },
    }));
  },

  updateScenario: (id, updates) => {
    set((state) => ({
      conversationState: {
        ...state.conversationState,
        scenarios: state.conversationState.scenarios.map((scenario) =>
          scenario.id === id ? { ...scenario, ...updates } : scenario
        ),
      },
    }));
  },

  addConstraint: (constraint) => {
    const newConstraint: Constraint = {
      ...constraint,
      id: crypto.randomUUID(),
    };
    set((state) => ({
      conversationState: {
        ...state.conversationState,
        constraints: [...state.conversationState.constraints, newConstraint],
      },
    }));
  },

  updateConstraint: (id, updates) => {
    set((state) => ({
      conversationState: {
        ...state.conversationState,
        constraints: state.conversationState.constraints.map((constraint) =>
          constraint.id === id ? { ...constraint, ...updates } : constraint
        ),
      },
    }));
  },

  setConnected: (connected) => {
    set({ connected });
  },

  setActiveTab: (tab) => {
    set({ activeTab: tab });
  },

  reset: () => {
    set({
      messages: [],
      conversationState: initialConversationState,
      connected: false,
      activeTab: 'chat',
    });
  },
}));