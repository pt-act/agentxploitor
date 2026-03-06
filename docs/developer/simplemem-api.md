# SimpleMem API Reference

## Overview

SimpleMem is an efficient lifelong memory system for LLM agents. It uses a three-stage pipeline based on Semantic Lossless Compression to maximize information density and token utilization.

**Three Stages**:
1. **Semantic Structured Compression**: Dialogue → Atomic Memory Entries (via MemoryBuilder)
2. **Structured Indexing & Consolidation**: Background evolution and indexing
3. **Adaptive Query-Aware Retrieval**: Question → Compressed factual answer (via HybridRetriever + AnswerGenerator)

## Import Paths

```python
# Main system
from main import SimpleMemSystem

# Data models
from models.memory_entry import MemoryEntry, Dialogue

# Core components
from core.memory_builder import MemoryBuilder
from core.hybrid_retriever import HybridRetriever
from core.answer_generator import AnswerGenerator

# Supporting components
from database.vector_store import VectorStore
from utils.embedding import EmbeddingModel
from utils.llm_client import LLMClient
```

## SimpleMemSystem (Main API)

### Initialization

```python
from main import SimpleMemSystem

# Minimal initialization (uses environment/config defaults)
system = SimpleMemSystem(
    db_path="./simplemem.db"
)

# Full customization
system = SimpleMemSystem(
    api_key="sk-...",                          # OpenAI API key
    model="gpt-4o",                            # LLM model
    base_url="https://api.openai.com/v1",     # Custom base URL
    db_path="./simplemem.db",                 # Database location
    table_name="memory_default",               # Memory table name
    clear_db=False,                            # Clear existing data
    enable_thinking=True,                      # Deep thinking mode
    use_streaming=False,                       # Streaming responses
    enable_planning=True,                      # Multi-query planning
    enable_reflection=True,                    # Reflection-based retrieval
    max_reflection_rounds=2,                   # Reflection iterations
    enable_parallel_processing=True,           # Parallel memory building
    max_parallel_workers=3,                    # Parallel workers
    enable_parallel_retrieval=True,            # Parallel query execution
    max_retrieval_workers=2                    # Parallel retrieval workers
)
```

**Parameter Defaults** (from config):
- `model`: "gpt-4o" (check config.py for current default)
- `enable_thinking`: False (enable for deep reasoning)
- `use_streaming`: False (streaming responses)
- `enable_planning`: True (multi-query planning)
- `enable_reflection`: True (reflection-based retrieval)
- `max_reflection_rounds`: 2 (reflection iterations)
- `enable_parallel_processing`: True (parallel memory building)
- `max_parallel_workers`: 4 (default workers)
- `enable_parallel_retrieval`: False (parallel retrieval)
- `max_retrieval_workers`: 3 (parallel retrieval workers)

## Data Models

### MemoryEntry (Atomic Entry)

Represents a self-contained, disambiguated fact extracted from dialogue.

```python
from models.memory_entry import MemoryEntry
from typing import List, Optional

class MemoryEntry:
    # Semantic Layer - Dense embedding base
    lossless_restatement: str  # Self-contained fact, no pronouns
    
    # Lexical Layer - Sparse keyword vectors
    keywords: List[str]  # Core keywords for exact matching (BM25)
    
    # Symbolic Layer - Metadata constraints
    timestamp: Optional[str]  # ISO 8601 format
    location: Optional[str]   # Natural language location
    persons: List[str]        # Extracted persons
    entities: List[str]       # Extracted entities (companies, products)
    topic: Optional[str]      # Topic phrase
    entry_id: str            # UUID
```

**Example MemoryEntry**:
```python
MemoryEntry(
    entry_id="550e8400-e29b-41d4-a716-446655440000",
    lossless_restatement="Alice discussed the marketing strategy for product XYZ with Bob at Starbucks in Shanghai on November 15, 2025 at 14:30",
    keywords=["Alice", "Bob", "product XYZ", "marketing strategy", "discussion"],
    timestamp="2025-11-15T14:30:00",
    location="Starbucks, Shanghai",
    persons=["Alice", "Bob"],
    entities=["product XYZ"],
    topic="Product marketing strategy discussion"
)
```

### Dialogue

Original dialogue entry from conversation.

```python
from models.memory_entry import Dialogue
from typing import Optional

class Dialogue:
    dialogue_id: int         # Sequential ID
    speaker: str             # Speaker name
    content: str             # Dialogue content
    timestamp: Optional[str] # ISO 8601 format

    def __str__(self) -> str:
        # Returns "[timestamp] speaker: content"
```

**Example Dialogue**:
```python
Dialogue(
    dialogue_id=1,
    speaker="user",
    content="How do we prevent SQL injection attacks?",
    timestamp="2025-01-15T14:30:00"
)
```

## Memory Interface

### `add_dialogue(speaker: str, content: str, timestamp: Optional[str] = None)`

Add a single dialogue to the memory system.

```python
# Simple dialogue
system.add_dialogue(
    speaker="user",
    content="What is the best way to implement rate limiting?"
)

# With timestamp
system.add_dialogue(
    speaker="assistant",
    content="Rate limiting should be implemented at API gateway level",
    timestamp="2025-01-15T14:30:00"
)

# Multiple dialogues in sequence
dialogues_sequence = [
    ("user", "How do we handle CORS?"),
    ("assistant", "CORS headers must be explicitly configured"),
    ("user", "What about OPTIONS requests?"),
    ("assistant", "OPTIONS is a preflight request type in CORS")
]

for speaker, content in dialogues_sequence:
    system.add_dialogue(speaker, content)
```

### `add_dialogues(dialogues: List[Dialogue])`

Batch add dialogues with optional parallel processing.

```python
from models.memory_entry import Dialogue

# Create dialogues
dialogues = [
    Dialogue(dialogue_id=1, speaker="user", content="Explain OAuth2"),
    Dialogue(dialogue_id=2, speaker="assistant", content="OAuth2 is a delegation protocol"),
    Dialogue(dialogue_id=3, speaker="user", content="How about implicit flow?"),
    Dialogue(dialogue_id=4, speaker="assistant", content="Implicit is deprecated for web apps"),
]

# Add in batch (uses parallel processing if > window_size * 2)
system.add_dialogues(dialogues)

# Parallel processing config:
# - If len(dialogues) > window_size * 2 → Use parallel workers
# - Otherwise → Use sequential processing
# - Window size: typically 10 dialogues (configurable)
```

### `finalize()`

Finalize dialogue input and process remaining buffer. Called at session end.

```python
# After adding all dialogues
system.finalize()

# What happens:
# 1. Process any remaining dialogues in buffer (safety check)
# 2. In parallel mode: already processed, this is fallback
# 3. All dialogues converted to atomic memory entries
# 4. Entries indexed in vector store (semantic + lexical + symbolic)
```

## Query Interface

### `ask(question: str) -> str`

Core Q&A interface for retrieving memory-augmented answers.

```python
# Simple question
answer = system.ask("What is the standard way to handle authentication?")
print(answer)

# Question with context
answer = system.ask("How did we previously handle rate limiting attacks?")

# Complex question (triggers planning + reflection)
answer = system.ask(
    "What security best practices did we discuss for API endpoints, "
    "and what specific implementation details were mentioned?"
)

# Expected behavior:
# 1. HybridRetriever searches vector store (semantic + lexical + symbolic)
# 2. If planning enabled: generates multiple query reformulations
# 3. If reflection enabled: refines results through multiple rounds
# 4. AnswerGenerator compresses retrieved entries into coherent answer
# 5. Returns: String answer with full context and facts
```

**Behind the Scenes**:
- Query-aware retrieval: Adapts based on question type
- Semantic search: Dense vector embeddings (semantic layer)
- Keyword search: BM25-style exact matching (lexical layer)
- Metadata filtering: Timestamp, location, entities (symbolic layer)
- Multi-round reflection: Iteratively refines results
- Answer generation: Compresses entries into natural language

## MemoryBuilder (Stage 1: Semantic Structured Compression)

Converts dialogues into atomic memory entries.

### Configuration

```python
from core.memory_builder import MemoryBuilder

builder = MemoryBuilder(
    llm_client=system.llm_client,
    vector_store=system.vector_store,
    window_size=10,                    # Dialogues per window
    enable_parallel_processing=True,   # Use parallel workers
    max_parallel_workers=3             # Number of workers
)

# Window-based processing:
# - Processes 10 dialogues at a time
# - Converts to atomic entries via LLM
# - Stores to vector store (semantic indexing)
# - Maintains previous window context
```

### Public Methods

#### `add_dialogue(dialogue, auto_process=True)`

Add single dialogue with optional auto-processing.

```python
dialogue = Dialogue(
    dialogue_id=1,
    speaker="assistant",
    content="Always validate user input to prevent SQL injection"
)

# Auto-process when buffer fills
builder.add_dialogue(dialogue, auto_process=True)

# Manual process (for testing)
builder.add_dialogue(dialogue, auto_process=False)
```

#### `add_dialogues(dialogues, auto_process=True)`

Batch add with parallel processing support.

```python
builder.add_dialogues(dialogues, auto_process=True)

# Processing logic:
if len(dialogues) > window_size * 2:
    # Use parallel processing
    add_dialogues_parallel(dialogues)
else:
    # Use sequential processing
    for dialogue in dialogues:
        add_dialogue(dialogue, auto_process=False)
```

#### `process_window()`

Manually process current window.

```python
# Manually trigger window processing
builder.process_window()

# What happens:
# 1. Extracts window from dialogue_buffer
# 2. Calls LLM to generate memory entries
# 3. Stores entries to vector_store
# 4. Maintains previous entries as context
# 5. Increments processed_count
```

#### `process_remaining()`

Process remaining dialogues (fallback method).

```python
# Safety check at session end
builder.process_remaining()

# Typically already done in parallel mode
# Used as fallback for incomplete windows
```

## HybridRetriever (Stage 3: Adaptive Query-Aware Retrieval)

Retrieves relevant memory entries using semantic, lexical, and symbolic search.

### Retrieval Modes

```python
from core.hybrid_retriever import HybridRetriever

retriever = HybridRetriever(
    llm_client=system.llm_client,
    vector_store=system.vector_store,
    enable_planning=True,              # Multi-query planning
    enable_reflection=True,            # Reflection-based refinement
    max_reflection_rounds=2,           # Iterations
    enable_parallel_retrieval=True,   # Parallel queries
    max_retrieval_workers=2            # Workers
)

# Retrieval strategy:
# 1. Multi-query planning: Rewrite question multiple ways
# 2. Hybrid search: Combine semantic + lexical + symbolic
# 3. Reflection: Iteratively refine results
# 4. Parallel execution: Search multiple reformulations simultaneously
```

### Retrieval Process

```python
# User asks question
question = "How should we validate API keys?"

# Internal process:
# 1. Query Planning: Generate 3-5 reformulations
#    - "Best practices for API key validation"
#    - "API key authentication implementation"
#    - "Secure API key handling patterns"
#
# 2. Parallel Search: Execute all queries in parallel
#    - Semantic search: embedding similarity
#    - Lexical search: keyword matching (BM25)
#    - Symbolic filter: metadata (timestamp, entities)
#
# 3. Reflection (if enabled): Analyze results
#    - Round 1: "Are results sufficient? Any missing context?"
#    - Round 2: "Should we search for related concepts?"
#    - Return refined results
#
# 4. Return: List of most relevant MemoryEntry objects
```

## AnswerGenerator (Stage 3: Answer Generation)

Compresses retrieved memory entries into coherent, natural language answers.

### Answer Generation

```python
from core.answer_generator import AnswerGenerator

generator = AnswerGenerator(llm_client=system.llm_client)

# Generator takes retrieved entries and produces:
# - Coherent narrative combining facts
# - Natural language without redundancy
# - Source entries implicitly compressed
# - Full context preserved in compressed form
```

## VectorStore (Database Layer)

Stores and retrieves memory entries with three-layer indexing.

### Three-Layer Indexing

```python
# Layer 1: Semantic (Dense Embeddings)
# - Entry: lossless_restatement
# - Index: Dense vector from embedding model
# - Query: Semantic similarity search
# - Distance: Cosine similarity

# Layer 2: Lexical (Sparse Keywords)
# - Entry: keywords field
# - Index: BM25 or similar sparse index
# - Query: Exact keyword matching
# - Distance: BM25 ranking

# Layer 3: Symbolic (Metadata)
# - Entry: timestamp, location, persons, entities, topic
# - Index: Metadata constraints
# - Query: Filtering (e.g., "January 2025", "Alice", "OAuth2")
# - Distance: Exact match
```

### Storage Methods

```python
from database.vector_store import VectorStore

vector_store = VectorStore(
    db_path="./simplemem.db",
    embedding_model=system.embedding_model,
    table_name="memory_default"
)

# Add entries (called by MemoryBuilder)
vector_store.add_entries(entries: List[MemoryEntry])

# Search entries (called by HybridRetriever)
results = vector_store.search(query: str, k: int)

# Clear database
vector_store.clear()
```

## EmbeddingModel

Generates dense embeddings for semantic search.

```python
from utils.embedding import EmbeddingModel

embedding_model = EmbeddingModel()

# Generate embedding for text
embedding = embedding_model.embed("API key validation best practices")
# Returns: 384-dim or 1536-dim vector (model dependent)

# Get model info
model_name = embedding_model.model_name
embedding_dim = embedding_model.embedding_dim
```

## LLMClient

Client for LLM interactions (memory generation, query planning, answer generation).

```python
from utils.llm_client import LLMClient

llm = LLMClient(
    api_key="sk-...",
    model="gpt-4o",
    base_url="https://api.openai.com/v1",
    enable_thinking=False,
    use_streaming=False
)

# Generate memory entries from dialogue
# (Called internally by MemoryBuilder)
entries = llm.generate_memory_entries(dialogue_window)

# Generate query reformulations
# (Called internally by HybridRetriever)
queries = llm.generate_queries(original_question)

# Generate answer
# (Called internally by AnswerGenerator)
answer = llm.generate_answer(question, retrieved_entries)
```

## Integration with HexStrike

SimpleMem integrates with HexStrike agents via UnifiedMemory (Code Voyager layer).

### Memory Types in HexStrike Context

```python
# Store security findings
system.add_dialogue(
    speaker="security_agent",
    content="Found XSS vulnerability in /search endpoint at line 234"
)

# Store exploit patterns
system.add_dialogue(
    speaker="exploit_agent",
    content="CSRF tokens should use SameSite=Strict and secure flag"
)

# Store detection methods
system.add_dialogue(
    speaker="cve_agent",
    content="CVE-2024-1234 requires authentication, affects versions <3.2"
)

# Later: Query accumulated knowledge
answer = system.ask("What XSS vulnerabilities have we found and where?")
answer = system.ask("How should CSRF tokens be configured for maximum security?")
answer = system.ask("What's our CVE detection pattern for authentication bypasses?")
```

## Configuration (config.py)

```python
# SimpleMem configuration parameters

WINDOW_SIZE = 10  # Dialogues per processing window

# LLM Settings
MODEL_NAME = "gpt-4o"
TEMPERATURE = 0.7

# Retrieval Settings
ENABLE_PLANNING = True
ENABLE_REFLECTION = True
MAX_REFLECTION_ROUNDS = 2

# Parallel Processing
ENABLE_PARALLEL_PROCESSING = True
MAX_PARALLEL_WORKERS = 4
ENABLE_PARALLEL_RETRIEVAL = False
MAX_RETRIEVAL_WORKERS = 3

# Database
DB_PATH = "./simplemem.db"
TABLE_NAME = "memory_default"
```

## Complete Example: Security Agent Memory

```python
from main import SimpleMemSystem
from models.memory_entry import Dialogue

# Initialize system
system = SimpleMemSystem(
    db_path="./hexstrike_memory.db",
    model="gpt-4o",
    enable_parallel_processing=True
)

# Simulate security agent findings
security_findings = [
    Dialogue(1, "scanner", "Port 22 open with weak SSH keys detected"),
    Dialogue(2, "analyzer", "SSH uses default configuration, upgrade to secure settings"),
    Dialogue(3, "scanner", "Found SQL injection in login form"),
    Dialogue(4, "analyzer", "Use parameterized queries and input validation"),
    Dialogue(5, "scanner", "Admin panel accessible without authentication"),
    Dialogue(6, "analyzer", "Implement OAuth2 or session-based auth"),
    Dialogue(7, "scanner", "Found 3 OWASP top 10 vulnerabilities"),
    Dialogue(8, "analyzer", "Prioritize: 1) Auth, 2) SQL Injection, 3) Rate Limiting"),
]

# Add findings (parallel processing)
system.add_dialogues(security_findings)

# Finalize
system.finalize()

# Query accumulated knowledge
print("Q: What vulnerabilities did we find?")
print(system.ask("What are all the vulnerabilities we discovered?"))
print()

print("Q: How should we fix SSH?")
print(system.ask("What was the recommendation for SSH security?"))
print()

print("Q: What's the remediation priority?")
print(system.ask("What order should we fix security issues in?"))
```

## Key Integration Points for AgentxploiTor

1. **Dialogue Storage**: Each agent action → `add_dialogue()`
2. **Batch Processing**: Multiple findings → `add_dialogues()` (parallel)
3. **Memory Finalization**: Session end → `finalize()`
4. **Knowledge Retrieval**: Agent questions → `ask()`
5. **Cross-Agent Context**: All agents share same VectorStore
6. **Temporal Tracking**: ISO timestamps on all entries
7. **Entity Extraction**: persons, entities metadata for filtering

