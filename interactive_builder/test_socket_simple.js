#!/usr/bin/env node

const { io } = require('socket.io-client');

console.log('🧪 Testing Socket.IO connection to localhost:8000...');

const socket = io('http://localhost:8000', {
  transports: ['polling', 'websocket'],
  timeout: 10000,
});

socket.on('connect', () => {
  console.log('✅ Connected successfully!');
  console.log('   Socket ID:', socket.id);
  console.log('   Transport:', socket.io.engine.transport.name);
  
  // Test sending a message
  setTimeout(() => {
    console.log('🧪 Sending test message...');
    socket.emit('message', { content: 'Test from Node.js client' });
  }, 1000);
  
  // Disconnect after 3 seconds
  setTimeout(() => {
    console.log('🛑 Disconnecting...');
    socket.disconnect();
    process.exit(0);
  }, 3000);
});

socket.on('connect_error', (error) => {
  console.log('❌ Connection failed:', error.message);
  process.exit(1);
});

socket.on('disconnect', (reason) => {
  console.log('❌ Disconnected:', reason);
});

socket.on('message', (data) => {
  console.log('📨 Received message:', data.content);
});

// Timeout after 10 seconds
setTimeout(() => {
  console.log('⏰ Test timed out');
  process.exit(1);
}, 10000);