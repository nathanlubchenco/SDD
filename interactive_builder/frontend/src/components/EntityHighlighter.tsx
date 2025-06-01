import { useState, useEffect, useRef } from 'react';
import { useConversationStore } from '@/store/conversationStore';
import { cn } from '@/lib/utils';

interface EntityHighlighterProps {
  text: string;
  onChange: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

const EntityHighlighter = ({ text, onChange, placeholder, disabled }: EntityHighlighterProps) => {
  const { conversationState } = useConversationStore();
  // Use conversationState for entity context
  const existingEntities = conversationState.discovered_entities || [];
  const [detectedEntities, setDetectedEntities] = useState<Array<{word: string, type: string, start: number, end: number}>>([]);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Simple client-side entity detection (matches backend patterns)
  const detectEntities = (inputText: string) => {
    const entities: Array<{word: string, type: string, start: number, end: number}> = [];
    
    const patterns = {
      actor: /\b(user|customer|admin|administrator|manager|operator|guest|visitor|member|client|developer|analyst|stakeholder|owner|reviewer|maintainer)\b/gi,
      data_entity: /\b(task|order|product|item|invoice|report|document|file|message|notification|record|entry|transaction|request|response|log|event|session|account|profile|setting|preference|configuration|data|comment|review|rating|feedback|note|attachment|history|output|input|result|analysis|pattern|suggestion|instruction|command|functionality|usage|context)\b/gi,
      system_component: /\b(database|db|server|api|service|application|app|system|platform|interface|ui|frontend|backend|endpoint|microservice|queue|cache|storage|repository|gateway|proxy|authentication|auth|authorization|security|encryption|cli|tool|analyzer|parser|processor|generator|extractor|codex|claude)\b/gi,
      business_concept: /\b(workflow|process|procedure|policy|rule|validation|permission|role|access|privilege|scope|domain|category|type|status|state|phase|stage|improvement|optimization|enhancement|recommendation|recognition|monitoring|tracking)\b/gi,
      action_concept: /\b(analyze|analyzes|analyzing|analysis|recognize|recognizes|recognizing|recognition|improve|improves|improving|improvement|update|updates|updating|upgrade|generate|generates|generating|creation|process|processes|processing|extract|extracts|extracting|extraction|run|runs|running|execute|execution)\b/gi
    };

    Object.entries(patterns).forEach(([type, pattern]) => {
      let match;
      while ((match = pattern.exec(inputText)) !== null) {
        entities.push({
          word: match[0],
          type,
          start: match.index,
          end: match.index + match[0].length
        });
      }
    });

    // Sort by position
    entities.sort((a, b) => a.start - b.start);
    
    // Remove overlapping entities (keep first)
    const nonOverlapping = [];
    let lastEnd = -1;
    for (const entity of entities) {
      if (entity.start >= lastEnd) {
        nonOverlapping.push(entity);
        lastEnd = entity.end;
      }
    }

    return nonOverlapping;
  };

  // Auto-resize textarea
  const autoResize = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  };

  useEffect(() => {
    if (text) {
      const entities = detectEntities(text);
      setDetectedEntities(entities);
    } else {
      setDetectedEntities([]);
    }
    autoResize();
  }, [text]);

  useEffect(() => {
    autoResize();
  }, []);

  const getEntityColor = (type: string) => {
    const colors = {
      actor: 'bg-blue-100 text-blue-800 border-blue-200',
      data_entity: 'bg-green-100 text-green-800 border-green-200',
      system_component: 'bg-purple-100 text-purple-800 border-purple-200',
      business_concept: 'bg-orange-100 text-orange-800 border-orange-200',
      action_concept: 'bg-pink-100 text-pink-800 border-pink-200'
    };
    return colors[type as keyof typeof colors] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  const renderHighlightedText = () => {
    if (detectedEntities.length === 0) {
      return <span className="text-muted-foreground">{text || placeholder}</span>;
    }

    const parts = [];
    let lastIndex = 0;

    detectedEntities.forEach((entity, index) => {
      // Add text before entity
      if (entity.start > lastIndex) {
        parts.push(
          <span key={`text-${index}`}>
            {text.slice(lastIndex, entity.start)}
          </span>
        );
      }

      // Add highlighted entity
      parts.push(
        <span
          key={`entity-${index}`}
          className={cn(
            "px-1 py-0.5 rounded border text-xs font-medium",
            getEntityColor(entity.type)
          )}
          title={`${entity.type.replace('_', ' ')}: ${entity.word}`}
        >
          {entity.word}
        </span>
      );

      lastIndex = entity.end;
    });

    // Add remaining text
    if (lastIndex < text.length) {
      parts.push(
        <span key="text-end">
          {text.slice(lastIndex)}
        </span>
      );
    }

    return parts;
  };

  return (
    <div className="relative">
      {/* Input field */}
      <textarea
        ref={textareaRef}
        value={text}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        disabled={disabled}
        rows={1}
        className={cn(
          "w-full px-3 py-2 rounded-md border border-input bg-background resize-none overflow-hidden",
          "focus:outline-none focus:ring-2 focus:ring-ring",
          "disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200",
          detectedEntities.length > 0 ? "text-transparent" : ""
        )}
        style={{ 
          minHeight: '44px',
          maxHeight: '200px',
          lineHeight: '1.5'
        }}
      />
      
      {/* Highlighted overlay */}
      {detectedEntities.length > 0 && (
        <div className="absolute inset-0 px-3 py-2 pointer-events-none overflow-hidden">
          <div className="text-sm leading-6 whitespace-pre-wrap break-words">
            {renderHighlightedText()}
          </div>
        </div>
      )}
      
      {/* Entity legend */}
      {detectedEntities.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1 text-xs">
          {Array.from(new Set(detectedEntities.map(e => e.type))).map(type => (
            <span
              key={type}
              className={cn(
                "px-2 py-1 rounded border",
                getEntityColor(type)
              )}
            >
              {type.replace('_', ' ')}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};

export default EntityHighlighter;