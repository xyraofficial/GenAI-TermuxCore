# NEXUS Agent v27

## Overview

NEXUS Agent v27 is a terminal-based AI assistant built for Termux (Android terminal emulator). It acts as an intelligent command-line agent that can execute terminal commands, perform Google searches, and provide real-time information. The agent uses the Groq API with the LLaMA 3.3 70B model to process natural language requests and respond with either direct replies or tool executions.

The project is designed specifically for the Termux environment, which has unique constraints like no sudo access and different package management commands.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Application Structure

**Problem**: Need a modular AI agent that can handle terminal operations safely in Termux.

**Solution**: Three-layer architecture separating concerns:
- `main.py` - Entry point, configuration management, and API communication with Groq
- `core/engine.py` - Terminal execution engine with Termux-specific command sanitization
- `modules/tools.py` - External tool integrations (search, time)
- `utils/loader.py` - UI components (animated loading indicator)

### AI Response Pattern

**Problem**: Need structured, predictable AI responses for tool execution.

**Solution**: JSON-only response format with two action types:
1. `{"action": "tool", "tool_name": "...", "args": "..."}` - Execute a tool
2. `{"action": "reply", "content": "..."}` - Direct text response

This ensures deterministic parsing of AI outputs for automated execution.

### Termux Command Sanitization

**Problem**: Termux lacks sudo and uses different package managers than standard Linux.

**Solution**: The `sanitize_command()` function in `core/engine.py`:
- Strips `sudo` prefixes automatically
- Converts `apt`/`apt-get` commands to `pkg` equivalents
- Auto-adds `-y` flags to prevent interactive prompts blocking execution

### Configuration Persistence

**Problem**: Need to persist API keys across sessions.

**Solution**: Simple JSON file (`nexus_config.json`) storing the Groq API key. Loaded on startup, saved when modified.

### Rich Terminal UI

**Problem**: Need visually appealing terminal interface.

**Solution**: Uses the `rich` library for:
- Styled panels and headers
- Markdown rendering
- Animated loading indicators with `HackerLoader` class
- Formatted tables and prompts

## External Dependencies

### Groq API
- **Purpose**: LLM inference using LLaMA 3.3 70B model
- **Endpoint**: `https://api.groq.com/openai/v1/chat/completions`
- **Auth**: API key stored in `nexus_config.json`
- **Model**: `llama-3.3-70b-versatile`

### Python Packages
- `requests` - HTTP client for Groq API calls
- `rich` - Terminal formatting, panels, markdown, live animations
- `googlesearch-python` - Google search integration via `googlesearch.search`

### System Requirements
- Termux environment (Android terminal)
- Python 3.x runtime
- Network access for API calls and web searches