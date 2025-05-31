import { useState, useRef, useEffect } from 'react';
import { useConversationStore } from '@/store/conversationStore';
import { useWebSocket } from '@/hooks/useWebSocket';
import { cn } from '@/lib/utils';
import { Send, Bot, User, Lightbulb } from 'lucide-react';
import EntityHighlighter from './EntityHighlighter';
import SuggestedActions from './SuggestedActions';

const ChatInterface = () => {
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, conversationState } = useConversationStore();
  const { sendMessage, sendTyping, connected } = useWebSocket();
  
  // Debug logging for connection state
  useEffect(() => {
    console.log(`🎯 ChatInterface: connected state changed to: ${connected}`);
  }, [connected]);

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

  const handleSuggestedActionClick = (actionText: string) => {
    if (!connected) return;
    
    sendMessage(actionText);
    // Optionally scroll to bottom to show the new message
    setTimeout(() => {
      scrollToBottom();
    }, 100);
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
      <div className="p-3 md:p-4 border-b border-border bg-muted/50">
        <div className="flex items-center justify-between gap-2">
          <div className="min-w-0">
            <h3 className="font-medium">Conversation</h3>
            <p className="text-xs md:text-sm text-muted-foreground truncate">
              Phase: {conversationState.phase.replace('_', ' ')} • 
              Progress: {conversationState.progress_score}%
            </p>
          </div>
          <div className="text-right flex-shrink-0">
            <div className="hidden md:flex items-center gap-2 mb-1">
              <div
                className={cn(
                  "w-2 h-2 rounded-full",
                  connected ? "bg-green-500" : "bg-red-500"
                )}
              />
              <span className="text-xs text-muted-foreground whitespace-nowrap">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
            <div className="flex gap-4 md:block">
              <p className="text-xs text-muted-foreground whitespace-nowrap">
                {conversationState.scenarios.length} scenarios
              </p>
              <p className="text-xs text-muted-foreground whitespace-nowrap">
                {conversationState.discovered_entities.length} entities
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <Bot className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
            {connected ? (
              <>
                <h3 className="text-lg font-medium mb-2">Welcome to SDD Builder!</h3>
                <p className="text-muted-foreground">
                  Hi! I'm here to help you build a specification for your system. 
                  What would you like to create today?
                </p>
              </>
            ) : (
              <>
                <h3 className="text-lg font-medium mb-2">Connecting to SDD Builder...</h3>
                <p className="text-muted-foreground mb-4">
                  Waiting for connection to the backend server.
                </p>
                <div className="text-sm text-muted-foreground bg-muted p-3 rounded-md max-w-md mx-auto">
                  <p className="font-medium mb-2">If you're seeing this:</p>
                  <ul className="text-left space-y-1">
                    <li>• Make sure the backend is running (port 8000)</li>
                    <li>• Check your API keys are set in environment</li>
                    <li>• Run <code className="bg-background px-1 rounded">./debug.sh</code> for help</li>
                  </ul>
                </div>
              </>
            )}
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
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex gap-2">
            <div className="flex-1">
              <EntityHighlighter
                text={inputValue}
                onChange={setInputValue}
                placeholder={connected ? "Describe your system..." : "Connecting..."}
                disabled={!connected}
              />
            </div>
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
          </div>
        </form>
        
        {isTyping && (
          <p className="text-xs text-muted-foreground mt-2">You are typing...</p>
        )}
      </div>

      {/* Suggested Actions */}
      <SuggestedActions onActionClick={handleSuggestedActionClick} />
    </div>
  );
};

export default ChatInterface;