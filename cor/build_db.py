import os
import sqlite3
import csv
import json
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(BASE_DIR, "cor.db")

def create_database():
    print(f"Opretter/overskriver SQLite-database: {DB_PATH}")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("PRAGMA synchronous = OFF;")
    cur.execute("PRAGMA journal_mode = MEMORY;")

    # 1. Tabel for alle godkendte ordformer (Scrabble / Wordfeud / Wordle)
    cur.execute("""
        CREATE TABLE words (
            word TEXT PRIMARY KEY,
            length INTEGER NOT NULL,
            is_wordle BOOLEAN NOT NULL DEFAULT 0,
            is_palindrome BOOLEAN NOT NULL DEFAULT 0
        ) WITHOUT ROWID;
    """)

    # 2. Tabel for lemmaer (grundformer) og deres ordklasser
    cur.execute("""
        CREATE TABLE lemmas (
            lemma TEXT PRIMARY KEY,
            pos TEXT NOT NULL,
            length INTEGER NOT NULL
        ) WITHOUT ROWID;
    """)

    # 3. Tabel for stavefejl og autoriserede rettelser (COR.SOEGEHJAELP)
    cur.execute("""
        CREATE TABLE typos (
            typo TEXT NOT NULL,
            correct_word TEXT NOT NULL,
            pos_tag TEXT,
            PRIMARY KEY (typo, correct_word)
        ) WITHOUT ROWID;
    """)

    # 4. Tabel for uregelmæssige verber
    cur.execute("""
        CREATE TABLE irregular_verbs (
            infinitive TEXT PRIMARY KEY,
            present TEXT NOT NULL,
            past TEXT NOT NULL,
            past_participle TEXT NOT NULL
        ) WITHOUT ROWID;
    """)

    # 5. Tabel for grammatiske kuriositeter og særkategorier
    cur.execute("""
        CREATE TABLE grammar_features (
            word TEXT NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            PRIMARY KEY (word, category)
        ) WITHOUT ROWID;
    """)

    conn.commit()
    return conn

def populate_words_and_lemmas(conn):
    cur = conn.cursor()
    print("Indlæser ordformer og grundformer...")

    # Hent palindromer til et opslagssæt
    palindromes_path = os.path.join(DATA_DIR, "cor_ordlister", "palindromer", "palindromer.txt")
    palindromes = set()
    if os.path.exists(palindromes_path):
        with open(palindromes_path, "r", encoding="utf-8") as f:
            palindromes = {line.strip().lower() for line in f if line.strip()}
    print(f"Palindromer fundet: {len(palindromes)}")

    # Indlæs Scrabble alle former
    scrabble_path = os.path.join(DATA_DIR, "cor_ordlister", "scrabble", "scrabble_alle_former.txt")
    if os.path.exists(scrabble_path):
        words_data = []
        with open(scrabble_path, "r", encoding="utf-8") as f:
            for line in f:
                w = line.strip().lower()
                if not w:
                    continue
                w_len = len(w)
                is_w = 1 if w_len == 5 else 0
                is_p = 1 if w in palindromes else 0
                words_data.append((w, w_len, is_w, is_p))

        print(f"Indsætter {len(words_data)} ord i 'words'...")
        cur.executemany("INSERT OR IGNORE INTO words (word, length, is_wordle, is_palindrome) VALUES (?, ?, ?, ?)", words_data)
        conn.commit()

    # Indlæs grundformer / lemmaer
    lemma_csv = os.path.join(DATA_DIR, "cor_ordlister", "grundformer", "grundformer_lemmaer.csv")
    if os.path.exists(lemma_csv):
        lemma_data = []
        with open(lemma_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                l = row["lemma"].strip().lower()
                pos = row["ordklasser"].strip()
                if l:
                    lemma_data.append((l, pos, len(l)))

        print(f"Indsætter {len(lemma_data)} grundformer i 'lemmas'...")
        cur.executemany("INSERT OR IGNORE INTO lemmas (lemma, pos, length) VALUES (?, ?, ?)", lemma_data)
        conn.commit()

def populate_typos(conn):
    cur = conn.cursor()
    typos_csv = os.path.join(DATA_DIR, "cor_ekstra", "stavefejl", "typiske_stavefejl_og_rettelser.csv")
    if os.path.exists(typos_csv):
        typo_data = []
        with open(typos_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                t = row["taste_stavefejl"].strip().lower()
                c = row["korrekt_form"].strip().lower()
                p = row.get("ordklasse", "").strip()
                if t and c:
                    typo_data.append((t, c, p))
        print(f"Indsætter {len(typo_data)} stavefejl i 'typos'...")
        cur.executemany("INSERT OR IGNORE INTO typos (typo, correct_word, pos_tag) VALUES (?, ?, ?)", typo_data)
        conn.commit()

def populate_grammar(conn):
    cur = conn.cursor()
    gram_dir = os.path.join(DATA_DIR, "cor_ekstra", "grammatik")
    kurio_dir = os.path.join(DATA_DIR, "cor_ekstra", "kuriositeter")

    # Uregelmæssige verber
    uv_csv = os.path.join(gram_dir, "uregelmaessige_verber.csv")
    if os.path.exists(uv_csv):
        uv_data = []
        with open(uv_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                inf = row["infinitiv"].strip().lower()
                pres = row["præsens"].strip().lower()
                past = row["præteritum"].strip().lower()
                part = row["perfektum_participium"].strip().lower()
                if inf:
                    uv_data.append((inf, pres, past, part))
        print(f"Indsætter {len(uv_data)} uregelmæssige verber...")
        cur.executemany("INSERT OR IGNORE INTO irregular_verbs VALUES (?, ?, ?, ?)", uv_data)

    # Simple kategorier
    categories = [
        (os.path.join(gram_dir, "substantiver_valgfrit_koen.txt"), "valgfrit_koen", "Fælleskøn eller intetkøn (en/et)"),
        (os.path.join(gram_dir, "plurale_tantum_kun_flertal.txt"), "plurale_tantum", "Findes kun i flertal"),
        (os.path.join(gram_dir, "singulare_tantum_kun_ental.txt"), "singulare_tantum", "Findes kun i ental"),
        (os.path.join(kurio_dir, "isogrammer_uden_gentagne_bogstaver.txt"), "isogram", "Alle bogstaver er unikke"),
        (os.path.join(kurio_dir, "paafolgende_dobbeltkonsonanter.txt"), "dobbeltkonsonanter", "Påfølgende dobbeltkonsonanter"),
        (os.path.join(kurio_dir, "q_uden_u.txt"), "q_uden_u", "Indeholder Q uden efterfølgende U"),
        (os.path.join(kurio_dir, "tre_ens_bogstaver_i_traek.txt"), "tre_ens_i_traek", "Tre ens bogstaver i træk"),
        (os.path.join(kurio_dir, "scrabble_svaere_korte_ord.txt"), "scrabble_svaere_korte", "Korte ord med C, X, Z, W, Q")
    ]

    gf_data = []
    for filepath, cat_name, note in categories:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                for line in f:
                    w = line.strip().lower()
                    if w:
                        gf_data.append((w, cat_name, note))

    # Ordklasse kamæleoner (CSV med flere ordklasser)
    kam_csv = os.path.join(gram_dir, "ordklasse_kamaeleoner.csv")
    if os.path.exists(kam_csv):
        with open(kam_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                w = row["lemma"].strip().lower()
                ok = row.get("ordklasser", "")
                antal = row.get("antal_ordklasser", "")
                if w:
                    gf_data.append((w, "ordklasse_kamaeleon", f"{antal} ordklasser: {ok}"))

    # Semordnilaps (venderord)
    sem_csv = os.path.join(kurio_dir, "semordnilaps_venderord.csv")
    if os.path.exists(sem_csv):
        with open(sem_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                w1 = row.get("ord1", "").strip().lower()
                w2 = row.get("ord2", "").strip().lower()
                if w1 and w2:
                    gf_data.append((w1, "semordnilap", f"Omvendt: {w2}"))

    print(f"Indsætter {len(gf_data)} grammatiske og kuriositets-træk...")
    cur.executemany("INSERT OR IGNORE INTO grammar_features VALUES (?, ?, ?)", gf_data)
    conn.commit()

def create_indexes(conn):
    cur = conn.cursor()
    print("Opretter optimerede indeks...")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_words_length ON words(length);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_words_wordle ON words(is_wordle);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_words_pal ON words(is_palindrome);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_lemmas_pos ON lemmas(pos);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_typos_typo ON typos(typo);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_grammar_cat ON grammar_features(category);")
    conn.commit()

def main():
    start = time.time()
    conn = create_database()
    populate_words_and_lemmas(conn)
    populate_typos(conn)
    populate_grammar(conn)
    create_indexes(conn)
    conn.close()
    elapsed = time.time() - start
    print(f"Færdig! SQLite-databasen er klar på {elapsed:.2f} sekunder.")

if __name__ == "__main__":
    main()
