# Code Voyager API Reference

## Overview

Code Voyager is a skill indexing and retrieval system for AI agents. It provides:
- **VoyagerBrain**: Session state management (project summary, working set, decisions, progress)
- **SkillFactory**: Skill discovery, indexing, and retrieval using ColBERT embeddings
- **SessionStart/SessionEnd**: Hooks for injecting context at session boundaries

## Import Paths

```python
# Brain management
from voyager.brain.store import (
    load_brain,
    save_brain,
    create_empty_brain,
    save_episode,
    save_last_update
)

# Skill indexing and search
from voyager.retrieval.index import SkillIndex
from voyager.scripts.skill.find import main as find_skill
from voyager.scripts.skill.index_cmd import main as index_skills

# Context injection at SessionStart
from voyager.scripts.brain.inject import (
    inject_from_stdin,
    build_context
)

# Unified memory integration
from voyager.memory.unified_memory import (
    UnifiedMemory,
    create_unified_memory,
    quick_store,
    quick_recall,
    MemoryType
)

# Utilities
from voyager import read_file, read_json, write_file, write_json
from voyager.logging import get_logger
```

## VoyagerBrain API

### Brain Data Structure

```python
# Brain JSON schema (brain.json)
{
    "version": 1,
    "project": {
        "summary": str,              # Project overview
        "stack_guesses": [str],      # Technology stack guesses
        "key_commands": [str]        # Important commands
    },
    "working_set": {
        "current_goal": str,         # Current objective
        "current_plan": [str],       # Steps in current plan
        "open_questions": [str],     # Unresolved questions
        "risks": [str]               # Known risks
    },
    "decisions": [
        {
            "decision": str,         # What was decided
            "reasoning": str,        # Why this decision
            "timestamp": str         # When decided
        }
    ],
    "progress": {
        "recent_changes": [str],     # Recent modifications
        "done": [str]                # Completed items
    },
    "signals": {
        "last_session_id": str,      # Previous session ID
        "last_updated_at": str       # ISO 8601 timestamp
    }
}
```

### Brain Management Functions

#### `load_brain(path=None) -> Dict[str, Any]`
Load brain state from `brain.json`. Returns empty brain if missing or invalid.

```python
from voyager.brain.store import load_brain

# Load default brain from project
brain = load_brain()

# Load from custom path
brain = load_brain("/path/to/brain.json")

# Access brain state
current_goal = brain["working_set"]["current_goal"]
decisions = brain["decisions"]
progress = brain["progress"]
```

#### `save_brain(brain, path=None, validate_schema=True) -> bool`
Save brain state to `brain.json` with optional validation.

```python
from voyager.brain.store import save_brain

# Update brain state
brain["working_set"]["current_goal"] = "Fix authentication flow"
brain["working_set"]["current_plan"] = [
    "Review login handler",
    "Add token validation",
    "Test with edge cases"
]

# Save with validation (default)
success = save_brain(brain)

# Save without validation (faster)
success = save_brain(brain, validate_schema=False)
```

#### `create_empty_brain(session_id="") -> Dict[str, Any]`
Create a new empty brain with default structure.

```python
from voyager.brain.store import create_empty_brain

# Create new brain for a session
brain = create_empty_brain(session_id="claude-20250115-abc123")
```

#### `save_episode(brain, session_id, include_md=True) -> Path | None`
Save a snapshot of brain state for this session (for episode tracking).

```python
from voyager.brain.store import save_episode

# After session work, save episode
episode_path = save_episode(brain, session_id="claude-20250115-abc123", include_md=True)
# Creates: .claude/voyager/episodes/20250115_143022_claude_20250115_abc123.json
#          .claude/voyager/episodes/20250115_143022_claude_20250115_abc123.md
```

#### `save_last_update(session_id, status, error=None, transcript_lines=0) -> bool`
Save metadata about the last brain update attempt (for debugging).

```python
from voyager.brain.store import save_last_update

# After processing
success = save_last_update(
    session_id="claude-20250115-abc123",
    status="success",
    transcript_lines=1500
)

# On failure
success = save_last_update(
    session_id="claude-20250115-abc123",
    status="failed",
    error="LLM timeout after 30s"
)
```

## SkillFactory API

### SkillIndex Class

The `SkillIndex` class manages skill discovery, indexing, and retrieval using ColBERT embeddings.

#### Initialization

```python
from voyager.retrieval.index import SkillIndex
from pathlib import Path

# Default behavior (uses ~/.skill-index/)
index = SkillIndex()

# Custom index path
index = SkillIndex(index_path=Path("/custom/index/path"))
```

#### `build(skill_roots=None, force=False, skip_llm=False, verbose=False) -> int`
Build or update the skill index from available skill sources.

```python
# Build with all defaults
count = index.build()

# Force rebuild from scratch
count = index.build(force=True)

# Skip LLM analysis (faster, lower quality)
count = index.build(skip_llm=True)

# Verbose output
count = index.build(verbose=True)

# With custom skill roots
count = index.build(
    skill_roots=[
        Path("./skills"),
        Path("~/.claude/skills/"),
        Path("./.claude/skills/generated")
    ],
    force=False,
    verbose=True
)

print(f"Indexed {count} skills")
```

Discovers skills from:
- `./skills/` (plugin skills)
- `./.claude/skills/local/` (local mirrors)
- `./.claude/skills/generated/` (generated skills)
- `~/.claude/skills/` (user skills)

#### `search(query, k=5) -> List[SkillResult]`
Search for relevant skills using semantic search.

```python
# Simple search
results = index.search("how to handle OAuth2 authentication", k=5)

for result in results:
    print(f"Name: {result.name}")
    print(f"Purpose: {result.purpose}")
    print(f"Path: {result.path}")
    print(f"Score: {result.score:.3f}")
    print(f"File types: {result.file_types}")
    print(f"Capabilities: {result.capabilities}")
    print()

# Retrieve top 10 results
results = index.search("database migration", k=10)
```

### SkillResult Object

```python
class SkillResult:
    skill_id: str          # Unique skill identifier
    name: str              # Skill name
    purpose: str           # What the skill does
    path: str              # Path to skill file
    score: float           # Relevance score (0-1)
    file_types: List[str]  # File types supported
    capabilities: List[str]# Capabilities provided
```

## SessionStart/SessionEnd Hooks

### SessionStart: Injecting Context

The `inject_from_stdin()` function reads hook input and produces brain context for injection.

```python
from voyager.scripts.brain.inject import inject_from_stdin, build_context

# Called at SessionStart hook
output = inject_from_stdin()

# Output structure:
{
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": "## Session Brain\n[brain content]\n\n## Suggested Next Actions\n..."
    },
    "suppressOutput": True
}
```

#### `build_context(brain_md, brain, snapshot) -> str`
Build the injection context from brain state and repo snapshot.

```python
from voyager.scripts.brain.inject import build_context
from voyager.repo.snapshot import snapshot_to_json

# Get components
brain_md = read_file(".claude/brain.md")
brain = load_brain()
snapshot = snapshot_to_json(Path.cwd())

# Build context
context = build_context(brain_md, brain, snapshot)

# Context includes:
# - Session Brain (from brain.md)
# - Suggested Next Actions (from brain JSON)
# - Repo Snapshot (git info, file tree, run hints)
```

### SessionEnd Hook

Called automatically at session end. Used to update brain state from transcript.

```python
# Handled by: voyager.scripts.brain.update
# Triggered by: SessionEnd hook
# Input: JSONL transcript from session
# Output: Updated brain.json
```

## Unified Memory API

Combines Code Voyager skills/context with SimpleMem facts/dialogue.

### UnifiedMemory Class

#### Initialization

```python
from voyager.memory.unified_memory import UnifiedMemory, create_unified_memory
from pathlib import Path

# Method 1: Direct instantiation
memory = UnifiedMemory(
    project_dir=Path("/path/to/project"),
    agent_name="MyAgent",
    enable_simplemem=True
)

# Method 2: Convenience function
memory = create_unified_memory(
    project_dir="/path/to/project",
    agent_name="MyAgent"
)
```

#### Memory Types

```python
from voyager.memory.unified_memory import MemoryType

# Four memory types with automatic routing:
MemoryType.SKILL     # Procedural knowledge (how to do things)
MemoryType.FACT      # Episodic knowledge (what happened)
MemoryType.CONTEXT   # Project/session context
MemoryType.DIALOGUE  # Conversational memory
```

#### `store(content, memory_type=None, metadata=None, speaker="user", timestamp=None) -> bool`
Store information in appropriate memory layer with automatic routing.

```python
# Auto-classify memory type
memory.store(
    content="To implement OAuth2, first register app credentials with provider"
)

# Explicit memory type
memory.store(
    content="User requested new dashboard feature",
    memory_type=MemoryType.FACT,
    speaker="user",
    metadata={"feature_id": "DASH-42"}
)

# With custom timestamp
memory.store(
    content="Fixed SQL injection vulnerability in login endpoint",
    memory_type=MemoryType.SKILL,
    metadata={"severity": "critical"},
    timestamp="2025-01-15T14:30:00"
)
```

#### `recall(query, memory_types=None, limit=10) -> Dict[str, List[Dict]]`
Retrieve information from both memory systems.

```python
# Search all memory types
results = memory.recall("OAuth2 authentication")
# Returns: {
#     "skills": [...],
#     "facts": [...],
#     "context": [...],
#     "dialogue": [...]
# }

# Search specific types
results = memory.recall(
    query="login vulnerability",
    memory_types=[MemoryType.SKILL, MemoryType.FACT],
    limit=5
)

# Process results
for skill in results["skills"]:
    print(f"Skill: {skill['content']}")
    print(f"Learned: {skill['timestamp']}")
```

#### `finalize_session()`
Finalize memory systems at session end (compresses dialogue into facts).

```python
# Call at SessionEnd
memory.finalize_session()
# SimpleMem compresses dialogue buffer into atomic facts
# Voyager brain state is persisted
```

#### `get_memory_stats() -> Dict[str, Any]`
Get statistics about both memory systems.

```python
stats = memory.get_memory_stats()

print(f"Skills: {stats['unified']['memory_types']['skills']}")
print(f"Facts: {stats['unified']['memory_types']['facts']}")
print(f"Context: {stats['unified']['memory_types']['context']}")
print(f"Dialogue: {stats['unified']['memory_types']['dialogue']}")
print(f"Total: {stats['unified']['total_entries']}")
```

### Convenience Functions

#### `quick_store(memory, content, speaker="user") -> bool`
Quick store with automatic classification.

```python
from voyager.memory.unified_memory import quick_store

quick_store(memory, "Fixed authentication timeout issue", speaker="assistant")
```

#### `quick_recall(memory, query, limit=5) -> str`
Quick recall returning formatted summary.

```python
from voyager.memory.unified_memory import quick_recall

summary = quick_recall(memory, "database migrations", limit=5)
# Returns formatted string with all matching memories
print(summary)
```

## Configuration Files

### Brain Paths (via voyager.config)

```python
from voyager.config import (
    get_brain_md_path,      # .claude/brain.md
    get_brain_json_path,    # .claude/voyager/brain.json
    get_episodes_dir,       # .claude/voyager/episodes/
    get_voyager_state_dir   # .claude/voyager/
)

# Example
brain_dir = get_voyager_state_dir()  # Returns: Path("./.claude/voyager/")
```

### Skill Index Paths

```python
from voyager.retrieval.index import SkillIndex

index = SkillIndex()
print(index.index_path)  # ~/.skill-index/ (default)
```

## Complete Example: Integration Flow

```python
from pathlib import Path
from voyager.brain.store import load_brain, save_brain
from voyager.retrieval.index import SkillIndex
from voyager.memory.unified_memory import create_unified_memory

# 1. Initialize project
project_dir = Path("/path/to/project")

# 2. Load brain state
brain = load_brain()
print(f"Current goal: {brain['working_set']['current_goal']}")

# 3. Build skill index
index = SkillIndex()
skill_count = index.build(verbose=True)
print(f"Indexed {skill_count} skills")

# 4. Search for relevant skills
skills = index.search("authentication flow", k=3)
for skill in skills:
    print(f"- {skill.name}: {skill.purpose}")

# 5. Initialize unified memory
memory = create_unified_memory(project_dir, agent_name="SecurityAudit")

# 6. Store learnings
for skill in skills:
    memory.store(
        content=f"Skill: {skill.name} - {skill.purpose}",
        memory_type="skill"
    )

# 7. Update brain with progress
brain["progress"]["recent_changes"].append("Reviewed authentication patterns")
brain["working_set"]["current_plan"] = [
    "Implement secure token validation",
    "Add rate limiting to login endpoint",
    "Test with OWASP test suite"
]
save_brain(brain)

# 8. Finalize session
memory.finalize_session()
```

## Key Integration Points for AgentxploiTor

1. **SessionStart**: Use `inject_from_stdin()` to inject brain + skills into Claude context
2. **Skills Injection**: Call `index.search()` to find relevant security patterns
3. **Memory Layer**: Use `UnifiedMemory` to track learned exploits and techniques
4. **SessionEnd**: Call `memory.finalize_session()` to compress dialogue into facts
5. **Brain Updates**: Save `brain.json` with findings and next steps

