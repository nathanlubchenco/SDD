import { useConversationStore } from '@/store/conversationStore';
import { Network, GitBranch, Target } from 'lucide-react';

const VisualizationCanvas = () => {
  const { conversationState } = useConversationStore();

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-border bg-muted/50">
        <h3 className="font-medium">System Visualization</h3>
        <p className="text-sm text-muted-foreground">
          Live view of your system as it emerges
        </p>
      </div>

      {/* Visualization content */}
      <div className="flex-1 p-6">
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
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {conversationState.discovered_entities.map((entity) => (
                  <div
                    key={entity.id}
                    className="p-3 rounded-md border border-border bg-card hover:shadow-sm transition-shadow"
                  >
                    <h5 className="font-medium">{entity.name}</h5>
                    <p className="text-sm text-muted-foreground">{entity.type}</p>
                    {entity.description && (
                      <p className="text-xs text-muted-foreground mt-1">
                        {entity.description}
                      </p>
                    )}
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
                      className="p-3 rounded-md border border-border bg-card"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h5 className="font-medium">{scenario.title}</h5>
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