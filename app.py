
import streamlit as st
import pandas as pd
import os
import csv
from datetime import datetime

FILE = "expenses.csv"

COLUMNS = ["Date", "Category", "Description", "Amount"]

st.set_page_config(
    page_title="Smart Expense Tracker",
    page_icon="💰",
    layout="wide"
)


# Initialize CSV file
def initialize():
    if not os.path.exists(FILE) or os.path.getsize(FILE) == 0:
        with open(FILE, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(COLUMNS)


# Load expense data
def load_data():
    initialize()

    df = pd.read_csv(FILE)

    if list(df.columns) != COLUMNS:
        st.error(
            "Incorrect CSV headers. Please check expenses.csv. "
            "Required headers: Date, Category, Description, Amount"
        )
        st.stop()

    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce")
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Category"] = df["Category"].fillna("").astype(str).str.strip()
    df["Description"] = df["Description"].fillna("").astype(str)

    return df.dropna(subset=["Amount", "Date"]).reset_index(drop=True)


# Save a new expense and prevent accidental duplicates
def save_expense(category, description, amount):
    date = datetime.now().strftime("%Y-%m-%d")

    existing = pd.read_csv(FILE)

    if not existing.empty:
        duplicate = existing[
            (existing["Date"].astype(str).str[:10] == date) &
            (existing["Category"].astype(str).str.strip() == category.strip()) &
            (existing["Description"].astype(str).str.strip() == description.strip()) &
            (pd.to_numeric(existing["Amount"], errors="coerce") == amount)
        ]

        if not duplicate.empty:
            return False

    with open(FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([date, category, description, amount])

    return True


# Delete an expense
def delete_expense(index):
    df = load_data()

    updated_df = df.drop(index=index)

    updated_df.to_csv(
        FILE,
        index=False,
        date_format="%Y-%m-%d"
    )


# Initialize and load data
initialize()
df = load_data()


# Application title
st.title("💰 Smart Expense Tracker")

st.write(
    "Manage your daily expenses, track your spending "
    "and monitor your monthly budget."
)


# Sidebar navigation
st.sidebar.title("Navigation")

page = st.sidebar.radio(
    "Select a page",
    [
        "Dashboard",
        "Add Expense",
        "Expense History",
        "Category Report",
        "Budget Tracker"
    ]
)


# Calculate monthly expenses
today = pd.Timestamp.today()

month_data = df[
    (df["Date"].dt.year == today.year) &
    (df["Date"].dt.month == today.month)
]

total = df["Amount"].sum()

monthly_total = month_data["Amount"].sum()


# DASHBOARD
if page == "Dashboard":

    st.subheader("📊 Expense Dashboard")

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Total Expenses",
        f"₹{total:.2f}"
    )

    col2.metric(
        "This Month",
        f"₹{monthly_total:.2f}"
    )

    col3.metric(
        "Total Transactions",
        len(df)
    )

    st.divider()

    st.subheader("Recent Expenses")

    if not df.empty:

        st.dataframe(
            df.sort_values("Date", ascending=False).head(10),
            use_container_width=True
        )

        st.subheader("Spending Overview")

        category_totals = df.groupby("Category")["Amount"].sum()

        st.bar_chart(category_totals)

    else:
        st.info("No expenses available. Add your first expense!")


# ADD EXPENSE
elif page == "Add Expense":

    st.subheader("➕ Add a New Expense")

    with st.form("expense_form"):

        category = st.selectbox(
            "Select Category",
            [
                "Food",
                "Travel",
                "Shopping",
                "Education",
                "Entertainment",
                "Health",
                "Other"
            ]
        )

        description = st.text_input("Description")

        amount = st.number_input(
            "Amount (₹)",
            min_value=0.0,
            step=10.0
        )

        submit = st.form_submit_button("Add Expense")

        if submit:

            if not description.strip():

                st.warning("Please enter a description.")

            elif amount <= 0:

                st.warning("Amount must be greater than zero.")

            else:

                saved = save_expense(
                    category,
                    description.strip(),
                    amount
                )

                if saved:

                    st.success("Expense added successfully!")

                    st.rerun()

                else:

                    st.warning(
                        "This exact expense is already recorded today. "
                        "No duplicate was added."
                    )


# EXPENSE HISTORY
elif page == "Expense History":

    st.subheader("📋 All Expenses")

    if not df.empty:

        display_df = df.copy().reset_index(drop=True)

        st.dataframe(
            display_df,
            use_container_width=True
        )

        st.divider()

        st.subheader("🗑️ Delete an Expense")

        selected_index = st.selectbox(
            "Select the expense you want to delete",

            options=display_df.index,

            format_func=lambda i: (
                f"Row {i + 1} | "
                f"{display_df.loc[i, 'Date'].strftime('%Y-%m-%d')} | "
                f"{display_df.loc[i, 'Category']} | "
                f"{display_df.loc[i, 'Description']} | "
                f"₹{display_df.loc[i, 'Amount']:.2f}"
            )
        )

        if st.button("Delete Selected Expense", type="primary"):

            delete_expense(selected_index)

            st.success("Expense deleted successfully!")

            st.rerun()

        st.divider()

        csv_data = df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "Download Expense Report",
            csv_data,
            "expense_report.csv",
            "text/csv"
        )

    else:

        st.info("No expenses available yet.")


# CATEGORY REPORT
elif page == "Category Report":

    st.subheader("📈 Category-wise Expense Report")

    if not df.empty:

        report = df.groupby("Category")["Amount"].sum()

        st.dataframe(
            report.reset_index(),
            use_container_width=True
        )

        st.bar_chart(report)

    else:

        st.info("No expenses available yet.")


# BUDGET TRACKER
elif page == "Budget Tracker":

    st.subheader("💳 Monthly Budget Tracker")

    budget = st.number_input(
        "Enter Your Monthly Budget (₹)",
        min_value=1.0,
        value=5000.0,
        step=500.0
    )

    remaining = budget - monthly_total

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Monthly Budget",
        f"₹{budget:.2f}"
    )

    col2.metric(
        "Amount Spent",
        f"₹{monthly_total:.2f}"
    )

    col3.metric(
        "Remaining Balance",
        f"₹{remaining:.2f}"
    )

    progress = min(monthly_total / budget, 1.0)

    st.progress(progress)

    if monthly_total > budget:

        st.error("⚠️ Warning! You exceeded your monthly budget.")

    else:

        st.success("You are within your monthly budget.")

    st.subheader("Monthly Spending Summary")

    st.write(f"Total expenses this month: ₹{monthly_total:.2f}")

    st.write(f"Remaining budget: ₹{remaining:.2f}")
