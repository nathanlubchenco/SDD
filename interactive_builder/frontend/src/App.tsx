import { useEffect } from 'react';
import { useConversationStore } from '@/store/conversationStore';
import ChatInterface from '@/components/ChatInterface';
import VisualizationCanvas from '@/components/VisualizationCanvas';
import PreviewPanel from '@/components/PreviewPanel';
import { ScenarioBuilder } from '@/components/ScenarioBuilder';
import { useWebSocket } from '@/hooks/useWebSocket';
import { socketManager } from '@/lib/socketManager';
import { cn } from '@/lib/utils';

function App() {
  const { activeTab, setActiveTab, connected, conversationState } = useConversationStore();
  useWebSocket(); // Initialize WebSocket connection
  
  // Show scenarios tab when in scenario building phase or when scenarios exist
  const showScenariosTab = conversationState.phase === 'scenario_building' || 
                          conversationState.scenarios.length > 0;

  // Cleanup on app unmount
  useEffect(() => {
    return () => {
      socketManager.disconnect();
    };
  }, []);

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b border-border px-4 lg:px-6 py-4">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 md:gap-4 min-w-0">
            <h1 className="text-lg lg:text-xl font-semibold truncate">SDD Specification Builder</h1>
            <div className="hidden sm:flex items-center gap-2">
              <div
                className={cn(
                  "w-2 h-2 rounded-full flex-shrink-0",
                  connected ? "bg-green-500" : "bg-red-500"
                )}
              />
              <span className="text-sm text-muted-foreground whitespace-nowrap">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          
          {/* Desktop tabs - only show on larger screens where we have multiple panels */}
          <nav className="hidden lg:flex items-center gap-1">
            {(['chat', 'visualization', 'preview', ...(showScenariosTab ? ['scenarios'] : [])] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "px-3 lg:px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap",
                  activeTab === tab
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>

          {/* Connection indicator for mobile */}
          <div className="sm:hidden flex items-center">
            <div
              className={cn(
                "w-3 h-3 rounded-full",
                connected ? "bg-green-500" : "bg-red-500"
              )}
            />
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Large desktop layout - three panels */}
        <div className="hidden xl:flex flex-1 min-w-0">
          <div className="w-2/5 min-w-0 border-r border-border">
            <ChatInterface />
          </div>
          <div className="w-2/5 min-w-0 border-r border-border">
            <VisualizationCanvas />
          </div>
          <div className="w-1/5 min-w-0">
            <PreviewPanel />
          </div>
        </div>

        {/* Medium desktop layout - two panels (chat + preview) */}
        <div className="hidden lg:flex xl:hidden flex-1 min-w-0">
          <div className="w-3/5 min-w-0 border-r border-border">
            <ChatInterface />
          </div>
          <div className="w-2/5 min-w-0">
            {activeTab === 'visualization' && <VisualizationCanvas />}
            {activeTab === 'scenarios' && <ScenarioBuilder isVisible={true} />}
            {(activeTab === 'preview' || (!['visualization', 'scenarios'].includes(activeTab))) && <PreviewPanel />}
          </div>
        </div>

        {/* Tablet layout - two panels side by side */}
        <div className="hidden md:flex lg:hidden flex-1 min-w-0">
          <div className="w-3/5 min-w-0 border-r border-border">
            <ChatInterface />
          </div>
          <div className="w-2/5 min-w-0">
            {activeTab === 'visualization' && <VisualizationCanvas />}
            {activeTab === 'scenarios' && <ScenarioBuilder isVisible={true} />}
            {(activeTab === 'preview' || (!['visualization', 'scenarios'].includes(activeTab))) && <PreviewPanel />}
          </div>
        </div>

        {/* Mobile layout - single panel with tabs */}
        <div className="md:hidden flex-1 flex flex-col min-w-0">
          {/* Mobile tabs */}
          <div className="border-b border-border bg-background">
            <nav className="flex overflow-x-auto">
              {(['chat', 'visualization', 'preview', ...(showScenariosTab ? ['scenarios'] : [])] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={cn(
                    "flex-shrink-0 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                    activeTab === tab
                      ? "border-primary text-primary"
                      : "border-transparent text-muted-foreground hover:text-foreground"
                  )}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </nav>
          </div>

          {/* Active panel */}
          <div className="flex-1 min-w-0 overflow-hidden">
            {activeTab === 'chat' && <ChatInterface />}
            {activeTab === 'visualization' && <VisualizationCanvas />}
            {activeTab === 'scenarios' && <ScenarioBuilder isVisible={true} />}
            {activeTab === 'preview' && <PreviewPanel />}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;