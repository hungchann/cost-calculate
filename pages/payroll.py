import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sqlite3
import os

# --- App Configuration ---
st.set_page_config(layout="wide", page_title="IT Payroll Manager", page_icon="💼")

# Database setup
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "payroll.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)    

def init_db():
    """Initialize the database with necessary tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS freelancers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        nationality TEXT NOT NULL,
        gross_payment REAL NOT NULL,
        tax_rate REAL NOT NULL,
        tax_amount REAL NOT NULL,
        net_payment REAL NOT NULL
    )
    ''')
    conn.commit()
    conn.close()

def add_freelancer(name, nationality, gross_payment, tax_rate, tax_amount, net_payment):
    """Add a new freelancer to the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        "INSERT INTO freelancers (name, nationality, gross_payment, tax_rate, tax_amount, net_payment) VALUES (?, ?, ?, ?, ?, ?)",
        (name, nationality, gross_payment, tax_rate, tax_amount, net_payment)
    )
    conn.commit()
    conn.close()
    
def get_all_freelancers():
    """Retrieve all freelancers from the database"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM freelancers", conn)
    conn.close()
    if not df.empty:
        # Format tax_rate as percentage string for display
        df['tax_rate'] = df['tax_rate'].apply(lambda x: f"{int(x*100)}%")
    return df

def delete_freelancer(freelancer_id):
    """Delete a freelancer from the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM freelancers WHERE id = ?", (freelancer_id,))
    conn.commit()
    result = c.rowcount > 0  # Returns True if a row was deleted
    conn.close()
    return result

def update_freelancer(freelancer_id, name, nationality, gross_payment, tax_rate, tax_amount, net_payment):
    """Update an existing freelancer's information"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """UPDATE freelancers 
           SET name = ?, nationality = ?, gross_payment = ?, tax_rate = ?, 
               tax_amount = ?, net_payment = ?
           WHERE id = ?""",
        (name, nationality, gross_payment, tax_rate, tax_amount, net_payment, freelancer_id)
    )
    conn.commit()
    result = c.rowcount > 0  # Returns True if a row was updated
    conn.close()
    return result

def get_freelancer_by_id(freelancer_id):
    """Get a single freelancer by ID"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM freelancers WHERE id = ?", (freelancer_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        # Convert to dictionary with column names
        columns = ['id', 'name', 'nationality', 'gross_payment', 'tax_rate', 'tax_amount', 'net_payment']
        return dict(zip(columns, row))
    return None

# Initialize database
init_db()

st.title("💼 Freelancer Payroll Manager")

# Create tabs for better organization
tab1, tab2 = st.tabs(["Add Freelancer", "Manage Freelancers"])

# Tab 1: Add Freelancer
with tab1:
    st.subheader("➕ Add Freelancer")
    with st.form("freelancer_form"):
        name = st.text_input("Full Name")
        nationality = st.selectbox("Nationality", ["Vietnamese", "Foreign"])
        monthly_payment = st.number_input("Payment Amount (VND)", step=100000)
        submit = st.form_submit_button("Add")

        if submit:
            tax_rate = 0.10 if nationality == "Vietnamese" else 0.20
            tax_amount = monthly_payment * tax_rate
            net_payment = monthly_payment - tax_amount
            add_freelancer(
                name=name,
                nationality=nationality,
                gross_payment=monthly_payment,
                tax_rate=tax_rate,
                tax_amount=tax_amount,
                net_payment=net_payment
            )
            st.success(f"Freelancer {name} added.")
            # Force a rerun to update the data display
            st.experimental_rerun()

# Tab 2: Manage Freelancers
with tab2:
    st.subheader("📊 Payroll Summary")
    
    # Always fetch the latest freelancer data
    freelancers_df = get_all_freelancers()
    
    if not freelancers_df.empty:
        # Add action buttons for each row
        # We'll use two approaches:
        # 1. For deletion: Add a delete button column
        # 2. For editing: Add an edit button column
        
        # Handle deletion
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write("Select freelancers to manage:")
        with col2:
            if st.button("Refresh Data"):
                st.experimental_rerun()
        
        # Display the dataframe
        st.dataframe(freelancers_df)
        
        # Create selection for editing or deleting
        freelancer_options = freelancers_df[['id', 'name']].copy()
        freelancer_options['display'] = freelancer_options['id'].astype(str) + ' - ' + freelancer_options['name']
        
        selected_id = st.selectbox(
            "Select freelancer to edit or delete:",
            options=freelancer_options['id'].tolist(),
            format_func=lambda x: freelancer_options[freelancer_options['id'] == x]['display'].iloc[0]
        )
        
        # Get the selected freelancer's data
        if selected_id:
            freelancer = get_freelancer_by_id(selected_id)
            if freelancer:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Edit Freelancer")
                    with st.form(key="edit_form"):
                        edit_name = st.text_input("Name", value=freelancer['name'])
                        edit_nationality = st.selectbox(
                            "Nationality", 
                            ["Vietnamese", "Foreign"],
                            index=0 if freelancer['nationality'] == "Vietnamese" else 1
                        )
                        edit_payment = st.number_input(
                            "Gross Payment (VND)", 
                            value=float(freelancer['gross_payment']),
                            step=100000.0
                        )
                        
                        # Recalculate tax when payment or nationality changes
                        edit_tax_rate = 0.10 if edit_nationality == "Vietnamese" else 0.20
                        edit_tax_amount = edit_payment * edit_tax_rate
                        edit_net_payment = edit_payment - edit_tax_amount
                        
                        st.write(f"Tax Rate: {int(edit_tax_rate * 100)}%")
                        st.write(f"Tax Amount: {edit_tax_amount:,.0f} VND")
                        st.write(f"Net Payment: {edit_net_payment:,.0f} VND")
                        
                        submit_edit = st.form_submit_button("Update Freelancer")
                        
                        if submit_edit:
                            if update_freelancer(
                                selected_id,
                                edit_name,
                                edit_nationality,
                                edit_payment,
                                edit_tax_rate,
                                edit_tax_amount,
                                edit_net_payment
                            ):
                                st.success(f"Updated {edit_name}'s information.")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to update. Please try again.")
                
                with col2:
                    st.subheader("Delete Freelancer")
                    st.write(f"Selected: **{freelancer['name']}**")
                    st.write(f"Gross Payment: {freelancer['gross_payment']:,.0f} VND")
                    st.write(f"Tax Rate: {int(freelancer['tax_rate'] * 100)}%")
                    
                    # Confirm deletion
                    if st.button("🗑️ Delete this freelancer", key=f"delete_{selected_id}"):
                        confirm = st.checkbox("Confirm deletion")
                        if confirm:
                            if delete_freelancer(selected_id):
                                st.success(f"Freelancer {freelancer['name']} has been deleted.")
                                st.experimental_rerun()
                            else:
                                st.error("Failed to delete. Please try again.")
        
        # Export options
        st.subheader("Export Options")
        csv = freelancers_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV Report", csv, "freelancer_payroll.csv", "text/csv")
    else:
        st.info("No freelancers added yet.")

# Add helpful information
with st.expander("💡 Understanding Payroll Tax Rates"):
    st.markdown("""
    ### Tax Rate Information
    
    - **Vietnamese Freelancers**: 10% Personal Income Tax (PIT)
    - **Foreign Freelancers**: 20% Personal Income Tax (PIT)
    
    These are simplified rates for demonstration purposes. Actual tax rates may vary based on:
    - Income thresholds
    - Tax residency status
    - Applicable tax treaties
    - Other deductions and exemptions
    
    Always consult with a tax professional for accurate tax advice.
    """)

