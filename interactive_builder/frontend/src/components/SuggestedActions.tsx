import { useState } from 'react';
import { useConversationStore } from '@/store/conversationStore';
import { cn } from '@/lib/utils';
import { MessageCircle, HelpCircle, Target, AlertCircle, Settings, Link, ArrowRight } from 'lucide-react';

interface SuggestedAction {
  text: string;
  type: string;
  priority: number;
  reasoning: string;
}

interface SuggestedActionsProps {
  onActionClick: (actionText: string) => void;
}

const SuggestedActions = ({ onActionClick }: SuggestedActionsProps) => {
  const { suggestedActions } = useConversationStore();
  const [expandedAction, setExpandedAction] = useState<number | null>(null);

  if (!suggestedActions || suggestedActions.length === 0) {
    return null;
  }

  const getActionIcon = (type: string) => {
    const icons = {
      clarification: HelpCircle,
      exploration: Target,
      validation: MessageCircle,
      edge_case: AlertCircle,
      constraint: Settings,
      relationship: Link,
      scenario: ArrowRight,
    };
    const IconComponent = icons[type as keyof typeof icons] || MessageCircle;
    return <IconComponent className="w-4 h-4" />;
  };

  const getActionColor = (type: string, priority: number) => {
    const baseColors = {
      clarification: 'border-blue-200 bg-blue-50 text-blue-800',
      exploration: 'border-green-200 bg-green-50 text-green-800',
      validation: 'border-purple-200 bg-purple-50 text-purple-800',
      edge_case: 'border-orange-200 bg-orange-50 text-orange-800',
      constraint: 'border-red-200 bg-red-50 text-red-800',
      relationship: 'border-indigo-200 bg-indigo-50 text-indigo-800',
      scenario: 'border-teal-200 bg-teal-50 text-teal-800',
    };

    let color = baseColors[type as keyof typeof baseColors] || baseColors.clarification;
    
    // Add priority-based styling
    if (priority > 0.8) {
      color += ' ring-2 ring-current/20';
    }

    return color;
  };

  const getPriorityLabel = (priority: number) => {
    if (priority > 0.8) return 'High Priority';
    if (priority > 0.6) return 'Medium Priority';
    return 'Low Priority';
  };

  const formatActionType = (type: string) => {
    return type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="border-t border-border bg-muted/30 p-3">
      <div className="mb-2">
        <h4 className="text-sm font-medium text-foreground flex items-center gap-2">
          <Target className="w-4 h-4" />
          Suggested Questions ({suggestedActions.length})
        </h4>
        <p className="text-xs text-muted-foreground">
          Click any question to explore that topic further
        </p>
      </div>

      <div className="space-y-2">
        {suggestedActions.map((action, index) => (
          <div key={index} className="space-y-1">
            <button
              onClick={() => onActionClick(action.text)}
              className={cn(
                "w-full text-left p-3 rounded-lg border transition-all duration-200",
                "hover:shadow-sm hover:scale-[1.02] active:scale-[0.98]",
                getActionColor(action.type, action.priority),
                "group"
              )}
            >
              <div className="flex items-start gap-3">
                <div className="flex-shrink-0 mt-0.5">
                  {getActionIcon(action.type)}
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 mb-1">
                    <span className="text-xs font-medium uppercase tracking-wide opacity-75">
                      {formatActionType(action.type)}
                    </span>
                    <div className="flex items-center gap-2">
                      {action.priority > 0.8 && (
                        <span className="text-xs bg-current/10 px-1.5 py-0.5 rounded">
                          High Priority
                        </span>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setExpandedAction(expandedAction === index ? null : index);
                        }}
                        className="text-xs opacity-60 hover:opacity-100 transition-opacity"
                      >
                        {expandedAction === index ? 'Less' : 'Why?'}
                      </button>
                    </div>
                  </div>
                  
                  <p className="text-sm font-medium leading-relaxed group-hover:text-current/90 transition-colors">
                    {action.text}
                  </p>
                  
                  {action.priority > 0.7 && (
                    <div className="flex items-center gap-1 mt-2 text-xs opacity-60">
                      <ArrowRight className="w-3 h-3" />
                      <span>Click to explore this topic</span>
                    </div>
                  )}
                </div>
              </div>
            </button>

            {expandedAction === index && action.reasoning && (
              <div className="ml-10 p-2 bg-background/60 rounded text-xs text-muted-foreground border border-border/50">
                <p className="font-medium mb-1">Why this question matters:</p>
                <p>{action.reasoning}</p>
              </div>
            )}
          </div>
        ))}
      </div>

      {suggestedActions.length > 3 && (
        <div className="mt-3 pt-2 border-t border-border/50">
          <p className="text-xs text-muted-foreground text-center">
            Answer any question to get more targeted suggestions
          </p>
        </div>
      )}
    </div>
  );
};

export default SuggestedActions;