import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import os

# Add the parent directory to sys.path to allow relative imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from utils.project_db import init_db, save_project, get_all_projects, get_project_by_id, update_project, delete_project

# --- App Configuration ---
st.set_page_config(layout="wide", page_title="IT Project Cost Calculator")

# Initialize database
init_db()

st.title("📊 IT Project Cost Calculator")
st.caption(f"Current Time: {pd.Timestamp.now(tz='Asia/Ho_Chi_Minh').strftime('%Y-%m-%d %H:%M:%S %Z')}")
st.markdown("---")

# Create tabs for better organization
tab1, tab2 = st.tabs(["Create New Calculation", "View Saved Calculations"])

with tab1:
    st.markdown("This tool only used for the first 10 deals")
    st.markdown("**Instructions:** Enter your estimated project revenue and costs below. All values should be in your primary operating currency.")

    # --- Input Sections ---
    # Using columns to organize input sections better
    col1, col2 = st.columns(2)

    total_expenses = 0
    category_expenses = {}

    # --- Column 1: Revenue and Team Structure ---
    with col1:
        st.header("Project Revenue")
        
        # Add project name field
        project_name = st.text_input("Project Name", "New Project", help="Enter a name to identify this calculation")
        
        with st.expander("Project Pricing", expanded=True):
            st.markdown("**Enter your project pricing, and we'll suggest cost allocations**")
            
            # Simplified pricing inputs focused on user input
            upfront_payment = st.number_input("Upfront Project Payment", min_value=0.0, value=0.0, step=500.0, format="%.2f")
            monthly_maintenance = st.number_input("Monthly Maintenance Fee", min_value=0.0, value=0.0, step=100.0, format="%.2f")
            num_maintenance_months = st.number_input("Number of Maintenance Months", min_value=0, value=1, step=1)
            total_maintenance = monthly_maintenance * num_maintenance_months
            other_revenue = st.number_input("Other Project Revenue", min_value=0.0, value=0.0, step=100.0, format="%.2f")
            
            total_revenue = upfront_payment + total_maintenance + other_revenue
                
            st.markdown(f"**Total Project Revenue: {total_revenue:,.2f}**")
            if total_maintenance > 0:
                st.markdown(f"*Maintenance Revenue ({num_maintenance_months} months): {total_maintenance:,.2f}*")

        st.header("Target Margin")
        with st.expander("Profit Margin Target", expanded=True):
            target_margin = st.slider("Target Profit Margin (%)", min_value=0, max_value=90, value=50, step=5)
            
            # Calculate available budget for costs based on target margin
            available_budget = total_revenue * (1 - target_margin/100) if total_revenue > 0 else 0
            
            st.markdown(f"**Target Margin: {target_margin}%**")
            st.markdown(f"**Available Budget for Costs: {available_budget:,.2f}**")
            
            # Typical industry allocation percentages
            st.markdown("#### Suggested Cost Distribution")
            
            if total_revenue > 0:
                with st.form("allocation_percentages"):
                    st.markdown("Adjust the allocation percentages for your project:")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        freelancer_allocation = st.slider("Freelancer Cost %", 0, 100, 50, 5)
                        internal_staff_allocation = st.slider("Internal Staff %", 0, 100, 20, 5)
                    with c2:    
                        tech_infra_allocation = st.slider("Tech & Infrastructure %", 0, 100, 15, 5)
                        admin_allocation = st.slider("Admin & Misc %", 0, 100, 15, 5)
                    
                    total_allocation = freelancer_allocation + internal_staff_allocation + tech_infra_allocation + admin_allocation
                    
                    calculation_col1, calculation_col2 = st.columns(2)
                    with calculation_col1:
                        submit_button = st.form_submit_button("Calculate Suggested Costs")
                    with calculation_col2:
                        save_button = st.form_submit_button("Save Calculation")
                    
                    if total_allocation != 100:
                        st.error(f"⚠️ Total allocation must equal 100% (currently {total_allocation}%)")
                    
                    # Save calculation to database when save button is clicked
                    if save_button and total_allocation == 100:
                        project_data = {
                            "name": project_name,
                            "upfront_payment": upfront_payment,
                            "monthly_maintenance": monthly_maintenance,
                            "maintenance_months": num_maintenance_months,
                            "other_revenue": other_revenue,
                            "target_margin": target_margin,
                            "freelancer_allocation": freelancer_allocation,
                            "internal_staff_allocation": internal_staff_allocation,
                            "tech_infra_allocation": tech_infra_allocation,
                            "admin_allocation": admin_allocation
                        }
                        project_id = save_project(project_data)
                        st.success(f"Calculation saved as '{project_name}' (ID: {project_id})")
        
    # In column 2, display the suggested costs based on allocations
    with col2:
        st.header("Suggested Cost Allocations")
        
        if total_revenue > 0 and 'allocation_percentages' in st.session_state and total_allocation == 100:
            # Calculate suggested costs based on available budget
            freelancer_budget = available_budget * (freelancer_allocation / 100)
            internal_staff_budget = available_budget * (internal_staff_allocation / 100)
            tech_infra_budget = available_budget * (tech_infra_allocation / 100)
            admin_budget = available_budget * (admin_allocation / 100)
            
            # Store in category expenses for later display
            category_expenses = {
                "A. Freelancers": freelancer_budget,
                "B. Internal Staff": internal_staff_budget,
                "C. Tech & Infrastructure": tech_infra_budget,
                "D. Admin & Misc": admin_budget
            }
            
            total_expenses = sum(category_expenses.values())
            
            # Display detailed cost suggestions by category
            with st.expander("Freelancer Cost Suggestions", expanded=True):
                st.metric("Total Freelancer Budget", f"{freelancer_budget:,.2f}")
                
                # Calculate per-developer allocation
                st.markdown("#### Suggested Freelancer Payments")
                dev_count = st.number_input("Number of Freelance Developers", min_value=1, max_value=10, value=2, step=1)
                
                if dev_count > 0:
                    even_split = freelancer_budget / dev_count
                    st.markdown(f"**Even split per developer: {even_split:,.2f}**")
                    
                    # Slider for adjusting allocations between developers
                    if dev_count > 1:
                        st.markdown("#### Adjust Developer Payment Split")
                        remaining = freelancer_budget
                        dev_allocations = []
                        
                        for i in range(1, dev_count):
                            max_percent = 100 if i == dev_count-1 else 90
                            percent = st.slider(f"Developer {i} (% of freelancer budget)", 
                                               min_value=5, max_value=max_percent, 
                                               value=max(5, int(100/dev_count)), step=5)
                            amount = freelancer_budget * (percent / 100)
                            remaining -= amount
                            dev_allocations.append((f"Developer {i}", amount, percent))
                        
                        # Last developer gets remainder
                        if remaining > 0:
                            percent = 100 - sum(alloc[2] for alloc in dev_allocations)
                            dev_allocations.append((f"Developer {dev_count}", remaining, percent))
                        
                        for name, amount, percent in dev_allocations:
                            st.markdown(f"* **{name}**: {amount:,.2f} ({percent}% of freelancer budget)")
            
            with st.expander("Internal Staff Allocation"):
                st.metric("Total Internal Staff Budget", f"{internal_staff_budget:,.2f}")
                
                int_dev_percent = st.slider("Internal Developer %", 0, 100, 70, 5)
                sales_percent = 100 - int_dev_percent
                
                int_dev_budget = internal_staff_budget * (int_dev_percent / 100)
                sales_budget = internal_staff_budget * (sales_percent / 100)
                
                st.markdown(f"* **Internal Developer**: {int_dev_budget:,.2f} ({int_dev_percent}%)")
                st.markdown(f"* **Sales Person**: {sales_budget:,.2f} ({sales_percent}%)")
            
            with st.expander("Technology & Infrastructure"):
                st.metric("Total Tech & Infrastructure Budget", f"{tech_infra_budget:,.2f}")
                st.markdown("Suggested breakdown:")
                st.markdown(f"* **Cloud Hosting**: {tech_infra_budget * 0.4:,.2f} (40%)")
                st.markdown(f"* **Software Tools**: {tech_infra_budget * 0.3:,.2f} (30%)")
                st.markdown(f"* **Domain/Google Workspace**: {tech_infra_budget * 0.15:,.2f} (15%)")
                st.markdown(f"* **Misc Tech Costs**: {tech_infra_budget * 0.15:,.2f} (15%)")
            
            with st.expander("Administrative & Miscellaneous"):
                st.metric("Total Admin & Misc Budget", f"{admin_budget:,.2f}")
                st.markdown("Suggested breakdown:")
                st.markdown(f"* **Accounting/Legal**: {admin_budget * 0.3:,.2f} (30%)")
                st.markdown(f"* **Bank Fees**: {admin_budget * 0.2:,.2f} (20%)")
                st.markdown(f"* **Contingency**: {admin_budget * 0.5:,.2f} (50%)")
        else:
            if total_revenue <= 0:
                st.info("Enter project revenue to see suggested cost allocations.")
            elif 'allocation_percentages' not in st.session_state:
                st.info("Click 'Calculate Suggested Costs' to see allocations.")
            elif total_allocation != 100:
                st.warning("Total allocation percentages must equal 100%.")

    # --- Project Summary ---
    st.markdown("---")
    st.header("📊 Project Financial Summary")

    # Fix the condition that determines when to display the summary
    if total_revenue > 0:
        # Move form-based allocation to session state to persist between reruns
        if submit_button or "saved_allocations" not in st.session_state:
            st.session_state["saved_allocations"] = {
                "freelancer": freelancer_allocation,
                "internal_staff": internal_staff_allocation,
                "tech_infra": tech_infra_allocation,
                "admin": admin_allocation,
                "total": total_allocation
            }
        
        # Use the saved allocations if available and valid
        saved = st.session_state["saved_allocations"]
        if saved["total"] == 100:
            freelancer_alloc = saved["freelancer"]
            internal_staff_alloc = saved["internal_staff"]
            tech_infra_alloc = saved["tech_infra"] 
            admin_alloc = saved["admin"]
        else:
            # Default allocations
            freelancer_alloc = 50
            internal_staff_alloc = 20
            tech_infra_alloc = 15
            admin_alloc = 15
        
        # Always recalculate with current target margin
        available_budget = total_revenue * (1 - target_margin/100)
        
        # Calculate costs based on current allocations
        freelancer_budget = available_budget * (freelancer_alloc / 100)
        internal_staff_budget = available_budget * (internal_staff_alloc / 100)
        tech_infra_budget = available_budget * (tech_infra_alloc / 100)
        admin_budget = available_budget * (admin_alloc / 100)
        
        # Update category expenses for display
        category_expenses = {
            "A. Freelancers": freelancer_budget,
            "B. Internal Staff": internal_staff_budget,
            "C. Tech & Infrastructure": tech_infra_budget,
            "D. Admin & Misc": admin_budget
        }
        
        total_expenses = sum(category_expenses.values())
        
        if saved["total"] != 100:
            st.info("Using default cost allocations. Adjust and submit the form for customized allocations.")
        
        # Calculate summary metrics
        expected_profit = total_revenue - total_expenses
        actual_margin_pct = (expected_profit / total_revenue * 100) if total_revenue > 0 else 0

        col_sum1, col_sum2, col_sum3 = st.columns(3)
        with col_sum1:
            st.metric("Total Project Revenue", f"{total_revenue:,.2f}")
        with col_sum2:
            st.metric("Suggested Total Expenses", f"{total_expenses:,.2f}")
        with col_sum3:
            st.metric("Expected Profit", f"{expected_profit:,.2f}", 
                    delta=f"{actual_margin_pct:.1f}% margin" if total_revenue > 0 else "N/A")

        # Display improved cost breakdown visualization
        if total_expenses > 0:
            st.markdown("---")
            st.subheader("Cost Allocation Breakdown")
            
            # Create two columns for different visualizations
            viz_col1, viz_col2 = st.columns([3, 2])
            
            # Check if Plotly is installed
            try:
                plotly_available = True
            except ImportError:
                plotly_available = False
                st.warning("📦 **Plotly is not installed.** For better visualizations, install it with: `pip install plotly`")
            
            with viz_col1:
                if plotly_available:
                    # Create a stacked bar chart showing deal composition using Plotly
                    # Prepare data for stacked visualization
                    fig = go.Figure()
                    
                    # Add profit bar
                    fig.add_trace(go.Bar(
                        name='Profit',
                        y=['Deal Composition'],
                        x=[expected_profit],
                        orientation='h',
                        marker=dict(color='#2ecc71'),
                        text=f"{actual_margin_pct:.1f}%",
                        textposition='inside',
                        insidetextanchor='middle'
                    ))
                    
                    # Add expense categories
                    categories = list(category_expenses.keys())
                    colors = ['#3498db', '#9b59b6', '#e74c3c', '#f39c12']
                    
                    for i, (category, amount) in enumerate(category_expenses.items()):
                        percentage = (amount / total_revenue * 100)
                        fig.add_trace(go.Bar(
                            name=category,
                            y=['Deal Composition'],
                            x=[amount],
                            orientation='h',
                            marker=dict(color=colors[i % len(colors)]),
                            text=f"{percentage:.1f}%" if percentage >= 5 else "",
                            textposition='inside',
                            insidetextanchor='middle'
                        ))
                    
                    # Customize layout
                    fig.update_layout(
                        title='Deal Size Composition',
                        barmode='stack',
                        height=200,
                        margin=dict(l=50, r=50, t=50, b=20),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
                        xaxis=dict(title='Amount')
                    )
                    
                    # Show the figure
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Fallback to Streamlit's built-in charts
                    st.subheader("Deal Size Composition")
                    
                    # Create a DataFrame for the deal composition
                    deal_data = {
                        "Component": ["Profit"] + list(category_expenses.keys()),
                        "Amount": [expected_profit] + list(category_expenses.values()),
                        "Percentage": [actual_margin_pct] + [
                            (amount / total_revenue * 100) for amount in category_expenses.values()
                        ]
                    }
                    
                    deal_df = pd.DataFrame(deal_data)
                    deal_df["Label"] = deal_df.apply(
                        lambda x: f"{x['Component']}: {x['Amount']:.2f} ({x['Percentage']:.1f}%)", 
                        axis=1
                    )
                    
                    # Display as a horizontal bar chart
                    st.bar_chart(deal_df.set_index("Component")["Amount"], use_container_width=True)
                
                # Add annotations explaining the chart
                st.markdown("**Deal Composition**: This chart shows how your total project revenue is distributed across cost categories and profit.")
            
            with viz_col2:
                if plotly_available:
                    # Create a pie chart for expense breakdown (excluding profit)
                    labels = list(category_expenses.keys())
                    values = list(category_expenses.values())
                    
                    fig = go.Figure(data=[go.Pie(
                        labels=labels,
                        values=values,
                        hole=.3,
                        textinfo='label+percent',
                        insidetextorientation='radial'
                    )])
                    
                    fig.update_layout(
                        title='Expense Distribution',
                        height=320,
                        margin=dict(l=20, r=20, t=50, b=20)
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    # Fallback to Streamlit's built-in charts
                    st.subheader("Expense Distribution")
                    
                    # Create a pie chart for expenses using Matplotlib
                    expense_df = pd.DataFrame({
                        "Category": list(category_expenses.keys()),
                        "Amount": list(category_expenses.values())
                    })
                    
                    # Display as a bar chart (Streamlit doesn't have built-in pie charts)
                    st.bar_chart(expense_df.set_index("Category"), use_container_width=True)
                
                st.markdown("**Expense Distribution**: This chart shows the proportion of expenses by category.")
            
            # Display Table with percentages (unchanged)
            st.subheader("Detailed Allocation Table")
            summary_data = []
            for category, amount in category_expenses.items():
                percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
                revenue_pct = (amount / total_revenue * 100) if total_revenue > 0 else 0
                summary_data.append({
                    "Category": category, 
                    "Amount": f"{amount:,.2f}", 
                    "% of Expenses": f"{percentage:.1f}%",
                    "% of Revenue": f"{revenue_pct:.1f}%"
                })
            
            # Add profit row
            summary_data.append({
                "Category": "Profit", 
                "Amount": f"{expected_profit:,.2f}", 
                "% of Expenses": "N/A",
                "% of Revenue": f"{actual_margin_pct:.1f}%"
            })

            st.table(pd.DataFrame(summary_data))
    else:
        st.info("Enter project revenue to see financial summary.")

    # Add note about updating results
    st.markdown("---")
    st.caption("**Note**: After changing the Target Margin, all calculations will update immediately. After adjusting cost allocation sliders, click the 'Calculate Suggested Costs' button to update the results.")

# Tab for viewing saved calculations
with tab2:
    st.header("Saved Project Calculations")
    
    # Fetch all saved projects
    saved_projects = get_all_projects()
    
    if not saved_projects:
        st.info("No saved calculations found. Use the 'Create New Calculation' tab to save your first calculation.")
    else:
        # Create DataFrame for display
        projects_df = pd.DataFrame(saved_projects)
        
        # Calculate and add total revenue column
        projects_df['total_revenue'] = (
            projects_df['upfront_payment'] + 
            (projects_df['monthly_maintenance'] * projects_df['maintenance_months']) +
            projects_df['other_revenue']
        )
        
        # Format display table
        display_df = projects_df[['id', 'name', 'total_revenue', 'target_margin', 'created_at']].copy()
        display_df.columns = ['ID', 'Project Name', 'Total Revenue', 'Target Margin %', 'Created At']
        
        # Format numbers
        display_df['Total Revenue'] = display_df['Total Revenue'].apply(lambda x: f"{x:,.2f}")
        display_df['Target Margin %'] = display_df['Target Margin %'].apply(lambda x: f"{x:.0f}%")
        
        # Display the table
        st.dataframe(display_df, use_container_width=True)
        
        # Project selection for actions (view/edit/delete)
        selected_project_id = st.selectbox(
            "Select a project to view, edit or delete:",
            options=[p['id'] for p in saved_projects],
            format_func=lambda x: f"ID {x}: {next((p['name'] for p in saved_projects if p['id'] == x), 'Unknown')}"
        )
        
        if selected_project_id:
            # Get the selected project
            project = get_project_by_id(selected_project_id)
            
            # Display project details and action buttons
            st.subheader(f"Project: {project['name']}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                load_button = st.button("Load Project")
            with col2:
                edit_button = st.button("Edit Project")
            with col3:
                delete_button = st.button("Delete Project")
            
            if load_button:
                # Store the project data in session state to load in the other tab
                st.session_state.load_project = project
                st.success(f"Project '{project['name']}' loaded. Switch to 'Create New Calculation' tab to view.")
            
            elif edit_button:
                # Store the project data in session state for editing
                st.session_state.edit_project = project
                st.success(f"Switch to 'Create New Calculation' tab to edit project '{project['name']}'.")
                
            elif delete_button:
                # Show confirmation before deleting
                confirm_delete = st.checkbox("Confirm deletion")
                if confirm_delete and st.button("Confirm Delete"):
                    if delete_project(selected_project_id):
                        st.success(f"Project '{project['name']}' has been deleted.")
                        st.experimental_rerun()
                    else:
                        st.error("Failed to delete project. Please try again.")

            # Display project details
            st.subheader("Project Details")
            
            # Calculate total revenue
            total_revenue = (
                project['upfront_payment'] + 
                (project['monthly_maintenance'] * project['maintenance_months']) +
                project['other_revenue']
            )
            
            # Calculate available budget based on target margin
            available_budget = total_revenue * (1 - project['target_margin']/100) if total_revenue > 0 else 0
            
            # Calculate costs based on allocations
            freelancer_budget = available_budget * (project['freelancer_allocation'] / 100)
            internal_staff_budget = available_budget * (project['internal_staff_allocation'] / 100)
            tech_infra_budget = available_budget * (project['tech_infra_allocation'] / 100)
            admin_budget = available_budget * (project['admin_allocation'] / 100)
            
            # Calculate total expenses and profit
            total_expenses = freelancer_budget + internal_staff_budget + tech_infra_budget + admin_budget
            expected_profit = total_revenue - total_expenses
            actual_margin_pct = (expected_profit / total_revenue * 100) if total_revenue > 0 else 0
            
            # Display financial summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Revenue", f"{total_revenue:,.2f}")
            with col2:
                st.metric("Total Expenses", f"{total_expenses:,.2f}")
            with col3:
                st.metric("Profit", f"{expected_profit:,.2f}", delta=f"{actual_margin_pct:.1f}% margin")
            
            # Display allocation details
            st.subheader("Cost Allocations")
            
            allocation_data = {
                "Category": ["Freelancer", "Internal Staff", "Tech & Infrastructure", "Admin & Misc"],
                "Percentage": [
                    f"{project['freelancer_allocation']:.0f}%",
                    f"{project['internal_staff_allocation']:.0f}%", 
                    f"{project['tech_infra_allocation']:.0f}%",
                    f"{project['admin_allocation']:.0f}%"
                ],
                "Amount": [
                    f"{freelancer_budget:,.2f}",
                    f"{internal_staff_budget:,.2f}",
                    f"{tech_infra_budget:,.2f}",
                    f"{admin_budget:,.2f}"
                ]
            }
            
            # Display as a table
            st.table(pd.DataFrame(allocation_data))
            
            # Display chart if Plotly is available
            try:
                # Create a pie chart for expense breakdown
                labels = allocation_data["Category"]
                values = [
                    freelancer_budget,
                    internal_staff_budget,
                    tech_infra_budget,
                    admin_budget
                ]
                
                fig = go.Figure(data=[go.Pie(
                    labels=labels,
                    values=values,
                    hole=.3,
                    textinfo='label+percent',
                    insidetextorientation='radial'
                )])
                
                fig.update_layout(
                    title='Expense Distribution',
                    height=300,
                    margin=dict(l=20, r=20, t=50, b=20)
                )
                
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning("Chart could not be displayed")

# Check if a project is loaded from storage and populate fields
if hasattr(st.session_state, 'load_project') or hasattr(st.session_state, 'edit_project'):
    # Get project data from session state
    project_data = getattr(st.session_state, 'load_project', None) or getattr(st.session_state, 'edit_project', None)
    
    # Switch to the first tab
    st._set_query_params(**{'selected_tab': 0})
    
    # Reset the session state to avoid future reloads
    if hasattr(st.session_state, 'load_project'):
        del st.session_state.load_project
    if hasattr(st.session_state, 'edit_project'):
        del st.session_state.edit_project
        
    # Display instructions to the user
    st.sidebar.success(f"Project '{project_data['name']}' loaded. Adjust values and save as a new project or update the existing one.")
    
    # Create a mechanism to update this project
    if st.sidebar.button(f"Update Project: {project_data['name']}"):
        # Get current values from the UI
        updated_data = {
            "name": project_name,
            "upfront_payment": upfront_payment,
            "monthly_maintenance": monthly_maintenance,
            "maintenance_months": num_maintenance_months,
            "other_revenue": other_revenue,
            "target_margin": target_margin,
            "freelancer_allocation": freelancer_allocation,
            "internal_staff_allocation": internal_staff_allocation,
            "tech_infra_allocation": tech_infra_allocation,
            "admin_allocation": admin_allocation
        }
        
        # Update the project
        if update_project(project_data['id'], updated_data):
            st.sidebar.success(f"Project '{project_data['name']}' has been updated.")
            st.experimental_rerun()
        else:
            st.sidebar.error("Failed to update project. Please try again.")