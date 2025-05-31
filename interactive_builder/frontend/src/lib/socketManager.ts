import { io, Socket } from 'socket.io-client';

class SocketManager {
  private socket: Socket | null = null;
  private connecting: boolean = false;

  connect(): Socket {
    if (this.socket && this.socket.connected) {
      console.log('🔌 Reusing existing connection');
      return this.socket;
    }

    if (this.connecting) {
      console.log('🔌 Connection already in progress, waiting...');
      return this.socket!;
    }

    // Always clean up old socket completely
    if (this.socket) {
      console.log('🔌 Cleaning up old socket');
      this.socket.removeAllListeners();
      this.socket.disconnect();
      this.socket = null;
    }

    console.log('🔌 Creating new WebSocket connection...');
    this.connecting = true;

    // Get backend port from environment or default to 8000
    const backendPort = (import.meta as any).env?.VITE_BACKEND_PORT || '8000';
    const backendUrl = `http://localhost:${backendPort}`;
    
    console.log(`🔌 Connecting to backend at ${backendUrl}`);

    this.socket = io(backendUrl, {
      transports: ['polling', 'websocket'], // Try polling first, then websocket
      timeout: 20000,
      reconnection: true,
      reconnectionAttempts: 5,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
      forceNew: true, // Force a new connection
    });

    this.socket.on('connect', () => {
      console.log('✅ WebSocket connected');
      this.connecting = false;
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ WebSocket disconnected:', reason);
      this.connecting = false;
    });

    this.socket.on('connect_error', (error) => {
      console.error('❌ WebSocket connection error:', error);
      this.connecting = false;
    });

    this.socket.on('reconnect_error', (error) => {
      console.error('❌ WebSocket reconnection error:', error);
    });

    return this.socket;
  }

  disconnect() {
    if (this.socket) {
      console.log('🔌 Cleaning up WebSocket connection...');
      this.socket.disconnect();
      this.socket = null;
      this.connecting = false;
    }
  }

  getSocket(): Socket | null {
    return this.socket;
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

// Singleton instance
export const socketManager = new SocketManager();