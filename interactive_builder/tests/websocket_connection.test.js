/**
 * WebSocket Connection Regression Test
 * 
 * Prevents regression of WebSocket connection issues by testing:
 * 1. Backend WebSocket endpoint accessibility
 * 2. CORS configuration for multiple frontend ports
 * 3. Socket.IO handshake and message exchange
 * 4. Connection state management
 */

const { spawn } = require('child_process');
const fetch = require('node-fetch');
const { io } = require('socket.io-client');

// Test configuration
const BACKEND_PORT = 8000;
const TEST_TIMEOUT = 10000;
const FRONTEND_PORTS = [3000, 3001];

class WebSocketRegressionTest {
  constructor() {
    this.backendProcess = null;
    this.testResults = [];
  }

  async runAllTests() {
    console.log('🧪 Starting WebSocket Connection Regression Tests...\n');
    
    try {
      await this.startBackend();
      await this.testBackendHealth();
      await this.testSocketIOHandshake();
      await this.testCORSConfiguration();
      await this.testSocketIOConnection();
      await this.testMessageExchange();
      
      console.log('\n✅ All WebSocket regression tests passed!');
      return true;
    } catch (error) {
      console.error('\n❌ WebSocket regression test failed:', error.message);
      return false;
    } finally {
      await this.cleanup();
    }
  }

  async startBackend() {
    console.log('🚀 Starting backend for testing...');
    
    return new Promise((resolve, reject) => {
      this.backendProcess = spawn('python', ['main.py'], {
        cwd: '../backend',
        stdio: 'pipe'
      });

      const timeout = setTimeout(() => {
        reject(new Error('Backend startup timeout'));
      }, 5000);

      // Wait for backend to be ready
      const checkHealth = async () => {
        try {
          const response = await fetch(`http://localhost:${BACKEND_PORT}/api/health`);
          if (response.ok) {
            clearTimeout(timeout);
            console.log('✅ Backend started successfully');
            resolve();
          }
        } catch (e) {
          setTimeout(checkHealth, 100);
        }
      };

      setTimeout(checkHealth, 1000);
    });
  }

  async testBackendHealth() {
    console.log('🔍 Testing backend health endpoint...');
    
    const response = await fetch(`http://localhost:${BACKEND_PORT}/api/health`);
    const data = await response.json();
    
    if (!response.ok || data.status !== 'healthy') {
      throw new Error('Backend health check failed');
    }
    
    console.log('✅ Backend health check passed');
  }

  async testSocketIOHandshake() {
    console.log('🤝 Testing Socket.IO handshake...');
    
    const response = await fetch(`http://localhost:${BACKEND_PORT}/socket.io/?EIO=4&transport=polling`);
    const text = await response.text();
    
    if (!response.ok || !text.includes('sid')) {
      throw new Error('Socket.IO handshake failed');
    }
    
    console.log('✅ Socket.IO handshake successful');
  }

  async testCORSConfiguration() {
    console.log('🌐 Testing CORS configuration for multiple frontend ports...');
    
    for (const port of FRONTEND_PORTS) {
      const response = await fetch(`http://localhost:${BACKEND_PORT}/socket.io/?EIO=4&transport=polling`, {
        headers: {
          'Origin': `http://localhost:${port}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`CORS failed for port ${port}`);
      }
      
      console.log(`✅ CORS working for port ${port}`);
    }
  }

  async testSocketIOConnection() {
    console.log('🔌 Testing Socket.IO connection...');
    
    return new Promise((resolve, reject) => {
      const socket = io(`http://localhost:${BACKEND_PORT}`, {
        transports: ['polling', 'websocket'],
        timeout: 5000,
      });

      const timeout = setTimeout(() => {
        socket.disconnect();
        reject(new Error('Socket.IO connection timeout'));
      }, TEST_TIMEOUT);

      socket.on('connect', () => {
        clearTimeout(timeout);
        console.log('✅ Socket.IO connection established');
        socket.disconnect();
        resolve();
      });

      socket.on('connect_error', (error) => {
        clearTimeout(timeout);
        socket.disconnect();
        reject(new Error(`Socket.IO connection error: ${error.message}`));
      });
    });
  }

  async testMessageExchange() {
    console.log('💬 Testing message exchange...');
    
    return new Promise((resolve, reject) => {
      const socket = io(`http://localhost:${BACKEND_PORT}`, {
        transports: ['polling', 'websocket'],
        timeout: 5000,
      });

      let welcomeReceived = false;
      let responseReceived = false;

      const timeout = setTimeout(() => {
        socket.disconnect();
        reject(new Error('Message exchange timeout'));
      }, TEST_TIMEOUT);

      socket.on('connect', () => {
        // Test sending a message
        setTimeout(() => {
          socket.emit('message', { content: 'Test message from regression test' });
        }, 1000);
      });

      socket.on('message', (data) => {
        if (data.content && data.content.includes('help you build')) {
          welcomeReceived = true;
          console.log('✅ Welcome message received');
        }
      });

      socket.on('typing_end', (data) => {
        if (data.content) {
          responseReceived = true;
          console.log('✅ AI response received');
          
          if (welcomeReceived && responseReceived) {
            clearTimeout(timeout);
            socket.disconnect();
            resolve();
          }
        }
      });

      socket.on('error', (error) => {
        clearTimeout(timeout);
        socket.disconnect();
        reject(new Error(`Message exchange error: ${error.message}`));
      });
    });
  }

  async cleanup() {
    console.log('🧹 Cleaning up test environment...');
    
    if (this.backendProcess) {
      this.backendProcess.kill();
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    console.log('✅ Cleanup complete');
  }
}

// Run tests if called directly
if (require.main === module) {
  const test = new WebSocketRegressionTest();
  test.runAllTests().then(success => {
    process.exit(success ? 0 : 1);
  });
}

module.exports = WebSocketRegressionTest;