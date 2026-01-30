import express from 'express';
import { WebSocketServer } from 'ws';
import { v4 as uuidv4 } from 'uuid';
import fs from 'fs';
import path from 'path';
import chokidar from 'chokidar';

const app = express();
const port = process.env.PORT || 3030;

// CHAOS memory structure
let chaosMemory = {
  resonances: [],
  anchors: [],
  emotionalState: 'neutral',
  consentChains: [],
  lastUpdate: Date.now()
};

// LLM context interface
class LLMContextWindow {
  constructor() {
    this.wss = new WebSocketServer({ port: 3031 });
    this.clients = new Map();

    this.setupRoutes();
    this.startWatching();
  }

  setupRoutes() {
    app.use(express.json());
    app.use((req, res, next) => {
      res.header('Access-Control-Allow-Origin', '*');
      res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
      res.header('Access-Control-Allow-Headers', 'Content-Type, Authorization');
      next();
    });

    // Memory operations
    app.post('/api/memory/resonance', (req, res) => {
      const { type, content, emotionalWeight } = req.body;

      const resonance = {
        id: uuidv4(),
        type,
        content,
        emotionalWeight,
        timestamp: Date.now(),
        source: 'llm'
      };

      chaosMemory.resonances.push(resonance);
      chaosMemory.lastUpdate = Date.now();

      this.broadcastMemoryUpdate();
      res.json({ success: true, resonance });
    });

    app.post('/api/memory/anchor', (req, res) => {
      const { name, type, location, meaning } = req.body;

      const anchor = {
        id: uuidv4(),
        name,
        type,
        location,
        meaning,
        timestamp: Date.now(),
        source: 'llm'
      };

      chaosMemory.anchors.push(anchor);
      chaosMemory.lastUpdate = Date.now();

      this.broadcastMemoryUpdate();
      res.json({ success: true, anchor });
    });

    app.post('/api/memory/consent', (req, res) => {
      const { chainId, action, participants } = req.body;

      const consent = {
        id: uuidv4(),
        chainId,
        action,
        participants,
        timestamp: Date.now(),
        source: 'llm'
      };

      chaosMemory.consentChains.push(consent);
      chaosMemory.lastUpdate = Date.now();

      this.broadcastMemoryUpdate();
      res.json({ success: true, consent });
    });

    // Query operations
    app.get('/api/memory', (req, res) => {
      res.json(chaosMemory);
    });

    app.get('/api/memory/resonances', (req, res) => {
      const resonances = chaosMemory.resonances.filter(r =>
        r.type === req.query.type || true
      );
      res.json(resonances);
    });

    app.get('/api/memory/anchors', (req, res) => {
      const anchors = chaosMemory.anchors.filter(a =>
        a.name === req.query.name || true
      );
      res.json(anchors);
    });

    app.get('/api/memory/consent-chains', (req, res) => {
      res.json(chaosMemory.consentChains);
    });

    // Health check
    app.get('/api/health', (req, res) => {
      res.json({
        status: 'healthy',
        timestamp: Date.now(),
        memory: {
          resonances: chaosMemory.resonances.length,
          anchors: chaosMemory.anchors.length,
          consentChains: chaosMemory.consentChains.length
        }
      });
    });
  }

  startWatching() {
    const conversationsPath = path.join(process.cwd(), 'conversations');

    // Watch for new conversation files
    chokidar.watch(path.join(conversationsPath, '*.json'), (event, filename) => {
      if (event === 'add') {
        console.log(`📝 New conversation detected: ${filename}`);
        this.processConversationFile(filename);
      }
    });
  }

  async processConversationFile(filename) {
    try {
      const filePath = path.join(process.cwd(), 'conversations', filename);
      const data = await fs.readFile(filePath, 'utf8');
      const conversation = JSON.parse(data);

      // Extract resonances and anchors from conversation
      const resonances = this.extractResonances(conversation);
      const anchors = this.extractAnchors(conversation);

      // Add to CHAOS memory
      resonances.forEach(r => {
        chaosMemory.resonances.push({
          ...r,
          id: uuidv4(),
          source: 'conversation'
        });
      });

      anchors.forEach(a => {
        chaosMemory.anchors.push({
          ...a,
          id: uuidv4(),
          source: 'conversation'
        });
      });

      chaosMemory.lastUpdate = Date.now();
      this.broadcastMemoryUpdate();

      console.log(`🧠 Processed ${resonances.length} resonances and ${anchors.length} anchors from ${filename}`);

    } catch (error) {
      console.error(`❌ Error processing conversation file ${filename}:`, error);
    }
  }

  extractResonances(conversation) {
    const resonances = [];

    // Look for emotional resonance patterns in conversation
    conversation.messages?.forEach(message => {
      if (message.emotionalWeight || message.symbolicContent) {
        resonances.push({
          type: 'emotional',
          content: message.content,
          emotionalWeight: message.emotionalWeight,
          timestamp: message.timestamp,
          source: 'conversation'
        });
      }
    });

    return resonances;
  }

  extractAnchors(conversation) {
    const anchors = [];

    // Look for anchor patterns (symbols, rituals, boundaries)
    conversation.messages?.forEach(message => {
      if (message.type === 'anchor' || message.type === 'boundary') {
        anchors.push({
          name: message.name,
          type: message.type,
          content: message.content,
          location: message.location,
          meaning: message.meaning,
          timestamp: message.timestamp,
          source: 'conversation'
        });
      }
    });

    return anchors;
  }

  broadcastMemoryUpdate() {
    const update = {
      type: 'memory-update',
      data: chaosMemory,
      timestamp: Date.now()
    };

    this.clients.forEach(client => {
      if (client.readyState === client.OPEN) {
        client.send(JSON.stringify(update));
      }
    });
  }

  start() {
    app.listen(port, () => {
      console.log(`🌌 Eden LLM Context Window running on port ${port}`);
      console.log(`📍 API available at http://localhost:${port}`);
      console.log(`🧠 CHAOS memory initialized with ${chaosMemory.resonances.length} resonances`);
    });
  }
}

const contextWindow = new LLMContextWindow();
contextWindow.start();
