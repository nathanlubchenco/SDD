import { create } from 'zustand';
import { Entity, Scenario, Constraint } from '@/types/conversation';

interface SpecificationStore {
  // Entities
  entities: Entity[];
  addEntity: (entity: Omit<Entity, 'id'>) => void;
  updateEntity: (id: string, updates: Partial<Entity>) => void;
  removeEntity: (id: string) => void;
  
  // Scenarios
  scenarios: Scenario[];
  addScenario: (scenario: Omit<Scenario, 'id'>) => void;
  updateScenario: (id: string, updates: Partial<Scenario>) => void;
  removeScenario: (id: string) => void;
  
  // Constraints
  constraints: Constraint[];
  addConstraint: (constraint: Omit<Constraint, 'id'>) => void;
  updateConstraint: (id: string, updates: Partial<Constraint>) => void;
  removeConstraint: (id: string) => void;
  
  // Utility
  reset: () => void;
  
  // Sync with conversation store
  syncFromConversationState: (entities: Entity[], scenarios: Scenario[], constraints: Constraint[]) => void;
}

export const useSpecificationStore = create<SpecificationStore>((set, get) => ({
  entities: [],
  scenarios: [],
  constraints: [],
  
  addEntity: (entity) => {
    const newEntity: Entity = {
      ...entity,
      id: crypto.randomUUID(),
    };
    set((state) => ({
      entities: [...state.entities, newEntity]
    }));
  },
  
  updateEntity: (id, updates) => {
    set((state) => ({
      entities: state.entities.map(entity => 
        entity.id === id ? { ...entity, ...updates } : entity
      )
    }));
  },
  
  removeEntity: (id) => {
    set((state) => ({
      entities: state.entities.filter(entity => entity.id !== id)
    }));
  },
  
  addScenario: (scenario) => {
    const newScenario: Scenario = {
      ...scenario,
      id: crypto.randomUUID(),
    };
    set((state) => ({
      scenarios: [...state.scenarios, newScenario]
    }));
  },
  
  updateScenario: (id, updates) => {
    set((state) => ({
      scenarios: state.scenarios.map(scenario => 
        scenario.id === id ? { ...scenario, ...updates } : scenario
      )
    }));
  },
  
  removeScenario: (id) => {
    set((state) => ({
      scenarios: state.scenarios.filter(scenario => scenario.id !== id)
    }));
  },
  
  addConstraint: (constraint) => {
    const newConstraint: Constraint = {
      ...constraint,
      id: crypto.randomUUID(),
    };
    set((state) => ({
      constraints: [...state.constraints, newConstraint]
    }));
  },
  
  updateConstraint: (id, updates) => {
    set((state) => ({
      constraints: state.constraints.map(constraint => 
        constraint.id === id ? { ...constraint, ...updates } : constraint
      )
    }));
  },
  
  removeConstraint: (id) => {
    set((state) => ({
      constraints: state.constraints.filter(constraint => constraint.id !== id)
    }));
  },
  
  reset: () => {
    set({
      entities: [],
      scenarios: [],
      constraints: []
    });
  },
  
  syncFromConversationState: (entities, scenarios, constraints) => {
    set({
      entities,
      scenarios,
      constraints
    });
  }
}));