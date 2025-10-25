# VesselOS Kira Prime – Git Submodules & Unified Storage Architecture

**Version**: 1.3.0  
**Focus**: Repository Integration + Sequential Agent Routing  
**Status**: Implementation Ready

---

## 📋 Table of Contents

1. [Git Submodules Integration](#git-submodules-integration)
2. [Unified Storage Architecture](#unified-storage-architecture)
3. [Sequential Routing System](#sequential-routing-system)
4. [Agent Storage Schemas](#agent-storage-schemas)
5. [Implementation Guide](#implementation-guide)
6. [Testing & Validation](#testing--validation)

---

## 🔗 Git Submodules Integration

### Architecture Overview

```
kira-prime/
├── .git/
├── .gitmodules                      # Submodule configuration
├── external/                        # External modules
│   ├── vessel-narrative-mrp/       # Submodule: MRP system
│   │   ├── scrolls/
│   │   ├── personas/
│   │   └── rituals/
│   └── echo-community-toolkit/     # Submodule: Echo tools
│       ├── steganography/
│       ├── memory/
│       └── ledger/
├── agents/                          # Core agents
│   ├── garden/                     # Ritual orchestrator
│   ├── echo/                       # Voice & persona
│   ├── limnus/                     # Memory & ledger
│   └── kira/                       # Validator
├── storage/                         # Unified storage layer
│   ├── adapters/                   # Storage adapters
│   ├── schemas/                    # Data schemas
│   └── migrations/                 # Schema migrations
└── interface/                       # Routing & orchestration
    ├── router.py                   # Sequential router
    └── dispatcher.py               # Agent dispatcher
```

### Step 1: Add Submodules

```bash
#!/bin/bash
# scripts/setup_submodules.sh

set -e

echo "🔗 Setting up Git submodules..."

# Create external directory
mkdir -p external

# Add vessel-narrative-mrp as submodule
echo "Adding vessel-narrative-mrp..."
git submodule add https://github.com/your-org/vessel-narrative-mrp.git external/vessel-narrative-mrp

# Add echo-community-toolkit as submodule
echo "Adding echo-community-toolkit..."
git submodule add https://github.com/your-org/echo-community-toolkit.git external/echo-community-toolkit

# Initialize and update submodules
git submodule init
git submodule update

echo "✅ Submodules added!"
echo ""
echo "To clone this repo with submodules, use:"
echo "  git clone --recurse-submodules <repo-url>"
echo ""
echo "To update submodules to latest:"
echo "  git submodule update --remote"
```

### Step 2: .gitmodules Configuration

```ini
# .gitmodules

[submodule "external/vessel-narrative-mrp"]
    path = external/vessel-narrative-mrp
    url = https://github.com/your-org/vessel-narrative-mrp.git
    branch = main

[submodule "external/echo-community-toolkit"]
    path = external/echo-community-toolkit
    url = https://github.com/your-org/echo-community-toolkit.git
    branch = main
```

### Step 3: Submodule Management Scripts

```bash
#!/bin/bash
# scripts/update_submodules.sh

# Update all submodules to latest
git submodule update --remote --merge

# Show submodule status
git submodule status

echo "✅ Submodules updated!"
```

```bash
#!/bin/bash
# scripts/sync_external.sh

# Sync specific files from submodules to core system
echo "🔄 Syncing external resources..."

# Copy scrolls from vessel-narrative-mrp
cp -r external/vessel-narrative-mrp/scrolls/* assets/scrolls/

# Copy personas from vessel-narrative-mrp
cp -r external/vessel-narrative-mrp/personas/* assets/personas/

# Copy steganography tools from echo-community-toolkit
cp -r external/echo-community-toolkit/steganography/* agents/limnus/stego/

# Copy memory utilities from echo-community-toolkit
cp -r external/echo-community-toolkit/memory/* storage/adapters/

echo "✅ External resources synced!"
```

---

## 💾 Unified Storage Architecture

### Storage Layer Design

```
┌─────────────────────────────────────────────────────────┐
│              Unified Storage Layer                      │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────┐ │
│  │  Garden   │  │   Echo    │  │  Limnus   │  │  Kira │ │
│  │  Storage  │  │  Storage  │  │  Storage  │  │Storage│ │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └───┬───┘ │
│        │              │              │             │     │
│        └──────────────┴──────────────┴─────────────┘     │
│                       │                                  │
│                ┌──────▼──────┐              ┌──────────┐ │
│                │   Storage   │              │  Storage │ │
│                │   Adapter   │              │  Adapter │ │
│                │  (Primary)  │              │ (Secondary│ │
│                └──────┬──────┘              └─────┬────┘ │
│                       │                            │     │
│        ┌──────────────┼────────────┬───────────────┘     │
│        │              │            │                     │
│        ▼              ▼            ▼                     │
│   ┌────────┐    ┌────────┐   ┌─────────┐                │
│   │  JSON  │    │ SQLite │   │ MongoDB │                │
│   └────────┘    └────────┘   └─────────┘                │
│                                                         │
│  Features:                                              │
│    • Pluggable backends (JSON/SQLite/MongoDB/etc)       │
│    • Unified schema across all agents                   │
│    • Automatic migrations                               │
│    • Transaction support                                │
│    • Backup/restore                                     │
└─────────────────────────────────────────────────────────┘
```

### Storage Schema

```python
# storage/schemas/base.py

"""
Unified storage schema for all agents

All agents follow this structure:
- Common fields (id, timestamp, workspace_id)
- Agent-specific data in flexible 'data' field
- Metadata for versioning and auditing
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import json

@dataclass
class BaseRecord:
    """Base record for all storage"""
    id: str
    workspace_id: str
    agent: str  # 'garden', 'echo', 'limnus', 'kira'
    timestamp: str
    record_type: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    version: int = 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=2)
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create from dictionary"""
        return cls(**data)
```

### Storage Adapter Interface

```python
# storage/adapters/base.py

"""
Base storage adapter interface

All storage backends (JSON, SQLite, MongoDB) implement this interface.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path
from storage.schemas.base import BaseRecord

class StorageAdapter(ABC):
    """Base storage adapter"""
    
    def __init__(self, workspace_id: str, root: Path):
        self.workspace_id = workspace_id
        self.root = Path(root)
    
    @abstractmethod
    async def create(self, record: BaseRecord) -> str:
        """Create new record, return ID"""
        ...
    
    @abstractmethod
    async def read(self, record_id: str) -> Optional[BaseRecord]:
        """Read record by ID"""
        ...
    
    @abstractmethod
    async def update(self, record_id: str, data: Dict[str, Any]) -> bool:
        """Update record"""
        ...
    
    @abstractmethod
    async def delete(self, record_id: str) -> bool:
        """Delete record"""
        ...
    
    @abstractmethod
    async def query(self, 
                   agent: Optional[str] = None,
                   record_type: Optional[str] = None,
                   filters: Optional[Dict[str, Any]] = None,
                   limit: int = 100) -> List[BaseRecord]:
        """Query records with filters"""
        ...
    
    @abstractmethod
    async def count(self, 
                   agent: Optional[str] = None,
                   record_type: Optional[str] = None) -> int:
        """Count records"""
        ...
    
    @abstractmethod
    async def backup(self, output_path: Path) -> bool:
        """Backup all data"""
        ...
    
    @abstractmethod
    async def restore(self, input_path: Path) -> bool:
        """Restore from backup"""
        ...


class StorageManager:
    """
    Manages storage adapters for all agents
    
    Provides unified interface for storage operations.
    """
    
    def __init__(self, workspace_id: str, backend: str = "json", root: Path = Path(".")):
        self.workspace_id = workspace_id
        self.backend = backend
        self.root = root
        
        # Initialize adapter
        self.adapter = self._create_adapter(backend)
    
    def _create_adapter(self, backend: str) -> StorageAdapter:
        """Create storage adapter based on backend type"""
        if backend == "json":
            from storage.adapters.json_adapter import JSONAdapter
            return JSONAdapter(self.workspace_id, self.root)
        if backend == "sqlite":
            from storage.adapters.sqlite_adapter import SQLiteAdapter
            return SQLiteAdapter(self.workspace_id, self.root)
        if backend == "mongodb":
            from storage.adapters.mongo_adapter import MongoAdapter
            return MongoAdapter(self.workspace_id, self.root)
        raise ValueError(f"Unknown backend: {backend}")
    
    async def create_record(self, 
                          agent: str, 
                          record_type: str, 
                          data: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Create new record"""
        import uuid
        from datetime import datetime, timezone
        
        record = BaseRecord(
            id=str(uuid.uuid4()),
            workspace_id=self.workspace_id,
            agent=agent,
            timestamp=datetime.now(timezone.utc).isoformat(),
            record_type=record_type,
            data=data,
            metadata=metadata or {}
        )
        
        return await self.adapter.create(record)
    
    async def get_record(self, record_id: str) -> Optional[BaseRecord]:
        """Get record by ID"""
        return await self.adapter.read(record_id)
    
    async def query_records(self,
                          agent: Optional[str] = None,
                          record_type: Optional[str] = None,
                          filters: Optional[Dict[str, Any]] = None,
                          limit: int = 100) -> List[BaseRecord]:
        """Query records"""
        return await self.adapter.query(agent, record_type, filters, limit)
    
    async def get_agent_state(self, agent: str) -> Dict[str, Any]:
        """Get current state for an agent"""
        records = await self.query_records(agent=agent, limit=1000)
        
        # Build state from records
        state = {
            "agent": agent,
            "workspace_id": self.workspace_id,
            "records": [r.to_dict() for r in records]
        }
        
        return state
```

### JSON Storage Adapter

```python
# storage/adapters/json_adapter.py

"""
JSON file storage adapter

Stores each agent's data in separate JSON files.
"""

import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime

from storage.adapters.base import StorageAdapter, BaseRecord

class JSONAdapter(StorageAdapter):
    """JSON file storage adapter"""
    
    def __init__(self, workspace_id: str, root: Path):
        super().__init__(workspace_id, root)
        self.storage_dir = self.root / "storage" / workspace_id
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Agent-specific storage files
        self.agent_files = {
            "garden": self.storage_dir / "garden.json",
            "echo": self.storage_dir / "echo.json",
            "limnus": self.storage_dir / "limnus.json",
            "kira": self.storage_dir / "kira.json"
        }
        
        # Initialize files
        for file_path in self.agent_files.values():
            if not file_path.exists():
                file_path.write_text(json.dumps({"records": []}, indent=2))
    
    def _load_agent_data(self, agent: str) -> dict:
        """Load data for specific agent"""
        file_path = self.agent_files.get(agent)
        if not file_path or not file_path.exists():
            return {"records": []}
        
        return json.loads(file_path.read_text())
    
    def _save_agent_data(self, agent: str, data: dict):
        """Save data for specific agent"""
        file_path = self.agent_files.get(agent)
        if file_path:
            file_path.write_text(json.dumps(data, indent=2))
    
    async def create(self, record: BaseRecord) -> str:
        """Create new record"""
        data = self._load_agent_data(record.agent)
        data["records"].append(record.to_dict())
        self._save_agent_data(record.agent, data)
        return record.id
    
    async def read(self, record_id: str) -> Optional[BaseRecord]:
        """Read record by ID"""
        for agent in self.agent_files.keys():
            data = self._load_agent_data(agent)
            for record_dict in data.get("records", []):
                if record_dict.get("id") == record_id:
                    return BaseRecord.from_dict(record_dict)
        return None
    
    async def update(self, record_id: str, update_data: Dict[str, Any]) -> bool:
        """Update record"""
        for agent in self.agent_files.keys():
            data = self._load_agent_data(agent)
            for record_dict in data.get("records", []):
                if record_dict.get("id") == record_id:
                    record_dict["data"].update(update_data)
                    record_dict.setdefault("metadata", {})["updated_at"] = datetime.now().isoformat()
                    self._save_agent_data(agent, data)
                    return True
        return False
    
    async def delete(self, record_id: str) -> bool:
        """Delete record"""
        for agent in self.agent_files.keys():
            data = self._load_agent_data(agent)
            original_count = len(data.get("records", []))
            data["records"] = [r for r in data.get("records", []) if r.get("id") != record_id]
            if len(data["records"]) < original_count:
                self._save_agent_data(agent, data)
                return True
        return False
    
    async def query(self,
                   agent: Optional[str] = None,
                   record_type: Optional[str] = None,
                   filters: Optional[Dict[str, Any]] = None,
                   limit: int = 100) -> List[BaseRecord]:
        """Query records"""
        results: List[BaseRecord] = []
        agents_to_search = [agent] if agent else list(self.agent_files.keys())
        
        for agent_name in agents_to_search:
            data = self._load_agent_data(agent_name)
            for record_dict in data.get("records", []):
                if record_type and record_dict.get("record_type") != record_type:
                    continue
                if filters:
                    match = all(record_dict.get("data", {}).get(k) == v for k, v in filters.items())
                    if not match:
                        continue
                results.append(BaseRecord.from_dict(record_dict))
                if len(results) >= limit:
                    return results
        return results
    
    async def count(self, agent: Optional[str] = None, record_type: Optional[str] = None) -> int:
        """Count records"""
        count = 0
        agents_to_search = [agent] if agent else list(self.agent_files.keys())
        
        for agent_name in agents_to_search:
            data = self._load_agent_data(agent_name)
            for record_dict in data.get("records", []):
                if record_type and record_dict.get("record_type") != record_type:
                    continue
                count += 1
        return count
    
    async def backup(self, output_path: Path) -> bool:
        """Backup all data"""
        import tarfile
        with tarfile.open(output_path, "w:gz") as tar:
            tar.add(self.storage_dir, arcname="storage")
        return True
    
    async def restore(self, input_path: Path) -> bool:
        """Restore from backup"""
        import tarfile
        with tarfile.open(input_path, "r:gz") as tar:
            tar.extractall(self.root)
        return True
```

---

## 🔀 Sequential Routing System

### Router Architecture

```
User Input (Voice/Text)
        ↓
┌─────────────┐
│   Router    │
│  (Dispatch) │
└──────┬──────┘
       │
       ↓
[Sequential Flow]
         │
┌────▼────┐
│ Garden  │─→ Log ritual event, advance stage
└────┬────┘
     │
┌────▼────┐
│  Echo   │─→ Apply persona styling, voice modulation
└────┬────┘
     │
┌────▼────┐
│ Limnus  │─→ Store in memory, update ledger
└────┬────┘
     │
┌────▼────┐
│  Kira   │─→ Validate, check integrity
└────┬────┘
     │
     ↓
   Synthesized Response
```

### Router Implementation

```python
# interface/router.py

"""
Sequential Agent Router

Routes input through agents in order: Garden → Echo → Limnus → Kira
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import logging

from storage.adapters.base import StorageManager
from agents.garden.garden_agent import GardenAgent
from agents.echo.echo_agent import EchoAgent
from agents.limnus.limnus_agent import LimnusAgent
from agents.kira.kira_agent import KiraAgent

logger = logging.get_logger(__name__)

@dataclass
class RoutingContext:
    """Context passed through routing pipeline"""
    input_text: str
    user_id: str
    workspace_id: str
    timestamp: str
    metadata: Dict[str, Any]
    garden_result: Optional[Dict[str, Any]] = None
    echo_result: Optional[Dict[str, Any]] = None
    limnus_result: Optional[Dict[str, Any]] = None
    kira_result: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def to_dict(self) -> dict:
        return asdict(self)


class SequentialRouter:
    """Routes input through agents sequentially"""
    
    def __init__(self, workspace_id: str, storage: StorageManager):
        self.workspace_id = workspace_id
        self.storage = storage
        self.garden = GardenAgent(workspace_id, storage)
        self.echo = EchoAgent(workspace_id, storage)
        self.limnus = LimnusAgent(workspace_id, storage)
        self.kira = KiraAgent(workspace_id, storage)
        self.sequence = [
            ("garden", self.garden),
            ("echo", self.echo),
            ("limnus", self.limnus),
            ("kira", self.kira)
        ]
    
    async def route(self, input_text: str, user_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Route input through sequential agent pipeline"""
        context = RoutingContext(
            input_text=input_text,
            user_id=user_id,
            workspace_id=self.workspace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            metadata=metadata or {}
        ) Aunt as legible? wait truncated at in doc? in original.
