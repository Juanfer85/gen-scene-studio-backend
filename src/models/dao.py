import sqlite3, time, json

def init_db(conn: sqlite3.Connection):
    cur = conn.cursor()
    # Create table with new schema if it doesn't exist
    cur.execute("""CREATE TABLE IF NOT EXISTS jobs(
        job_id TEXT PRIMARY KEY,
        state TEXT,
        progress INTEGER,
        created_at INTEGER,
        job_type TEXT DEFAULT 'unknown',
        payload TEXT DEFAULT '{}'
    )""")
    
    # Simple migration: Check if columns exist, if not add them
    try:
        cur.execute("SELECT job_type FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        print("⚠️ Migrating jobs table: adding job_type")
        cur.execute("ALTER TABLE jobs ADD COLUMN job_type TEXT DEFAULT 'unknown'")
    
    try:
        cur.execute("SELECT payload FROM jobs LIMIT 1")
    except sqlite3.OperationalError:
        print("⚠️ Migrating jobs table: adding payload")
        cur.execute("ALTER TABLE jobs ADD COLUMN payload TEXT DEFAULT '{}'")

    cur.execute("""CREATE TABLE IF NOT EXISTS renders(
        job_id TEXT,
        item_id TEXT,
        hash TEXT,
        quality TEXT,
        url TEXT,
        status TEXT,
        PRIMARY KEY(job_id, item_id)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS assets_cache(
        hash TEXT PRIMARY KEY,
        url TEXT,
        created_at INTEGER
    )""")
    conn.commit()

def upsert_job(conn, job_id:str, state:str, progress:int, job_type:str='unknown', payload:dict=None):
    if payload is None: payload = {}
    payload_json = json.dumps(payload)
    
    cur = conn.cursor()
    # Check if job exists to preserve created_at if updating
    cur.execute("SELECT created_at FROM jobs WHERE job_id = ?", (job_id,))
    row = cur.fetchone()
    
    if row:
        # Update
        cur.execute(
            "UPDATE jobs SET state=?, progress=?, job_type=?, payload=? WHERE job_id=?",
            (state, progress, job_type, payload_json, job_id)
        )
    else:
        # Insert
        cur.execute(
            "INSERT INTO jobs(job_id,state,progress,created_at,job_type,payload) VALUES(?,?,?,?,?,?)",
            (job_id, state, progress, int(time.time()), job_type, payload_json)
        )
    conn.commit()

def update_job_state(conn, job_id:str, state:str, progress:int|None=None):
    cur = conn.cursor()
    if progress is None:
        cur.execute("UPDATE jobs SET state=? WHERE job_id=?", (state, job_id))
    else:
        cur.execute("UPDATE jobs SET state=?, progress=? WHERE job_id=?", (state, progress, job_id))
    conn.commit()

def insert_or_update_render(conn, job_id:str, item_id:str, h:str, quality:str, url:str|None, status:str):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO renders(job_id,item_id,hash,quality,url,status) VALUES(?,?,?,?,?,?) "
        "ON CONFLICT(job_id,item_id) DO UPDATE SET hash=excluded.hash, quality=excluded.quality, url=excluded.url, status=excluded.status",
        (job_id, item_id, h, quality, url, status)
    )
    conn.commit()

def list_job_outputs(conn, job_id:str):
    cur = conn.cursor()
    cur.execute("SELECT item_id as id, quality, hash, url, status FROM renders WHERE job_id=? ORDER BY item_id", (job_id,))
    columns = [column[0] for column in cur.description]
    results = []
    for row in cur.fetchall():
        results.append(dict(zip(columns, row)))
    return results

def get_cached_asset(conn, h:str) -> str|None:
    cur = conn.cursor()
    cur.execute("SELECT url FROM assets_cache WHERE hash=?", (h,))
    row = cur.fetchone()
    return row[0] if row else None

def set_cached_asset(conn, h:str, url:str):
    cur = conn.cursor()
    cur.execute("INSERT OR REPLACE INTO assets_cache(hash,url,created_at) VALUES(?,?,?)",
                (h, url, int(time.time())))
    conn.commit()