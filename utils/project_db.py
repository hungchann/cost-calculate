import sqlite3
import os
import pandas as pd
from datetime import datetime

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'project_costs.db')

# Ensure data directory exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    """Initialize the database schema if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create projects table if not exists
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        upfront_payment REAL NOT NULL,
        monthly_maintenance REAL NOT NULL,
        maintenance_months INTEGER NOT NULL,
        other_revenue REAL NOT NULL,
        target_margin REAL NOT NULL,
        freelancer_allocation REAL NOT NULL,
        internal_staff_allocation REAL NOT NULL,
        tech_infra_allocation REAL NOT NULL,
        admin_allocation REAL NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    conn.commit()
    conn.close()

def save_project(project_data):
    """Save a project to the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    INSERT INTO projects (
        name, upfront_payment, monthly_maintenance, maintenance_months, 
        other_revenue, target_margin, freelancer_allocation, 
        internal_staff_allocation, tech_infra_allocation, admin_allocation
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        project_data["name"],
        project_data["upfront_payment"],
        project_data["monthly_maintenance"],
        project_data["maintenance_months"],
        project_data["other_revenue"],
        project_data["target_margin"],
        project_data["freelancer_allocation"],
        project_data["internal_staff_allocation"],
        project_data["tech_infra_allocation"],
        project_data["admin_allocation"]
    ))
    
    conn.commit()
    last_id = cursor.lastrowid
    conn.close()
    return last_id

def get_all_projects():
    """Retrieve all projects from database"""
    conn = sqlite3.connect(DB_PATH)
    
    # Use pandas to read from SQLite
    df = pd.read_sql_query("SELECT * FROM projects ORDER BY created_at DESC", conn)
    conn.close()
    
    if df.empty:
        return []
    
    # Convert DataFrame to list of dictionaries
    projects = df.to_dict('records')
    return projects

def get_project_by_id(project_id):
    """Retrieve a specific project by ID"""
    conn = sqlite3.connect(DB_PATH)
    
    query = "SELECT * FROM projects WHERE id = ?"
    df = pd.read_sql_query(query, conn, params=[project_id])
    conn.close()
    
    if df.empty:
        return None
    
    return df.iloc[0].to_dict()

def update_project(project_id, project_data):
    """Update an existing project"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    UPDATE projects SET
        name = ?, 
        upfront_payment = ?, 
        monthly_maintenance = ?, 
        maintenance_months = ?, 
        other_revenue = ?, 
        target_margin = ?, 
        freelancer_allocation = ?, 
        internal_staff_allocation = ?, 
        tech_infra_allocation = ?, 
        admin_allocation = ?
    WHERE id = ?
    ''', (
        project_data["name"],
        project_data["upfront_payment"],
        project_data["monthly_maintenance"],
        project_data["maintenance_months"],
        project_data["other_revenue"],
        project_data["target_margin"],
        project_data["freelancer_allocation"],
        project_data["internal_staff_allocation"],
        project_data["tech_infra_allocation"],
        project_data["admin_allocation"],
        project_id
    ))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

def delete_project(project_id):
    """Delete a project from the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    
    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success
