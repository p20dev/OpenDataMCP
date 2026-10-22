# Dansk COR MCP Server (Model Context Protocol)

En officiel og lynhurtig **Model Context Protocol (MCP)** server for det danske sprog baseret på datasættene fra [Det Centrale Ordregister (COR)](https://ordregister.dk/) og Dansk Sprognævn i [OpenData](https://opendata.p20.dev).

Serveren gør det muligt for AI-agenter (såsom Claude Desktop, Antigravity, Cursor eller andre MCP-kompatible klienter) at udføre præcise ordbogsopslag, mønstersøgning (Wordle, krydsord, Scrabble), officiel stavekontrol og grammatisk analyse.

---

## ⚡ Funktioner og Værktøjer (Tools)

Serveren udstiller 4 specialiserede værktøjer:

| Værktøj | Beskrivelse | Eksempel på parametre |
| :--- | :--- | :--- |
| `lookup_word` | Slår et dansk ord op. Afgør om ordet er godkendt, henter ordklasse(r), grundform (lemma), køn, uregelmæssige bøjningsformer og stavefejlsrettelser. | `{"word": "cykler"}` |
| `find_words` | Fleksibel ordsøger med støtte for vildtegn (`*`, `?`), regex, ordlængde, ordklasse (`sb`, `vb`, `adj` osv.), Wordle-filtre og palindromer. | `{"pattern": "k?tte", "is_wordle": true}` |
| `check_spelling` | Kontrollerer et ord mod COR.SOEGEHJAELP (Dansk Sprognævns officielle samling af almindelige fejl og tastefejl) og returnerer korrekte autoriserede former. | `{"word": "accellerere"}` |
| `grammar_features` | Slår grammatiske særtræk op: uregelmæssige verber, substantiver med valgfrit køn (*en/et*), *plurale tantum* (kun flertal), *singulare tantum* (kun ental) og ordklasse-kamæleoner. | `{"category": "valgfrit_koen", "query": "folie"}` |

---

## 📦 Forudsætninger & Installation

Serveren kører på Python 3.10+ og anvender den officielle `mcp` pakke samt en optimeret SQLite-database (`cor.db`).

### 1. Installer afhængigheder
```bash
pip install "mcp[cli]"
```

### 2. Generer SQLite-databasen
Databasen opbygges lynhurtigt (< 2 sekunder) direkte fra OpenData-repositoriets datalister:
```bash
python mcp/cor/build_db.py
```
Dette genererer `mcp/cor/cor.db` med over **386.000 ordformer**, 61.000 lemmaer og knap 9.000 registrerede stavefejl.

### 3. Kør automatiseret test
```bash
python mcp/cor/test_tools.py
```

---

## 🚀 Konfiguration i MCP-klienter

### Claude Desktop
Tilføj følgende til din `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "dansk-cor": {
      "command": "python",
      "args": [
        "/sti/til/OpenData/mcp/cor/server.py"
      ]
    }
  }
}
```

> **Tip:** Udskift `/sti/til/OpenData/` med den faktiske absolutte sti til repositoriet på dit system.

### Antigravity / Cursor
Tilføj serveren under MCP-indstillinger som en `stdio`-server:
- **Command**: `python` (eller sti til dit Python-miljø)
- **Args**: `["<sti-til-OpenData>/mcp/cor/server.py"]`

---

## 🌐 Data og Licens
- Data stammer fra **Det Centrale Ordregister (COR)** og **COR.SOEGEHJAELP** udgivet af Dansk Sprognævn under **CC0 1.0 Universal** (Public Domain).
- Webportal og datadokumentation: [opendata.p20.dev](https://opendata.p20.dev)
