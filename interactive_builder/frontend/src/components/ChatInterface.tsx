import { useState, useRef, useEffect } from 'react';
import { useConversationStore } from '@/store/conversationStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { cn } from '@/lib/utils';
import { Send, Bot, User } from 'lucide-react';

const ChatInterface = () => {
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, conversationState } = useConversationStore();
  const { sendMessage, sendTyping, connected } = useWebSocket();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim() || !connected) return;

    sendMessage(inputValue.trim());
    setInputValue('');
    setIsTyping(false);
    sendTyping(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInputValue(value);

    // Send typing indicators
    if (value && !isTyping) {
      setIsTyping(true);
      sendTyping(true);
    } else if (!value && isTyping) {
      setIsTyping(false);
      sendTyping(false);
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="h-full flex flex-col">
      {/* Chat header with context */}
      <div className="p-4 border-b border-border bg-muted/50">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-medium">Conversation</h3>
            <p className="text-sm text-muted-foreground">
              Phase: {conversationState.phase.replace('_', ' ')} • 
              Progress: {conversationState.progress_score}%
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted-foreground">
              {conversationState.scenarios.length} scenarios
            </p>
            <p className="text-xs text-muted-foreground">
              {conversationState.discovered_entities.length} entities
            </p>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <Bot className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            <h3 className="text-lg font-medium mb-2">Welcome to SDD Builder!</h3>
            <p className="text-muted-foreground">
              Hi! I'm here to help you build a specification for your system. 
              What would you like to create today?
            </p>
          </div>
        )}

        {messages.map((message) => (
          <div
            key={message.id}
            className={cn(
              "flex gap-3",
              message.role === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                  <Bot className="w-4 h-4 text-primary-foreground" />
                </div>
              </div>
            )}

            <div
              className={cn(
                "max-w-[80%] rounded-lg px-4 py-2",
                message.role === 'user'
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              )}
            >
              {message.typing ? (
                <div className="flex items-center gap-1">
                  <div className="flex gap-1">
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                    <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                  </div>
                  <span className="text-xs text-muted-foreground ml-2">AI is typing...</span>
                </div>
              ) : (
                <>
                  <p className="whitespace-pre-wrap">{message.content}</p>
                  <p className={cn(
                    "text-xs mt-1 opacity-70",
                    message.role === 'user' ? 'text-primary-foreground' : 'text-muted-foreground'
                  )}>
                    {formatTime(message.timestamp)}
                  </p>
                </>
              )}
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center">
                  <User className="w-4 h-4 text-muted-foreground" />
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <div className="p-4 border-t border-border">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={inputValue}
            onChange={handleInputChange}
            placeholder={connected ? "Type your message..." : "Connecting..."}
            disabled={!connected}
            className={cn(
              "flex-1 px-3 py-2 rounded-md border border-input bg-background",
              "focus:outline-none focus:ring-2 focus:ring-ring",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || !connected}
            className={cn(
              "px-4 py-2 bg-primary text-primary-foreground rounded-md",
              "hover:bg-primary/90 transition-colors",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "flex items-center justify-center"
            )}
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        
        {isTyping && (
          <p className="text-xs text-muted-foreground mt-2">You are typing...</p>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;