import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Optional


class PaperTracker:
    """SQLite-based tracker for research paper metadata and control."""
    
    def __init__(self, db_path: str = "papers.db"):
        self.db_path = Path(db_path)
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with papers table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS papers (
                    paper_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    authors TEXT,
                    abstract TEXT,
                    journal TEXT,
                    pub_date TEXT,
                    source_type TEXT NOT NULL,
                    pmc_id TEXT,
                    pmid TEXT,
                    doi TEXT,
                    keywords TEXT,
                    last_updated TEXT NOT NULL,
                    processed BOOLEAN DEFAULT FALSE
                )
            """)
            conn.commit()
    
    def add_paper(self, paper_data: Dict) -> bool:
        """Add or update paper metadata."""
        paper_data['last_updated'] = datetime.now().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO papers 
                    (paper_id, title, authors, abstract, journal, pub_date, 
                     source_type, pmc_id, pmid, doi, keywords, last_updated, processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    paper_data.get('paper_id'),
                    paper_data.get('title'),
                    json.dumps(paper_data.get('authors', [])),
                    paper_data.get('abstract'),
                    paper_data.get('journal'),
                    paper_data.get('pub_date'),
                    paper_data.get('source_type'),
                    paper_data.get('pmc_id'),
                    paper_data.get('pmid'),
                    paper_data.get('doi'),
                    json.dumps(paper_data.get('keywords', [])),
                    paper_data['last_updated'],
                    paper_data.get('processed', False)
                ))
                conn.commit()
                return True
            except sqlite3.Error as e:
                print(f"Error adding paper: {e}")
                return False
    
    def get_stored_ids(self, source_type: Optional[str] = None) -> Set[str]:
        """Get all stored paper IDs, optionally filtered by source type."""
        with sqlite3.connect(self.db_path) as conn:
            if source_type:
                cursor = conn.execute(
                    "SELECT paper_id FROM papers WHERE source_type = ?", 
                    (source_type,)
                )
            else:
                cursor = conn.execute("SELECT paper_id FROM papers")
            return {row[0] for row in cursor.fetchall()}
    
    def is_paper_stored(self, paper_id: str) -> bool:
        """Check if paper is already stored."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM papers WHERE paper_id = ? LIMIT 1", 
                (paper_id,)
            )
            return cursor.fetchone() is not None
    
    def mark_processed(self, paper_id: str) -> bool:
        """Mark paper as processed in vector database."""
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    "UPDATE papers SET processed = TRUE WHERE paper_id = ?",
                    (paper_id,)
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False
    
    def get_unprocessed_papers(self, limit: Optional[int] = None) -> List[Dict]:
        """Get papers that haven't been processed into vector DB yet."""
        with sqlite3.connect(self.db_path) as conn:
            query = "SELECT * FROM papers WHERE processed = FALSE"
            if limit:
                query += f" LIMIT {limit}"
            
            cursor = conn.execute(query)
            columns = [desc[0] for desc in cursor.description]
            
            papers = []
            for row in cursor.fetchall():
                paper = dict(zip(columns, row))
                # Parse JSON fields
                paper['authors'] = json.loads(paper['authors']) if paper['authors'] else []
                paper['keywords'] = json.loads(paper['keywords']) if paper['keywords'] else []
                papers.append(paper)
            
            return papers
    
    def get_stats(self) -> Dict:
        """Get database statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN processed = TRUE THEN 1 END) as processed,
                    COUNT(CASE WHEN source_type = 'pmc' THEN 1 END) as pmc_papers,
                    COUNT(CASE WHEN source_type = 'local' THEN 1 END) as local_papers
                FROM papers
            """)
            row = cursor.fetchone()
            return {
                'total_papers': row[0],
                'processed_papers': row[1],
                'pmc_papers': row[2],
                'local_papers': row[3],
                'unprocessed_papers': row[0] - row[1]
            }