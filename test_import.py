#!/usr/bin/env python3
import sys
sys.path.insert(0, 'src')

import agentxploitor

# Get exact name
name = 'AgentxploiTorAgent'
print(f"Importing: {name!r}")

module = __import__('agentxploitor', fromlist=[name])
cls = getattr(module, name)
print(f"Got class: {cls}")
