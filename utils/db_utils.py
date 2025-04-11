import sqlite3
import pandas as pd
import os
from pathlib import Path

# Define database path
DB_PATH = Path(__file__).parent.parent / "data" / "bookkeeping.db"

def init_db():
    """Initialize the database and create tables if they don't exist"""
    # Ensure the data directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create transactions table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            vnd_amount REAL NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            reference TEXT,
            exchange_rate REAL DEFAULT 1.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def save_transaction(transaction_data):
    """Save a new transaction to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO transactions
        (date, type, amount, currency, vnd_amount, description, category, reference, exchange_rate)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        transaction_data["date"],
        transaction_data["type"],
        transaction_data["amount"],
        transaction_data["currency"],
        transaction_data["vnd_amount"],
        transaction_data["description"],
        transaction_data["category"],
        transaction_data["reference"],
        transaction_data["exchange_rate"]
    ))
    
    conn.commit()
    conn.close()

def update_transaction(transaction_id, transaction_data):
    """Update an existing transaction in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE transactions
        SET date = ?, type = ?, amount = ?, currency = ?, 
            vnd_amount = ?, description = ?, category = ?, 
            reference = ?, exchange_rate = ?
        WHERE id = ?
    ''', (
        transaction_data["date"],
        transaction_data["type"],
        transaction_data["amount"],
        transaction_data["currency"],
        transaction_data["vnd_amount"],
        transaction_data["description"],
        transaction_data["category"],
        transaction_data["reference"],
        transaction_data["exchange_rate"],
        transaction_id
    ))
    
    conn.commit()
    conn.close()

def delete_transaction(transaction_id):
    """Delete a transaction from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    
    conn.commit()
    conn.close()

def get_all_transactions():
    """Get all transactions from the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM transactions ORDER BY date DESC
    ''')
    
    rows = cursor.fetchall()
    transactions = [dict(row) for row in rows]
    
    conn.close()
    return transactions

def get_filtered_transactions(types=None, categories=None):
    """Get transactions filtered by type and/or category"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if types and len(types) > 0:
        placeholders = ', '.join('?' for _ in types)
        query += f" AND type IN ({placeholders})"
        params.extend(types)
    
    if categories and len(categories) > 0:
        placeholders = ', '.join('?' for _ in categories)
        query += f" AND category IN ({placeholders})"
        params.extend(categories)
    
    query += " ORDER BY date DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    transactions = [dict(row) for row in rows]
    
    conn.close()
    return transactions

def export_to_dataframe():
    """Export all transactions to a pandas DataFrame"""
    conn = sqlite3.connect(DB_PATH)
    query = "SELECT * FROM transactions ORDER BY date DESC"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df
