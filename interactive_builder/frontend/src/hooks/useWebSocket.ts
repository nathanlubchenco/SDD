import { useEffect, useRef } from 'react';
import { Socket } from 'socket.io-client';
import { useConversationStore } from '@/store/conversationStore';
import { socketManager } from '@/lib/socketManager';

export const useWebSocket = () => {
  const socketRef = useRef<Socket | null>(null);
  const { addMessage, updateConversationState, setConnected, connected, setSuggestedActions } = useConversationStore();
  const listenersSetupRef = useRef(false);

  useEffect(() => {
    // Get the singleton socket
    const socket = socketManager.connect();
    socketRef.current = socket;
    
    // Check initial connection state
    console.log(`🔌 Initial socket connection state: ${socket?.connected}`);
    if (socket?.connected) {
      console.log('🔄 Socket already connected, setting state to TRUE');
      setConnected(true);
    }

    // Always clean up and re-setup listeners to ensure proper state sync
    // Remove any existing listeners to prevent duplicates
    socket.off('connect');
    socket.off('disconnect');
    socket.off('connect_error');
    socket.off('reconnect');
    socket.off('reconnect_error');
    socket.off('message');
    socket.off('typing_start');
    socket.off('typing_end');
    socket.off('conversation_state_update');
    socket.off('suggested_actions');
    socket.off('error');

    socket.on('connect', () => {
      console.log('✅ Connected to WebSocket server');
      console.log('🔄 Setting connected state to TRUE');
      setConnected(true);
    });

    socket.on('disconnect', (reason) => {
      console.log('❌ Disconnected from WebSocket:', reason);
      console.log('🔄 Setting connected state to FALSE');
      setConnected(false);
    });

    socket.on('connect_error', (error) => {
      console.error('🔥 WebSocket connection error:', error);
      setConnected(false);
    });

    socket.on('reconnect', (attemptNumber) => {
      console.log(`🔄 Reconnected after ${attemptNumber} attempts`);
      setConnected(true);
    });

    socket.on('reconnect_error', (error) => {
      console.error('🔄 Reconnection failed:', error);
    });

    socket.on('message', (data) => {
      addMessage({
        content: data.content,
        role: 'assistant',
        typing: false,
      });
    });

    socket.on('typing_start', () => {
      addMessage({
        content: '',
        role: 'assistant',
        typing: true,
      });
    });

    socket.on('typing_end', (data) => {
      // Remove any existing typing messages first
      const { messages, updateMessage } = useConversationStore.getState();
      const typingMessage = messages.find(m => m.role === 'assistant' && m.typing);
      
      if (typingMessage) {
        updateMessage(typingMessage.id, {
          content: data.content,
          typing: false,
        });
      } else {
        // Fallback: add new message if no typing message found
        addMessage({
          content: data.content,
          role: 'assistant',
          typing: false,
        });
      }
    });

    socket.on('conversation_state_update', (state) => {
      updateConversationState(state);
    });

    socket.on('suggested_actions', (actions) => {
      console.log('🎯 Suggested actions received:', actions);
      setSuggestedActions(actions || []);
    });

    socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    // Set up a periodic sync to ensure state stays in sync
    const syncInterval = setInterval(() => {
      const actualState = socket?.connected || false;
      const storeState = useConversationStore.getState().connected;
      if (actualState !== storeState) {
        console.log(`🔄 Syncing connection state: actual=${actualState}, store=${storeState}`);
        setConnected(actualState);
      }
    }, 1000);

    return () => {
      // Clean up interval
      clearInterval(syncInterval);
      
      // Clean up listeners but don't disconnect the singleton
      if (socket) {
        socket.off('connect');
        socket.off('disconnect');
        socket.off('connect_error');
        socket.off('reconnect');
        socket.off('reconnect_error');
        socket.off('message');
        socket.off('typing_start');
        socket.off('typing_end');
        socket.off('conversation_state_update');
        socket.off('suggested_actions');
        socket.off('error');
      }
      socketRef.current = null;
    };
  }, []); // Empty deps - only run once

  const sendMessage = (content: string) => {
    const socket = socketManager.getSocket();
    if (socket?.connected) {
      socket.emit('message', { content });
      addMessage({
        content,
        role: 'user',
      });
    }
  };

  const sendTyping = (isTyping: boolean) => {
    const socket = socketManager.getSocket();
    if (socket?.connected) {
      socket.emit(isTyping ? 'typing_start' : 'typing_end');
    }
  };

  return {
    sendMessage,
    sendTyping,
    connected,
  };
};