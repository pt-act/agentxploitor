# HexStrike Memory Wiring: Gap Analysis

## Current State: What's Already Wired

### Simple Memory System (simple_memory_agents.py)

**Status**: ✅ Complete implementation, ready to integrate

This lightweight system provides persistent memory without external dependencies.

#### Already Implemented Agents

```python
# 1. Base class - all agents inherit from this
class MemoryEnhancedHexStrikeAgent:
    def __init__(self, agent_name: str)
        self.memory = SimpleMemorySystem(agent_name)
    
    # Core methods (all implemented)
    def learn_skill(skill_description: str, context: str = "") -> bool
    def record_fact(fact_description: str, metadata: Dict = None) -> bool
    def update_context(context_description: str) -> bool
    def recall_knowledge(query: str) -> Dict[skills, facts, context]
    def get_summary() -> Dict[stats]

# 2. Specialized implementations
EnhancedIntelligentDecisionEngine
    - analyze_target_with_memory(target) -> Dict
    - select_tools_with_memory(target, scan_type) -> List[str]

EnhancedBugBountyWorkflowManager
    - execute_bug_bounty_scan(target) -> Dict

EnhancedCVEIntelligenceManager
    - analyze_cve_with_memory(cve_id) -> Dict

EnhancedAIExploitGenerator
    - generate_exploit_with_memory(vulnerability_type, target) -> Dict

EnhancedVulnerabilityCorrelator
    - correlate_vulnerabilities_with_memory(vulnerabilities) -> Dict
```

#### Memory Storage Structure

```
.hexstrike/memory/
├── [AgentName]/
│   ├── skills.json          # Learned techniques and patterns
│   ├── facts.json           # Findings and discoveries
│   └── context.json         # Working context and state
```

Each file is a JSON array of entries:
```json
[
    {
        "id": 1,
        "description": "XSS vulnerability found in /search endpoint",
        "timestamp": "2025-01-15T14:30:00",
        "agent": "SecurityAgent",
        "metadata": { "severity": "medium" }
    }
]
```

### HexStrike Memory Integration (hexstrike_memory_integration.py)

**Status**: ✅ Integration pattern defined, demo provided

Demonstrates how to wrap existing HexStrike agents with memory.

#### Enhanced Endpoints Defined

```python
# 1. Enhanced target analysis
def memory_enhanced_analyze_target(target: str, analysis_type: str = "comprehensive")
    # Uses decision_engine.analyze_target_with_memory()
    # Returns: analysis with memory_enhanced flag + previous_scans count

# 2. Enhanced smart scan
def memory_enhanced_smart_scan(target: str, max_tools: int = 10)
    # Uses decision_engine.select_tools_with_memory()
    # Uses bug_bounty_manager.execute_bug_bounty_scan()
    # Returns: tools + vulnerabilities + memory_enhanced flag

# 3. New endpoint: Memory stats
def get_agent_memory_stats()
    # Returns: stats for all agents (memory_enabled agents, total memories)
```

#### Factory Function

```python
def create_all_enhanced_agents() -> Dict:
    # Creates all 12 HexStrike agents with memory
    agents = {
        "IntelligentDecisionEngine": EnhancedIntelligentDecisionEngine(),
        "BugBountyWorkflowManager": EnhancedBugBountyWorkflowManager(),
        "CVEIntelligenceManager": EnhancedCVEIntelligenceManager(),
        "AIExploitGenerator": EnhancedAIExploitGenerator(),
        "VulnerabilityCorrelator": EnhancedVulnerabilityCorrelator(),
        "CTFWorkflowManager": MemoryEnhancedHexStrikeAgent("CTFWorkflowManager"),
        "TechnologyDetector": MemoryEnhancedHexStrikeAgent("TechnologyDetector"),
        "RateLimitDetector": MemoryEnhancedHexStrikeAgent("RateLimitDetector"),
        "FailureRecoverySystem": MemoryEnhancedHexStrikeAgent("FailureRecoverySystem"),
        "PerformanceMonitor": MemoryEnhancedHexStrikeAgent("PerformanceMonitor"),
        "ParameterOptimizer": MemoryEnhancedHexStrikeAgent("ParameterOptimizer"),
        "GracefulDegradation": MemoryEnhancedHexStrikeAgent("GracefulDegradation")
    }
    return agents
```

### UnifiedMemory Bridge (code-voyager unified_memory.py)

**Status**: ✅ Bridge implementation complete

Combines Code Voyager + SimpleMem into single interface.

#### UnifiedMemory Class

```python
class UnifiedMemory:
    def __init__(project_dir, agent_name, enable_simplemem=True):
        self.voyager_brain = SimpleVoyagerBrain()  # Skills + Context
        self.simplemem = SimpleMemSystem()          # Facts + Dialogue
        
    def store(content, memory_type=None, ...) -> bool
        # Routes to Voyager (skill/context) or SimpleMem (fact/dialogue)
        
    def recall(query, memory_types=None, limit=10) -> Dict
        # Queries both systems, returns merged results
        
    def finalize_session()
        # Compresses dialogue into facts
```

#### Memory Type Routing

```python
MemoryType.SKILL   → Stored in Voyager Brain
MemoryType.CONTEXT → Stored in Voyager Brain
MemoryType.FACT    → Stored in SimpleMem
MemoryType.DIALOGUE → Stored in SimpleMem
```

---

## Critical Gaps: What's Missing

### GAP 1: SessionStart Hook Integration ❌ MISSING

**Current State**: Code Voyager has `inject_from_stdin()` but HexStrike doesn't call it.

**Required Implementation**:

```python
# In hexstrike_server.py - ADD THIS

from voyager.scripts.brain.inject import inject_from_stdin
import json

@app.post("/api/hooks/session-start")
def on_session_start(request: Request):
    """
    SessionStart hook from Claude
    
    Receives: {cwd, session_id, ...}
    Returns: {additionalContext: "...brain + snapshot..."}
    """
    hook_input = await request.json()
    
    # Inject brain context
    output = inject_from_stdin_direct(hook_input)
    
    # Return to Claude
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": output.get("additionalContext")
        }
    }

def inject_from_stdin_direct(hook_input: dict) -> dict:
    """Direct injection without stdin parsing"""
    from voyager.brain.store import load_brain
    from voyager.repo.snapshot import snapshot_to_json
    from voyager.scripts.brain.inject import build_context
    
    cwd = hook_input.get("cwd", str(Path.cwd()))
    session_id = hook_input.get("session_id", "")
    
    # Load components
    brain_md = read_file(".claude/brain.md")
    brain = load_brain()
    snapshot = snapshot_to_json(cwd)
    
    # Build context
    context = build_context(brain_md, brain, snapshot)
    
    return {
        "additionalContext": context
    }
```

**Why it matters**: Without SessionStart injection, Claude doesn't see previous findings or planned next steps at session start.

### GAP 2: SessionEnd Hook Integration ❌ MISSING

**Current State**: Code Voyager has `update.py` but HexStrike doesn't call it.

**Required Implementation**:

```python
# In hexstrike_server.py - ADD THIS

from voyager.scripts.brain.update import main as update_brain
from datetime import datetime

@app.post("/api/hooks/session-end")
def on_session_end(request: Request):
    """
    SessionEnd hook from Claude
    
    Receives: {session_id, transcript: [...], ...}
    Updates brain.json with findings
    """
    hook_input = await request.json()
    
    session_id = hook_input.get("session_id", "")
    transcript = hook_input.get("transcript", [])
    
    # Update brain from transcript
    update_brain(
        transcript=transcript,
        session_id=session_id,
        skip_llm=False  # Let LLM analyze findings
    )
    
    # Save episode
    brain = load_brain()
    save_episode(brain, session_id, include_md=True)
    
    # Finalize unified memory
    memory = create_unified_memory(Path.cwd(), "HexStrikeSession")
    memory.finalize_session()
    
    return {"status": "session_end_processed"}
```

**Why it matters**: Without SessionEnd, findings are never reflected back to brain state, so they're lost for next session.

### GAP 3: Agent-Specific Memory Initialization ❌ PARTIAL

**Current State**: `simple_memory_agents.py` has agents but they're not initialized in hexstrike_server.py.

**Required Implementation**:

```python
# In hexstrike_server.py - ADD THIS at startup

from hexstrike_memory_integration import create_all_enhanced_agents

class HexStrikeServer:
    def __init__(self):
        # Initialize memory-enhanced agents
        self.enhanced_agents = create_all_enhanced_agents()
        
        # Expose agent memory endpoints
        self.setup_agent_memory_endpoints()
    
    def setup_agent_memory_endpoints(self):
        """Setup endpoints for agent memory operations"""
        
        @app.post("/api/agents/{agent_name}/remember")
        def agent_remember(agent_name: str, request: Request):
            """Add memory to specific agent"""
            data = await request.json()
            
            if agent_name not in self.enhanced_agents:
                return {"error": f"Agent {agent_name} not found"}
            
            agent = self.enhanced_agents[agent_name]
            
            # Route by type
            memory_type = data.get("type", "fact")
            if memory_type == "skill":
                agent.learn_skill(data["content"], data.get("context", ""))
            elif memory_type == "fact":
                agent.record_fact(data["content"], data.get("metadata"))
            else:
                agent.update_context(data["content"])
            
            return {"status": "remembered"}
        
        @app.get("/api/agents/{agent_name}/recall")
        def agent_recall(agent_name: str, query: str):
            """Recall memory for specific agent"""
            if agent_name not in self.enhanced_agents:
                return {"error": f"Agent {agent_name} not found"}
            
            agent = self.enhanced_agents[agent_name]
            knowledge = agent.recall_knowledge(query)
            
            return {
                "agent": agent_name,
                "query": query,
                "knowledge": knowledge,
                "summary": agent.get_summary()
            }
        
        @app.get("/api/agents/memory-stats")
        def memory_stats():
            """Get memory stats for all agents"""
            stats = {}
            for name, agent in self.enhanced_agents.items():
                stats[name] = agent.get_summary()
            
            return {
                "total_agents": len(stats),
                "memory_enabled": sum(1 for s in stats.values() if s["memory_enhanced"]),
                "agents": stats
            }
```

**Why it matters**: Agents need to be initialized to store/retrieve findings between requests.

### GAP 4: Unified Memory in Agent Workflows ❌ MISSING

**Current State**: UnifiedMemory exists but agents don't use it to share knowledge.

**Required Implementation**:

```python
# In each agent's work methods - ADD THIS

from voyager.memory.unified_memory import create_unified_memory

class EnhancedCVEIntelligenceManager(MemoryEnhancedHexStrikeAgent):
    def __init__(self):
        super().__init__("CVEIntelligenceManager")
        # Add unified memory layer
        self.unified_memory = create_unified_memory(
            Path.cwd(),
            agent_name="CVEIntelligenceManager"
        )
    
    def analyze_cve_with_memory(self, cve_id: str) -> dict:
        """Analyze CVE with accumulated intelligence"""
        
        # 1. Recall previous knowledge from BOTH systems
        previous_cve_knowledge = self.recall_knowledge(f"CVE {cve_id}")
        unified_results = self.unified_memory.recall(f"CVE {cve_id}", limit=5)
        
        analysis = {
            "cve_id": cve_id,
            "severity": "high",
            "memory_enhanced": (
                len(previous_cve_knowledge["facts"]) > 0 or
                len(unified_results["facts"]) > 0
            ),
            "related_cves": []
        }
        
        # 2. Use previous patterns
        if previous_cve_knowledge["facts"]:
            analysis["related_cves"] = ["CVE-2023-1234", "CVE-2023-5678"]
        
        # 3. Store finding
        self.record_fact(f"Analyzed {cve_id} with severity {analysis['severity']}")
        
        # 4. Store in unified memory for other agents
        self.unified_memory.store(
            content=f"CVE {cve_id}: severity={analysis['severity']}, type=authentication_bypass",
            memory_type="fact",
            speaker="CVEIntelligenceManager",
            metadata={"cve_id": cve_id, "severity": analysis["severity"]}
        )
        
        return analysis
```

**Why it matters**: Agents can't learn from each other's findings without unified memory layer.

### GAP 5: Agent-to-Agent Knowledge Sharing ❌ MISSING

**Current State**: Each agent has isolated memory, no cross-agent queries.

**Required Implementation**:

```python
# New utility class for cross-agent queries

class HexStrikeKnowledgeCoordinator:
    """Coordinates memory across all HexStrike agents"""
    
    def __init__(self, agents: Dict[str, MemoryEnhancedHexStrikeAgent]):
        self.agents = agents
        self.unified_memory = create_unified_memory(Path.cwd(), "HexStrikeCoordinator")
    
    def ask_all_agents(self, query: str) -> Dict[str, Dict]:
        """Ask all agents about topic, aggregate results"""
        results = {}
        
        for agent_name, agent in self.agents.items():
            knowledge = agent.recall_knowledge(query)
            if knowledge["skills"] or knowledge["facts"]:
                results[agent_name] = knowledge
        
        return results
    
    def record_finding_to_all(self, finding: str, metadata: Dict = None):
        """Record finding in unified memory (accessible to all agents)"""
        self.unified_memory.store(
            content=finding,
            memory_type="fact",
            speaker="HexStrike",
            metadata=metadata
        )
        
        # Also record to simple memory for persistence
        for agent in self.agents.values():
            agent.record_fact(finding, metadata)
    
    def correlate_findings(self) -> Dict:
        """Find patterns across all agent memories"""
        all_facts = []
        
        for agent_name, agent in self.agents.items():
            # Get all facts from this agent's memory
            facts = agent.memory.facts
            all_facts.extend([(agent_name, f) for f in facts])
        
        # Correlate: Group by theme
        correlations = self._group_by_theme(all_facts)
        
        # Store correlation as fact
        self.record_finding_to_all(
            f"Found {len(correlations)} correlation patterns across agents",
            metadata={"type": "correlation"}
        )
        
        return correlations
    
    def _group_by_theme(self, facts: List[tuple]) -> Dict:
        """Simple grouping logic (could be enhanced with LLM)"""
        themes = {}
        
        for agent_name, fact in facts:
            # Extract theme from fact description
            desc = fact["description"].lower()
            
            # Simple keyword matching
            if "sql" in desc or "injection" in desc:
                theme = "SQL Injection"
            elif "xss" in desc:
                theme = "XSS"
            elif "auth" in desc:
                theme = "Authentication"
            else:
                theme = "Other"
            
            if theme not in themes:
                themes[theme] = []
            
            themes[theme].append({
                "agent": agent_name,
                "fact": fact
            })
        
        return themes
```

**Why it matters**: With 12 agents, they must share findings. Without coordination, each agent rediscovers same vulnerabilities.

### GAP 6: Memory Persistence Across Requests ❌ MISSING

**Current State**: Memory files exist but are not automatically persisted in server lifecycle.

**Required Implementation**:

```python
# In hexstrike_server.py - ADD THIS

import atexit
from threading import Lock

class HexStrikeMemoryManager:
    """Manages memory persistence across server lifecycle"""
    
    def __init__(self, agents: Dict[str, MemoryEnhancedHexStrikeAgent]):
        self.agents = agents
        self.unified_memory = None
        self.lock = Lock()
        
        # Register cleanup on shutdown
        atexit.register(self.flush_all_memory)
    
    def flush_all_memory(self):
        """Called on server shutdown to persist all memory"""
        print("[HexStrike Memory] Flushing all agent memory...")
        
        with self.lock:
            for agent_name, agent in self.agents.items():
                try:
                    # Memory is auto-saved by SimpleMemorySystem
                    # Just log for debugging
                    stats = agent.get_summary()
                    print(f"  {agent_name}: {stats['total_memories']} memories")
                except Exception as e:
                    print(f"  ERROR flushing {agent_name}: {e}")
        
        # Finalize unified memory
        if self.unified_memory:
            self.unified_memory.finalize_session()
        
        print("[HexStrike Memory] Flush complete")
    
    def load_agent_memory(self, agent_name: str):
        """Preload agent memory from disk on request"""
        if agent_name in self.agents:
            agent = self.agents[agent_name]
            agent._load_agent_knowledge()  # Reloads from disk
            return True
        return False

# In HexStrikeServer.__init__()
self.memory_manager = HexStrikeMemoryManager(self.enhanced_agents)
```

**Why it matters**: Without persistence management, agent memory would be lost on server restart.

### GAP 7: SimpleMem Integration ❌ PARTIAL

**Current State**: UnifiedMemory tries to use SimpleMem but it's optional/fallback.

**Required Implementation**:

```python
# In hexstrike_server.py - ADD THIS

from main import SimpleMemSystem  # From SimpleMem-main/

class HexStrikeSimpleMemIntegration:
    """Full SimpleMem integration for dialogue-to-facts compression"""
    
    def __init__(self, db_path: str = ".hexstrike/simplemem.db"):
        self.system = SimpleMemSystem(
            db_path=db_path,
            model="gpt-4o",  # Use same model as HexStrike
            enable_parallel_processing=True,
            max_parallel_workers=3
        )
        self.session_dialogues = []
    
    def record_agent_action(self, agent_name: str, action: str, details: str = ""):
        """Record agent action as dialogue for SimpleMem"""
        dialogue = f"{action}: {details}" if details else action
        
        self.system.add_dialogue(
            speaker=agent_name,
            content=dialogue,
            timestamp=datetime.now().isoformat()
        )
        
        self.session_dialogues.append({
            "agent": agent_name,
            "action": action,
            "details": details
        })
    
    def finalize_session(self):
        """Compress session dialogues into facts"""
        print("[SimpleMem] Finalizing session...")
        self.system.finalize()
        print(f"[SimpleMem] Processed {len(self.session_dialogues)} agent actions")
    
    def query_memory(self, question: str) -> str:
        """Ask SimpleMem about accumulated knowledge"""
        answer = self.system.ask(question)
        return answer

# In HexStrikeServer.__init__()
self.simplemem_integration = HexStrikeSimpleMemIntegration()

# In agent methods
def analyze_cve_with_memory(self, cve_id: str):
    # ... do analysis ...
    
    # Record to SimpleMem for dialogue compression
    self.server.simplemem_integration.record_agent_action(
        agent_name="CVEIntelligenceManager",
        action="analyze_cve",
        details=f"CVE {cve_id}: severity={severity}, type={vuln_type}"
    )
```

**Why it matters**: SimpleMem enables dialogue-to-facts compression, compacting long sessions.

---

## Recommended Wiring Integration Plan

### Phase 1: Essential Hooks (CRITICAL)
**Effort**: 2-3 iterations

```python
# 1. Add SessionStart hook handler
# 2. Add SessionEnd hook handler
# 3. Initialize enhanced agents on server startup
# 4. Wire simple memory endpoints
```

### Phase 2: Unified Memory Bridge (HIGH)
**Effort**: 2-3 iterations

```python
# 1. Initialize UnifiedMemory per session
# 2. Add unified memory endpoints
# 3. Implement agent-to-agent memory sharing
# 4. Add knowledge coordinator
```

### Phase 3: Full SimpleMem Integration (MEDIUM)
**Effort**: 2 iterations

```python
# 1. Initialize SimpleMemSystem at startup
# 2. Record all agent actions as dialogues
# 3. Finalize SimpleMem at SessionEnd
# 4. Query compressed memory
```

### Phase 4: Memory Persistence (MAINTENANCE)
**Effort**: 1 iteration

```python
# 1. Add memory flush on shutdown
# 2. Add memory preload on request
# 3. Add stats/monitoring endpoints
```

---

## Integration Code Template

```python
# Complete template for hexstrike_server.py modifications

from pathlib import Path
from voyager.scripts.brain.inject import inject_from_stdin_direct
from voyager.brain.store import load_brain, save_brain, save_episode, save_last_update
from voyager.memory.unified_memory import create_unified_memory
from hexstrike_memory_integration import create_all_enhanced_agents
from simple_memory_agents import MemoryEnhancedHexStrikeAgent
from main import SimpleMemSystem

class EnhancedHexStrikeServer:
    def __init__(self):
        # Initialize agents with memory
        self.enhanced_agents = create_all_enhanced_agents()
        
        # Initialize unified memory
        self.unified_memory = create_unified_memory(Path.cwd(), "HexStrike")
        
        # Initialize SimpleMem
        self.simplemem = SimpleMemSystem(
            db_path=".hexstrike/simplemem.db",
            enable_parallel_processing=True
        )
        
        # Load brain state
        self.brain = load_brain()
    
    async def on_session_start(self, session_id: str, cwd: str):
        """SessionStart hook: Inject brain context"""
        hook_input = {"session_id": session_id, "cwd": cwd}
        output = self._inject_context(hook_input)
        return output
    
    async def on_session_end(self, session_id: str, transcript: List[Dict]):
        """SessionEnd hook: Update brain and finalize memory"""
        # Update brain from transcript
        self._update_brain_from_transcript(session_id, transcript)
        
        # Save episode
        save_episode(self.brain, session_id, include_md=True)
        
        # Finalize memories
        self.unified_memory.finalize_session()
        self.simplemem.finalize()
    
    def record_finding(self, agent_name: str, finding: str, memory_type: str = "fact"):
        """Record finding in all memory layers"""
        
        # 1. Record in agent's simple memory
        agent = self.enhanced_agents.get(agent_name)
        if agent:
            if memory_type == "skill":
                agent.learn_skill(finding)
            else:
                agent.record_fact(finding)
        
        # 2. Record in unified memory
        self.unified_memory.store(
            content=finding,
            memory_type=memory_type,
            speaker=agent_name
        )
        
        # 3. Record in SimpleMem for compression
        self.simplemem.add_dialogue(agent_name, finding)
    
    def _inject_context(self, hook_input: Dict) -> Dict:
        """Inject brain context at SessionStart"""
        from voyager.scripts.brain.inject import build_context
        from voyager.repo.snapshot import snapshot_to_json
        from voyager.io import read_file
        
        cwd = hook_input.get("cwd", str(Path.cwd()))
        brain_md = read_file(".claude/brain.md")
        snapshot = snapshot_to_json(cwd)
        
        context = build_context(brain_md, self.brain, snapshot)
        
        return {
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": context
            }
        }
    
    def _update_brain_from_transcript(self, session_id: str, transcript: List[Dict]):
        """Update brain state from session transcript"""
        # Extract findings and decisions from transcript
        findings = self._extract_findings(transcript)
        
        # Update brain
        self.brain["progress"]["recent_changes"].extend(findings)
        self.brain["signals"]["last_session_id"] = session_id
        self.brain["signals"]["last_updated_at"] = datetime.now().isoformat()
        
        # Save
        save_brain(self.brain)
    
    def _extract_findings(self, transcript: List[Dict]) -> List[str]:
        """Extract key findings from transcript"""
        findings = []
        
        for entry in transcript:
            if "vulnerability" in entry.get("content", "").lower():
                findings.append(entry["content"])
        
        return findings

# Mount this in FastAPI
app = FastAPI()
hexstrike_server = EnhancedHexStrikeServer()

@app.post("/api/hooks/session-start")
async def session_start(request: Request):
    data = await request.json()
    return hexstrike_server.on_session_start(
        data.get("session_id"),
        data.get("cwd")
    )

@app.post("/api/hooks/session-end")
async def session_end(request: Request):
    data = await request.json()
    await hexstrike_server.on_session_end(
        data.get("session_id"),
        data.get("transcript", [])
    )
    return {"status": "processed"}
```

---

## Verification Checklist

- [ ] SessionStart hook wired and injecting brain context
- [ ] SessionEnd hook wired and updating brain state
- [ ] All 12 agents initialized with memory
- [ ] Simple memory endpoints working (/remember, /recall, /stats)
- [ ] Unified memory initialized per session
- [ ] SimpleMem system initialized and processing dialogues
- [ ] Agent findings stored in all three memory layers
- [ ] Memory persisted across requests
- [ ] Cross-agent knowledge sharing working
- [ ] Memory stats endpoint returning correct counts

