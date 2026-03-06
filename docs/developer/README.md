# AgentxploiTor Developer Documentation

Developer reference for integrating Code-Voyager, SimpleMem, and HexStrike memory systems.

## 📚 Documentation Structure

### 1. **code-voyager-api.md** (525 lines)
Complete API reference for Code Voyager brain and skill management.

**When to use**:
- Implementing brain state management
- Building skill indexing/search
- Implementing SessionStart/SessionEnd hooks
- Using unified memory for combined access

**Key APIs**:
- `VoyagerBrain`: load_brain(), save_brain(), create_empty_brain()
- `SkillIndex`: build(), search()
- `UnifiedMemory`: store(), recall(), finalize_session()
- Context injection for SessionStart

**Example import**:
```python
from voyager.brain.store import load_brain, save_brain
from voyager.retrieval.index import SkillIndex
from voyager.memory.unified_memory import UnifiedMemory
```

### 2. **simplemem-api.md** (613 lines)
Complete API reference for SimpleMem dialogue-to-facts compression system.

**When to use**:
- Recording agent actions as dialogue
- Compressing session conversations
- Querying accumulated knowledge
- Implementing semantic memory with three-layer indexing

**Key APIs**:
- `SimpleMemSystem`: add_dialogue(), finalize(), ask()
- `MemoryBuilder`: Process window-based dialogue
- `HybridRetriever`: Multi-query planning + reflection
- `AnswerGenerator`: Compress facts into answers

**Example import**:
```python
from main import SimpleMemSystem
from models.memory_entry import Dialogue, MemoryEntry
```

### 3. **hexstrike-memory-wiring.md** (792 lines)
Gap analysis and integration guide for HexStrike memory systems.

**When to use**:
- Implementing hexstrike_server.py enhancements
- Wiring SessionStart/SessionEnd hooks
- Setting up cross-agent memory sharing
- Planning memory persistence

**Key Gaps Identified**:
1. SessionStart Hook Integration ❌
2. SessionEnd Hook Integration ❌
3. Agent Memory Initialization ❌ (partial)
4. Unified Memory in Workflows ❌
5. Agent-to-Agent Knowledge Sharing ❌
6. Memory Persistence ❌
7. SimpleMem Integration ❌ (partial)

**Integration Phases**:
- Phase 1 (Essential): SessionStart/SessionEnd hooks
- Phase 2 (High): Unified memory bridge
- Phase 3 (Medium): Full SimpleMem integration
- Phase 4 (Maintenance): Memory persistence

---

## 🎯 Quick Start Guide

### For API Reference Lookups

**Looking for a specific method signature?**
→ Use `code-voyager-api.md` or `simplemem-api.md`

**Need to understand data structures?**
→ Search for "Data Structure" or "Schema" in relevant document

**Want complete examples?**
→ Look for "Complete Example" sections at end of documents

### For Integration Implementation

**Starting fresh on hexstrike_server.py?**
→ Use template in `hexstrike-memory-wiring.md` → "Integration Code Template"

**Need to add SessionStart/SessionEnd hooks?**
→ Use code in `hexstrike-memory-wiring.md` → "GAP 1" and "GAP 2"

**Implementing cross-agent memory?**
→ Use `HexStrikeKnowledgeCoordinator` in `hexstrike-memory-wiring.md` → "GAP 5"

---

## 🔗 Three-System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    UNIFIED MEMORY LAYER                  │
│   (code-voyager/memory/unified_memory.py)               │
│                                                          │
│  Combines all memory types into single interface:       │
│  - Skills & Context (Voyager)                           │
│  - Facts & Dialogue (SimpleMem)                         │
└─────────────┬─────────────────────────────────┬─────────┘
              │                                 │
    ┌─────────▼────────────┐        ┌──────────▼──────────┐
    │  CODE VOYAGER        │        │   SIMPLEMEM        │
    │  (Brain + Skills)    │        │ (Dialogue → Facts) │
    │                      │        │                    │
    │ • brain.json         │        │ • MemoryBuilder    │
    │ • brain.md           │        │ • HybridRetriever  │
    │ • skill index        │        │ • AnswerGenerator  │
    │ • curriculum         │        │ • VectorStore      │
    │                      │        │                    │
    │ Paths:              │        │ Paths:            │
    │ .claude/brain.json   │        │ .hexstrike/       │
    │ .voyager/skills/     │        │  simplemem.db     │
    └──────────┬───────────┘        └────────────┬───────┘
               │                                 │
    ┌──────────▼─────────────────────────────────▼────────┐
    │        HEXSTRIKE AGENTS (12 specialized)            │
    │  (simple_memory_agents.py)                          │
    │                                                     │
    │ Each agent has:                                    │
    │ • SimpleMemorySystem (.hexstrike/memory/)          │
    │ • Unified memory access                            │
    │ • Learn/recall methods                             │
    └────────────────────────────────────────────────────┘
```

---

## 📊 Memory Type Routing

```
Input Content
    │
    ├─→ "How to prevent SQL injection?" → SKILL
    │                                      ↓
    │                               Code Voyager Brain
    │                               (Procedural Memory)
    │
    ├─→ "Found XSS in /api endpoint" → FACT
    │                                   ↓
    │                               SimpleMem
    │                               (Episodic Memory)
    │
    ├─→ "Project uses Node.js + React" → CONTEXT
    │                                      ↓
    │                               Code Voyager Brain
    │                               (Project State)
    │
    └─→ "User asked about auth flow" → DIALOGUE
                                        ↓
                                   SimpleMem
                                   (Conversation)
```

---

## 🔄 Session Lifecycle

```
SESSION START
     │
     ├─→ SessionStart Hook
     │   ├─ Inject brain.md
     │   ├─ Inject previous plan
     │   └─ Inject repo snapshot
     │
     ├─→ Initialize Agents
     │   ├─ Create 12 enhanced agents
     │   ├─ Load memory from disk
     │   └─ Initialize unified memory
     │
AGENT EXECUTION
     │
     ├─→ Record Findings
     │   ├─ SimpleMemorySystem.store_fact()
     │   ├─ UnifiedMemory.store()
     │   └─ SimpleMem.add_dialogue()
     │
     ├─→ Recall Knowledge
     │   ├─ agent.recall_knowledge()
     │   └─ UnifiedMemory.recall()
     │
SESSION END
     │
     ├─→ SessionEnd Hook
     │   ├─ Extract findings from transcript
     │   ├─ Update brain.json
     │   └─ Save episode
     │
     ├─→ Finalize Memory
     │   ├─ SimpleMem.finalize() (compress dialogue)
     │   └─ UnifiedMemory.finalize_session()
     │
     └─→ Persist All Memory
         ├─ agent.memory files (.hexstrike/)
         ├─ brain.json updates
         └─ SimpleMem database
```

---

## 💡 Common Tasks

### Task 1: Record a Security Finding

```python
# Method 1: Direct agent memory
agent = agents["SecurityAgent"]
agent.record_fact("Found XSS in /search endpoint at line 234")

# Method 2: Unified memory (accessible to all agents)
memory.store(
    content="Found XSS in /search endpoint at line 234",
    memory_type="fact",
    speaker="SecurityAgent"
)

# Method 3: SimpleMem (for dialogue compression)
simplemem.add_dialogue("SecurityAgent", "Found XSS in /search endpoint")
```

### Task 2: Retrieve Previous Findings

```python
# Method 1: Agent-specific recall
knowledge = agent.recall_knowledge("XSS vulnerabilities")
print(knowledge["facts"])  # Previous findings

# Method 2: Unified recall (all systems)
results = memory.recall("XSS vulnerabilities", limit=10)
print(results["facts"])     # SimpleMem facts
print(results["skills"])    # Learned patterns

# Method 3: SimpleMem Q&A
answer = simplemem.ask("What XSS vulnerabilities have we found?")
```

### Task 3: Share Knowledge Across Agents

```python
# Create coordinator
coordinator = HexStrikeKnowledgeCoordinator(agents)

# Query all agents about topic
findings = coordinator.ask_all_agents("SQL injection patterns")

# Record to all agents
coordinator.record_finding_to_all(
    "SQL injection found in login form",
    metadata={"severity": "critical"}
)

# Find correlations
patterns = coordinator.correlate_findings()
```

### Task 4: Inject Context at SessionStart

```python
# In hexstrike_server.py
@app.post("/api/hooks/session-start")
async def on_session_start(request: Request):
    hook_input = await request.json()
    
    # Inject brain context
    output = inject_context(hook_input)
    
    return {
        "hookSpecificOutput": {
            "additionalContext": output["additionalContext"]
        }
    }
```

### Task 5: Update Brain at SessionEnd

```python
# In hexstrike_server.py
@app.post("/api/hooks/session-end")
async def on_session_end(request: Request):
    data = await request.json()
    
    # Update brain from findings
    brain = load_brain()
    brain["progress"]["recent_changes"] = extract_findings(data["transcript"])
    save_brain(brain)
    
    # Save episode for future reference
    save_episode(brain, data["session_id"], include_md=True)
    
    # Finalize all memory systems
    memory.finalize_session()
    simplemem.finalize()
```

---

## 📋 Implementation Checklist

### Phase 1: Essential Wiring (2-3 iterations)
- [ ] Add SessionStart hook handler to hexstrike_server.py
- [ ] Add SessionEnd hook handler to hexstrike_server.py
- [ ] Initialize all 12 enhanced agents on server startup
- [ ] Wire /api/agents/{name}/remember endpoint
- [ ] Wire /api/agents/{name}/recall endpoint
- [ ] Wire /api/agents/memory-stats endpoint
- [ ] Test SessionStart context injection
- [ ] Test SessionEnd brain updates

### Phase 2: Unified Memory (2-3 iterations)
- [ ] Initialize UnifiedMemory per session
- [ ] Wire /api/memory/store endpoint
- [ ] Wire /api/memory/recall endpoint
- [ ] Implement HexStrikeKnowledgeCoordinator
- [ ] Wire /api/memory/ask-all-agents endpoint
- [ ] Test cross-agent knowledge sharing

### Phase 3: SimpleMem Integration (2 iterations)
- [ ] Initialize SimpleMemSystem at startup
- [ ] Record agent actions as dialogues
- [ ] Wire /api/memory/finalize endpoint
- [ ] Test dialogue compression
- [ ] Wire /api/memory/ask endpoint

### Phase 4: Persistence (1 iteration)
- [ ] Add memory flush on shutdown
- [ ] Add memory preload on request
- [ ] Add monitoring/stats endpoints
- [ ] Test persistence across restarts

---

## 📈 Expected Implementation Timeline

| Phase | Component | Effort | Iterations |
|-------|-----------|--------|-----------|
| 1 | SessionStart/SessionEnd hooks | Essential | 2-3 |
| 2 | Agent initialization + endpoints | High | 2-3 |
| 3 | Unified memory bridge | High | 2-3 |
| 4 | SimpleMem integration | Medium | 2 |
| 5 | Memory persistence | Maintenance | 1 |
| **Total** | **Full Memory System** | **Medium** | **9-12** |

---

**Last Updated**: 2025-01-15
**Status**: Complete - Ready for Implementation
**Next Action**: Read Phase 1 in hexstrike-memory-wiring.md

