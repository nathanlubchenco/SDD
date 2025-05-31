import { useState, useEffect } from 'react';
import { useConversationStore } from '@/store/conversationStore';
import { Network, GitBranch, Target, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

const VisualizationCanvas = () => {
  const { conversationState } = useConversationStore();
  const [newItems, setNewItems] = useState<Set<string>>(new Set());
  const [lastCounts, setLastCounts] = useState({ entities: 0, scenarios: 0, constraints: 0 });

  // Track new items for animation
  useEffect(() => {
    const currentCounts = {
      entities: conversationState.discovered_entities.length,
      scenarios: conversationState.scenarios.length,
      constraints: conversationState.constraints.length
    };

    const newItemIds = new Set<string>();

    // Check for new entities
    if (currentCounts.entities > lastCounts.entities) {
      const newEntities = conversationState.discovered_entities.slice(lastCounts.entities);
      newEntities.forEach(entity => newItemIds.add(`entity-${entity.id}`));
    }

    // Check for new scenarios
    if (currentCounts.scenarios > lastCounts.scenarios) {
      const newScenarios = conversationState.scenarios.slice(lastCounts.scenarios);
      newScenarios.forEach(scenario => newItemIds.add(`scenario-${scenario.id}`));
    }

    // Check for new constraints
    if (currentCounts.constraints > lastCounts.constraints) {
      const newConstraints = conversationState.constraints.slice(lastCounts.constraints);
      newConstraints.forEach(constraint => newItemIds.add(`constraint-${constraint.id}`));
    }

    if (newItemIds.size > 0) {
      setNewItems(newItemIds);
      // Clear new item highlights after animation
      setTimeout(() => setNewItems(new Set()), 2000);
    }

    setLastCounts(currentCounts);
  }, [conversationState.discovered_entities, conversationState.scenarios, conversationState.constraints]);

  const getEntityTypeColor = (type: string) => {
    const colors = {
      actor: 'bg-blue-50 border-blue-200 text-blue-800',
      data_entity: 'bg-green-50 border-green-200 text-green-800',
      system_component: 'bg-purple-50 border-purple-200 text-purple-800',
      business_concept: 'bg-orange-50 border-orange-200 text-orange-800',
      action_concept: 'bg-pink-50 border-pink-200 text-pink-800',
      entity: 'bg-gray-50 border-gray-200 text-gray-800'
    };
    return colors[type] || colors.entity;
  };

  const getEntityTypeIcon = (type: string) => {
    const icons = {
      actor: '👤',
      data_entity: '📊', 
      system_component: '⚙️',
      business_concept: '🏢',
      action_concept: '⚡',
      entity: '📦',
    };
    return icons[type] || icons.entity;
  };

  const parseEntityDescription = (description?: string) => {
    if (!description) return { main: '', relationships: [], synonyms: [], role: '' };
    
    const parts = description.split(' | ');
    const main = parts[0] || '';
    let relationships: string[] = [];
    let synonyms: string[] = [];
    let role = '';
    
    parts.forEach(part => {
      if (part.startsWith('Relationships:')) {
        relationships = part.replace('Relationships: ', '').split(', ');
      } else if (part.startsWith('Also known as:')) {
        synonyms = part.replace('Also known as: ', '').split(', ');
      } else if (part.startsWith('Role:')) {
        role = part.replace('Role: ', '');
      }
    });
    
    return { main, relationships, synonyms, role };
  };

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-3 md:p-4 border-b border-border bg-muted/50">
        <h3 className="font-medium">System Visualization</h3>
        <p className="text-xs md:text-sm text-muted-foreground">
          Live view of your system as it emerges
        </p>
      </div>

      {/* Visualization content */}
      <div className="flex-1 p-3 md:p-6 overflow-y-auto">
        {conversationState.discovered_entities.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center">
              <Network className="w-16 h-16 mx-auto mb-4 text-muted-foreground" />
              <h3 className="text-lg font-medium mb-2">System Map</h3>
              <p className="text-muted-foreground">
                As you describe your system, entities and their relationships will appear here
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Entities section */}
            <div>
              <h4 className="font-medium mb-3 flex items-center gap-2">
                <Target className="w-4 h-4" />
                Entities ({conversationState.discovered_entities.length})
              </h4>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
                {conversationState.discovered_entities.map((entity) => (
                  <div
                    key={entity.id}
                    className={cn(
                      "p-3 rounded-md border bg-card hover:shadow-sm transition-all duration-500",
                      getEntityTypeColor(entity.type),
                      newItems.has(`entity-${entity.id}`) 
                        ? "animate-pulse ring-2 ring-primary/50 scale-105" 
                        : "hover:scale-102"
                    )}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{getEntityTypeIcon(entity.type)}</span>
                          <h5 className="font-medium">{entity.name}</h5>
                        </div>
                        <p className="text-sm opacity-75 capitalize">{entity.type.replace('_', ' ')}</p>
                        
                        {entity.description && (() => {
                          const parsed = parseEntityDescription(entity.description);
                          return (
                            <div className="mt-2 space-y-1">
                              {parsed.main && (
                                <p className="text-xs opacity-60">{parsed.main}</p>
                              )}
                              {parsed.role && (
                                <p className="text-xs opacity-50">
                                  <span className="font-medium">Role:</span> {parsed.role}
                                </p>
                              )}
                              {parsed.synonyms.length > 0 && (
                                <p className="text-xs opacity-50">
                                  <span className="font-medium">Synonyms:</span> {parsed.synonyms.slice(0, 2).join(', ')}
                                </p>
                              )}
                              {parsed.relationships.length > 0 && (
                                <div className="text-xs opacity-50">
                                  <span className="font-medium">Relationships:</span>
                                  <div className="flex flex-wrap gap-1 mt-1">
                                    {parsed.relationships.slice(0, 3).map((rel, i) => (
                                      <span key={i} className="bg-black/10 px-1 py-0.5 rounded text-xs">
                                        {rel}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          );
                        })()}
                      </div>
                      {newItems.has(`entity-${entity.id}`) && (
                        <Sparkles className="w-4 h-4 text-primary animate-spin" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Scenarios section */}
            {conversationState.scenarios.length > 0 && (
              <div>
                <h4 className="font-medium mb-3 flex items-center gap-2">
                  <GitBranch className="w-4 h-4" />
                  Scenarios ({conversationState.scenarios.length})
                </h4>
                <div className="space-y-3">
                  {conversationState.scenarios.map((scenario) => (
                    <div
                      key={scenario.id}
                      className={cn(
                        "p-3 rounded-md border bg-card transition-all duration-500",
                        newItems.has(`scenario-${scenario.id}`)
                          ? "animate-pulse ring-2 ring-primary/50 scale-105 bg-primary/5"
                          : "hover:shadow-sm"
                      )}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h5 className="font-medium flex items-center gap-2">
                          {scenario.title}
                          {newItems.has(`scenario-${scenario.id}`) && (
                            <Sparkles className="w-4 h-4 text-primary animate-spin" />
                          )}
                        </h5>
                        <span className={`text-xs px-2 py-1 rounded ${
                          scenario.status === 'complete' ? 'bg-green-100 text-green-800' :
                          scenario.status === 'validated' ? 'bg-blue-100 text-blue-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {scenario.status}
                        </span>
                      </div>
                      <div className="text-sm space-y-1">
                        <p><span className="font-medium">Given:</span> {scenario.given}</p>
                        <p><span className="font-medium">When:</span> {scenario.when}</p>
                        <p><span className="font-medium">Then:</span> {scenario.then}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Future: Interactive diagram will go here */}
            <div className="mt-8 p-6 border border-dashed border-border rounded-lg">
              <div className="text-center text-muted-foreground">
                <Network className="w-8 h-8 mx-auto mb-2" />
                <p className="text-sm">Interactive system diagram coming soon...</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VisualizationCanvas;