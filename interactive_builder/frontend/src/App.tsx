import { useConversationStore } from '@/store/conversationStore';
import ChatInterface from '@/components/ChatInterface';
import VisualizationCanvas from '@/components/VisualizationCanvas';
import PreviewPanel from '@/components/PreviewPanel';
import { useWebSocket } from '@/hooks/useWebSocket';
import { cn } from '@/lib/utils';

function App() {
  const { activeTab, setActiveTab, connected } = useConversationStore();
  useWebSocket(); // Initialize WebSocket connection

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold">SDD Specification Builder</h1>
            <div className="flex items-center gap-2">
              <div
                className={cn(
                  "w-2 h-2 rounded-full",
                  connected ? "bg-green-500" : "bg-red-500"
                )}
              />
              <span className="text-sm text-muted-foreground">
                {connected ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
          
          {/* Desktop tabs */}
          <nav className="hidden md:flex items-center gap-1">
            {(['chat', 'visualization', 'preview'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={cn(
                  "px-4 py-2 rounded-md text-sm font-medium transition-colors",
                  activeTab === tab
                    ? "bg-primary text-primary-foreground"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                )}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Desktop layout - three panels */}
        <div className="hidden md:flex flex-1">
          <div className="w-2/5 border-r border-border">
            <ChatInterface />
          </div>
          <div className="w-2/5 border-r border-border">
            <VisualizationCanvas />
          </div>
          <div className="w-1/5">
            <PreviewPanel />
          </div>
        </div>

        {/* Mobile/tablet layout - single panel with tabs */}
        <div className="md:hidden flex-1 flex flex-col">
          {/* Mobile tabs */}
          <div className="border-b border-border">
            <nav className="flex">
              {(['chat', 'visualization', 'preview'] as const).map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={cn(
                    "flex-1 px-4 py-3 text-sm font-medium border-b-2 transition-colors",
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
          <div className="flex-1">
            {activeTab === 'chat' && <ChatInterface />}
            {activeTab === 'visualization' && <VisualizationCanvas />}
            {activeTab === 'preview' && <PreviewPanel />}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;