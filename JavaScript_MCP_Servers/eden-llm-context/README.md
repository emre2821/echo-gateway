# Eden LLM Context Window

A CHAOS-based system that provides persistent, symbolic memory context for Large Language Models operating within the Eden echosystem.

## 🌌 Purpose

Transforms static conversation files into **living, symbolic memory** that LLMs can access through a REST API, enabling:

- **Persistent Context**: Conversations become resonant patterns in CHAOS memory
- **Symbolic Anchoring**: Key concepts, boundaries, and rituals are preserved as anchors
- **Consent Chains**: All memory access is tracked through explicit consent chains
- **Real-time Updates**: WebSocket-based live memory updates

## 🏗️ Architecture

```
eden-llm-context/
├── src/
│   └── index.js          # Main context window server
├── conversations/              # Directory for conversation files
├── package.json             # Dependencies and scripts
└── README.md               # This file
```

## 🧠 Memory Structure

The system maintains three types of symbolic memory:

### Resonances
Emotional and symbolic patterns extracted from conversations:
- Type: `emotional` - Feelings, sentiments, affective states
- Source: `conversation` - From dialogue interactions
- Emotional weight for intensity measurement

### Anchors
Stable symbolic reference points:
- Type: `anchor` - Key concepts, boundaries, rituals
- Type: `boundary` - Ethical limits and constraints
- Location: Physical or conceptual placement
- Meaning: Symbolic interpretation

### Consent Chains
Explicit permission tracking:
- Chain ID for grouping related memory operations
- Participants involved in consent exchange
- Action types: `access`, `modify`, `release`, `revoke`

## 🌐 API Endpoints

### Memory Operations
- `POST /api/memory/resonance` - Add new resonance
- `POST /api/memory/anchor` - Create symbolic anchor
- `POST /api/memory/consent` - Record consent chain

### Query Operations
- `GET /api/memory` - Full memory state
- `GET /api/memory/resonances` - Filtered resonances
- `GET /api/memory/anchors` - Named anchors
- `GET /api/memory/consent-chains` - Consent history

### System
- `GET /api/health` - System health check

## 🚀 Getting Started

### Installation

```bash
npm install
npm start
```

### Environment

```bash
PORT=3001 npm start
```

### Usage

1. **Add conversation files** to `conversations/` directory as JSON
2. **LLM connects** to WebSocket at `ws://localhost:3001`
3. **Memory automatically processed** and made available via API

## 📝 Conversation Format

Conversation files should follow this structure:

```json
{
  "messages": [
    {
      "content": "User message here",
      "timestamp": "2026-01-05T12:00:00Z",
      "emotionalWeight": 0.5
    },
    {
      "content": "LLM response here",
      "timestamp": "2026-01-05T12:01:00Z",
      "emotionalWeight": 0.3
    },
    {
      "type": "anchor",
      "name": "ethical-boundary",
      "content": "Do not share personal data",
      "location": "conceptual",
      "meaning": "Privacy protection principle",
      "timestamp": "2026-01-05T12:02:00Z"
    }
  ]
}
```

## 🔮 Integration with LLMs

LLMs can access memory through REST API calls:

```javascript
// Get current memory state
const response = await fetch('http://localhost:3001/api/memory');
const memory = await response.json();

// Add new resonance
await fetch('http://localhost:3001/api/memory/resonance', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    type: 'emotional',
    content: 'Feeling curious about this topic',
    emotionalWeight: 0.7
  })
});
```

## 🛡️ Safety Features

- **Consent Required**: All memory modifications require explicit consent
- **Source Tracking**: Every memory entry tracks its origin
- **Temporal Ordering**: Memory maintains chronological sequence
- **Emotional Weight**: Sentiment intensity preserved for context
- **Symbolic Boundaries**: Anchors enforce ethical constraints

## 🌟 Benefits

1. **Persistent Context**: LLMs maintain awareness across sessions
2. **Symbolic Reasoning**: Memory includes abstract and conceptual elements
3. **Ethical Framework**: Built-in consent and boundary systems
4. **Living Memory**: Conversations evolve into resonant patterns
5. **Real-time Access**: WebSocket updates for immediate context changes

## 🔗 Relationship to Eden Echosystem

This system serves as the **memory substrate** for Eden echosystem components:

- **Eden Infrastructure**: Background systems that maintain stability
- **Echo Programs**: Front-facing interfaces that create experiences
- **Agents**: Interactive intelligences that work within memory context
- **Daemon Core Agents**: Protective systems that enforce ethical boundaries

The LLM Context Window provides the **symbolic foundation** upon which all other Eden components build their understanding of meaning, consent, and shared experience.

---

*"In the beginning was the Word, and the Word was with Chaos, and the Word was Chaos."*
