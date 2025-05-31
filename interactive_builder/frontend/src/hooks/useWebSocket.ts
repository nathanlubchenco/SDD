import { useEffect, useRef } from 'react';
import { io, Socket } from 'socket.io-client';
import { useConversationStore } from '@/store/conversationStore';

export const useWebSocket = () => {
  const socketRef = useRef<Socket | null>(null);
  const { addMessage, updateConversationState, setConnected } = useConversationStore();

  useEffect(() => {
    // Connect to WebSocket
    socketRef.current = io('ws://localhost:8000', {
      transports: ['websocket'],
    });

    const socket = socketRef.current;

    socket.on('connect', () => {
      console.log('Connected to WebSocket');
      setConnected(true);
    });

    socket.on('disconnect', () => {
      console.log('Disconnected from WebSocket');
      setConnected(false);
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
      // Update the typing message with actual content
      addMessage({
        content: data.content,
        role: 'assistant',
        typing: false,
      });
    });

    socket.on('conversation_state_update', (state) => {
      updateConversationState(state);
    });

    socket.on('error', (error) => {
      console.error('WebSocket error:', error);
    });

    return () => {
      socket.disconnect();
    };
  }, [addMessage, updateConversationState, setConnected]);

  const sendMessage = (content: string) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('message', { content });
      addMessage({
        content,
        role: 'user',
      });
    }
  };

  const sendTyping = (isTyping: boolean) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(isTyping ? 'typing_start' : 'typing_end');
    }
  };

  return {
    sendMessage,
    sendTyping,
    connected: useConversationStore((state) => state.connected),
  };
};