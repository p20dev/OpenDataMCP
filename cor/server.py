"""
COR MCP Server
--------------
Model Context Protocol server for Det Centrale Ordregister (COR) og Dansk Sprognævn.
Udstiller værktøjer til ordverifikation, ordbogssøgning (Wordle/Scrabble/regex),
stavekontrol (COR.SOEGEHJAELP) og grammatiske særtræk.
"""

import os
import re
import sqlite3
from typing import Optional, List, Dict, Any
from mcp.server.mcpserver import MCPServer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "cor.db")

server = MCPServer(
    name="opendata-cor",
    version="1.0.0",
    description="Officiel dansk sprog- og ordregisterserver baseret på COR (Det Centrale Ordregister, Dansk Sprognævn)."
)

def get_db_connection():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Databasen '{DB_PATH}' blev ikke fundet. Kør build_db.py først.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@server.tool(
    name="lookup_word",
    description="Slå et dansk ord op i COR. Undersøger om ordet er en godkendt form, henter grundform (lemma), ordklasse(r), grammatiske særtræk og bøjningsstatus."
)
def lookup_word(word: str) -> Dict[str, Any]:
    """
    Slår et ord op.
    :param word: Ordet der skal slås op (f.eks. 'cykler', 'betydning', 'gik').
    """
    clean = word.strip().lower()
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Tjek om ordet findes som gyldig godkendt form
    cur.execute("SELECT word, length, is_wordle, is_palindrome FROM words WHERE word = ?", (clean,))
    word_row = cur.fetchone()

    # 2. Tjek om ordet er et lemma (grundform)
    cur.execute("SELECT lemma, pos, length FROM lemmas WHERE lemma = ?", (clean,))
    lemma_row = cur.fetchone()

    # 3. Tjek grammatiske særtræk
    cur.execute("SELECT category, note FROM grammar_features WHERE word = ?", (clean,))
    grammar_rows = cur.fetchall()
    features = [{"category": r["category"], "note": r["note"]} for r in grammar_rows]

    # 4. Tjek uregelmæssigt verbum
    cur.execute("SELECT * FROM irregular_verbs WHERE infinitive = ? OR present = ? OR past = ? OR past_participle = ?",
                (clean, clean, clean, clean))
    verb_row = cur.fetchone()
    verb_info = None
    if verb_row:
        verb_info = {
            "infinitiv": verb_row["infinitive"],
            "praesens": verb_row["present"],
            "praeteritum": verb_row["past"],
            "perfektum_participium": verb_row["past_participle"]
        }

    # 5. Tjek eventuel stavefejl
    cur.execute("SELECT correct_word, pos_tag FROM typos WHERE typo = ?", (clean,))
    typo_rows = cur.fetchall()
    corrections = [{"korrekt_form": r["correct_word"], "ordklasse": r["pos_tag"]} for r in typo_rows]

    conn.close()

    exists = word_row is not None or lemma_row is not None

    return {
        "word": clean,
        "is_valid_danish_word": exists,
        "is_lemma": lemma_row is not None,
        "ordklasser": lemma_row["pos"].split("|") if lemma_row else [],
        "length": len(clean),
        "is_wordle_eligible": bool(word_row["is_wordle"]) if word_row else (len(clean) == 5),
        "is_palindrome": bool(word_row["is_palindrome"]) if word_row else False,
        "grammar_features": features,
        "irregular_verb": verb_info,
        "known_typo_corrections": corrections if not exists and corrections else corrections
    }

@server.tool(
    name="find_words",
    description="Søg efter danske ord med avancerede filtre: længde, regex, vildtegn (* eller ?), ordklasse eller kun Wordle/palindromer."
)
def find_words(
    pattern: Optional[str] = None,
    length: Optional[int] = None,
    pos: Optional[str] = None,
    is_wordle: Optional[bool] = None,
    is_palindrome: Optional[bool] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Søger i COR ordregisteret.
    :param pattern: Mønster til søgning. Kan indeholde '?' (ét bogstav), '*' (nul eller flere) eller regex (f.eks. '^b.*ing$').
    :param length: Nøjagtig ordlængde (f.eks. 5 til Wordle).
    :param pos: Filtrér efter ordklasse for grundformer (f.eks. 'sb', 'vb', 'adj').
    :param is_wordle: Filtrér specifikt på 5-bogstavsord.
    :param is_palindrome: Kun palindromer (sandt/falsk).
    :param limit: Maksimalt antal resultater (standard: 50, maks 500).
    """
    max_limit = min(limit, 500)
    conn = get_db_connection()
    cur = conn.cursor()

    conditions = []
    params = []

    # Hvis pos er angivet, søger vi i lemmas, ellers i words
    search_lemmas = bool(pos)

    table = "lemmas" if search_lemmas else "words"
    word_col = "lemma" if search_lemmas else "word"

    if length is not None:
        conditions.append(f"{table}.length = ?")
        params.append(length)

    if is_wordle:
        conditions.append(f"{table}.length = 5")

    if is_palindrome and not search_lemmas:
        conditions.append("words.is_palindrome = 1")

    if pos:
        # pos kan være f.eks. 'sb' eller 'vb'
        conditions.append(f"(lemmas.pos = ? OR lemmas.pos LIKE ? OR lemmas.pos LIKE ? OR lemmas.pos LIKE ?)")
        params.extend([pos, f"{pos}|%", f"%|{pos}", f"%|{pos}|%"])

    # Regex / Pattern konvertering hvis nødvendigt
    use_python_regex = False
    compiled_regex = None

    if pattern:
        clean_pat = pattern.strip().lower()
        # Hvis pattern indeholder regex specialtegn ud over ? og *
        if any(c in clean_pat for c in ["^", "$", "[", "]", "(", ")", "+", "{", "}", "|", "\\"]):
            use_python_regex = True
            compiled_regex = re.compile(clean_pat)
        elif "*" in clean_pat or "?" in clean_pat:
            # Konverter simpelt glob mønster til SQL LIKE
            sql_like = clean_pat.replace("*", "%").replace("?", "_")
            conditions.append(f"{table}.{word_col} LIKE ?")
            params.append(sql_like)
        else:
            # Eksakt eller delstreng
            conditions.append(f"{table}.{word_col} LIKE ?")
            params.append(f"%{clean_pat}%")

    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"SELECT {word_col} as ord, length FROM {table} {where_clause} ORDER BY length ASC, ord ASC"

    # Hvis vi bruger python regex filtrerer vi bagefter, ellers begrænser vi direkte i SQL
    if not use_python_regex:
        sql += f" LIMIT {max_limit}"

    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        w = r["ord"]
        if use_python_regex and compiled_regex:
            if not compiled_regex.search(w):
                continue
        results.append(w)
        if len(results) >= max_limit:
            break

    return {
        "total_matches_returned": len(results),
        "limit": max_limit,
        "filter": {
            "pattern": pattern,
            "length": length,
            "pos": pos,
            "is_wordle": is_wordle,
            "is_palindrome": is_palindrome
        },
        "words": results
    }

@server.tool(
    name="check_spelling",
    description="Kontrollér et ord eller slå typiske danske stavefejl op mod COR.SOEGEHJAELP (Dansk Sprognævns officielle samling af almindelige fejl og rettelser)."
)
def check_spelling(word: str) -> Dict[str, Any]:
    """
    Tjekker stavemåde og finder officielle rettelser.
    :param word: Ordet der skal kontrolleres (f.eks. 'accellerere', 'majestætisk', 'linje').
    """
    clean = word.strip().lower()
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Tjek om ordet findes direkte som godkendt ord
    cur.execute("SELECT word FROM words WHERE word = ?", (clean,))
    is_valid = cur.fetchone() is not None

    # 2. Slå op i stavefejlsdatabasen
    cur.execute("SELECT correct_word, pos_tag FROM typos WHERE typo = ?", (clean,))
    typo_rows = cur.fetchall()

    conn.close()

    suggestions = []
    for r in typo_rows:
        suggestions.append({
            "korrekt_form": r["correct_word"],
            "ordklasse": r["pos_tag"]
        })

    is_known_typo = len(suggestions) > 0

    status = "korrekt" if is_valid else ("kendt_tastefejl" if is_known_typo else "ukendt_ord")

    return {
        "input_word": clean,
        "status": status,
        "is_officially_approved": is_valid,
        "is_known_spelling_error": is_known_typo,
        "official_corrections": suggestions
    }

@server.tool(
    name="grammar_features",
    description="Udforsk grammatiske særtræk i dansk fra COR: uregelmæssige verber, substantiver med valgfrit køn (en/et), plurale tantum (kun flertal), singulare tantum (kun ental) og ordklasse-kamæleoner."
)
def grammar_features(
    category: str,
    query: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    Slår grammatiske særkategorier op.
    :param category: Kategori at slå op. Gyldige værdier:
                     'uregelmaessige_verber' (bøjningsrækker),
                     'valgfrit_koen' (en/et substantiver),
                     'plurale_tantum' (kun flertal),
                     'singulare_tantum' (kun ental),
                     'ordklasse_kamaeleon' (ord i 3+ ordklasser),
                     'isogram' (unikke bogstaver),
                     'semordnilap' (venderord),
                     'q_uden_u' (ord med q uden u).
    :param query: Valgfri søgestreng til at filtrere i ord eller bøjninger.
    :param limit: Maksimalt antal resultater (standard: 50, maks: 200).
    """
    cat = category.strip().lower()
    max_limit = min(limit, 200)
    conn = get_db_connection()
    cur = conn.cursor()

    if cat == "uregelmaessige_verber":
        sql = "SELECT infinitive, present, past, past_participle FROM irregular_verbs"
        params = []
        if query:
            q = f"%{query.strip().lower()}%"
            sql += " WHERE infinitive LIKE ? OR present LIKE ? OR past LIKE ? OR past_participle LIKE ?"
            params.extend([q, q, q, q])
        sql += f" LIMIT {max_limit}"
        cur.execute(sql, params)
        rows = cur.fetchall()
        results = [
            {
                "infinitiv": r["infinitive"],
                "praesens": r["present"],
                "praeteritum": r["past"],
                "perfektum_participium": r["past_participle"]
            }
            for r in rows
        ]
    else:
        sql = "SELECT word, category, note FROM grammar_features WHERE category = ?"
        params = [cat]
        if query:
            sql += " AND word LIKE ?"
            params.append(f"%{query.strip().lower()}%")
        sql += f" LIMIT {max_limit}"
        cur.execute(sql, params)
        rows = cur.fetchall()
        results = [{"word": r["word"], "note": r["note"]} for r in rows]

    conn.close()

    return {
        "category": cat,
        "query": query,
        "count": len(results),
        "results": results
    }

if __name__ == "__main__":
    # Kør serveren over standard stdio transport
    server.run(transport="stdio")
