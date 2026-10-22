# OpenDataMCP – Model Context Protocol (MCP) Servere / AI Tools

[🇩🇰 Dansk](#dansk) | [🇬🇧 English](#english)

---

<a name="dansk"></a>
## 🇩🇰 Dansk

Velkommen til **OpenDataMCP**-repositoriet. Dette arkiv indeholder officielle, produktionsklare **Model Context Protocol (MCP)** servere udarbejdet til AI-assistenter, agenter og sprogmodeller (Claude Desktop, Antigravity, Cursor, m.fl.).

> **Type:** Færdige, selvstændige MCP-servere og SQLite-sprogdatabaser  
> **Seneste synkronisering:** `2026-10-22 18:47:51 UTC`  
> **Aktive MCP-servere:** `1` stk. (5 filer, 32.4 MB)

### 📂 Mappestruktur

Hver MCP-server er placeret i sin egen undermappe med serverkode, SQLite-database, bygge-script og test-suite:

```text
OpenDataMCP/
├── README.md               # Denne centrale tosprogede dokumentation
├── mcp_manifest.json       # SHA-256 hash og filmanifest
├── cor/
│   ├── server.py           # MCP Server (JSON-RPC / stdio)
│   ├── build_db.py         # Database builder
│   ├── test_tools.py       # Værktøjstest og validering
│   └── README.md           # Serverspecifik dokumentation og opsætning
```

### 🛠️ Tilgængelige MCP Servere

#### 🔹 [**`cor`**](cor/)
Dansk sprog- og ordregisterserver baseret på Det Centrale Ordregister (COR) og Dansk Sprognævn. Udstiller værktøjer til ordverifikation, ordspilssøgning (Wordle, Scrabble), stavefejlskontrol og grammatisk analyse med over 386.000 ordformer.

- **Server-fil:** [`cor/server.py`](cor/server.py)
- **Filer:** 5 filer (32.4 MB)
- **Vejledning:** Se [`cor/README.md`](cor/README.md) for detaljerede instruktioner og opsætning i Claude Desktop / Cursor.

### ⚡ Hurtig Start (Eksempel med `cor`)

1. Klon repositoriet:
   ```bash
   git clone https://git.p20.dev/christian/OpenDataMCP.git
   cd OpenDataMCP/cor
   ```
2. Installer MCP-biblioteket:
   ```bash
   pip install "mcp[cli]"
   ```
3. Tilføj til din Claude Desktop konfiguration (`claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "dansk-cor": {
         "command": "python",
         "args": ["/sti/til/OpenDataMCP/cor/server.py"]
       }
     }
   }
   ```

### 📜 Licenser & Kildeangivelse

- **COR MCP Server:** Creative Commons CC0 1.0 Universal (Det Centrale Ordregister / Dansk Sprognævn).
- **Webportal:** [opendata.p20.dev](https://opendata.p20.dev)

---

<a name="english"></a>
## 🇬🇧 English

Welcome to **OpenDataMCP**. This repository distributes ready-to-run **Model Context Protocol (MCP)** servers tailored for AI assistants, agents, and LLMs (Claude Desktop, Cursor, Antigravity, and compatible MCP hosts).

> **Type:** Production-ready MCP servers with pre-indexed SQLite databases  
> **Last synchronized:** `2026-10-22 18:47:51 UTC`  
> **Active MCP servers:** `1` (5 files, 32.4 MB)

### 📂 Directory Layout

Each MCP server resides in an isolated directory containing the server logic, automated tests, local database assets, and instructions:

```text
OpenDataMCP/
├── README.md               # Root bilingual documentation
├── mcp_manifest.json       # SHA-256 release manifest
├── cor/
│   ├── server.py           # MCP Server implementation
│   ├── test_tools.py       # Automated tool test suite
│   └── README.md           # Client configuration guide
```

### 🛠️ Server Registry

#### 🔹 [**`cor`**](cor/)
Danish language and lexicographic register server based on Det Centrale Ordregister (COR) and the Danish Language Council. Exposes AI tools for word verification, anagram/Wordle/Scrabble pattern matching, spell-checking, and grammar analysis across 386k+ words.

- **Server Entrypoint:** [`cor/server.py`](cor/server.py)
- **Payload:** 5 files (32.4 MB)
- **Guide:** Consult [`cor/README.md`](cor/README.md) for full tool definitions and client configs.

### ⚡ Quickstart (`cor` Server)

1. Clone the repository:
   ```bash
   git clone https://git.p20.dev/christian/OpenDataMCP.git
   cd OpenDataMCP/cor
   ```
2. Install dependencies:
   ```bash
   pip install "mcp[cli]"
   ```
3. Configure your MCP client (e.g. `claude_desktop_config.json`):
   ```json
   {
     "mcpServers": {
       "dansk-cor": {
         "command": "python",
         "args": ["/path/to/OpenDataMCP/cor/server.py"]
       }
     }
   }
   ```

### 📜 Licenses & Attribution

- **COR MCP Server:** Creative Commons CC0 1.0 Universal (Det Centrale Ordregister / Danish Language Council).
- **Web Portal:** [opendata.p20.dev](https://opendata.p20.dev)