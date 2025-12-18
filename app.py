import streamlit as st
import pandas as pd
import os

# ---------------- FILES ----------------
FILES = {
    "users": "users.csv",
    "items": "items.csv",
    "depts": "departments.csv",
    "s156": "s156.csv",
    "ledger": "ledger.csv",
    "pll": "pll.csv",
    "summary": "summary.csv"
}

def load(file):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame()

def save(df, file):
    df.to_csv(file, index=False)

# ---------------- LOAD DATA ----------------
users = load(FILES["users"])
items = load(FILES["items"])
depts = load(FILES["depts"])
s156 = load(FILES["s156"])
ledger = load(FILES["ledger"])
pll = load(FILES["pll"])
summary = load(FILES["summary"])

# ---------------- LOGIN ----------------
st.sidebar.title("Login")
username = st.sidebar.text_input("Username")

if "username" not in users.columns or username not in users["username"].values:
    st.warning("Enter valid username (Store / Department / Admin)")
    st.stop()

role = users.loc[users["username"] == username, "role"].values[0]
st.sidebar.success(f"Role: {role}")

st.title("Digital Ledger Management System (DLMS)")
st.caption("Working Prototype – MSc IT")

# ---------------- MENU ----------------
menu = st.sidebar.selectbox(
    "Menu",
    [
        "Item Master", "Department Master", "S-156 Issue",
        "Approvals", "Ledger", "PLL", "Consumable Summary"
    ]
)

# ---------------- ITEM MASTER ----------------
if menu == "Item Master" and role == "Store":
    st.header("Item Master")
    item = st.text_input("Item Name")
    folio = st.text_input("Ledger Folio")
    itype = st.selectbox("Type", ["Permanent", "Consumable"])

    if st.button("Add Item"):
        exists = items[
            (items["Item"].str.lower() == item.lower()) &
            (items["Folio"].str.lower() == folio.lower())
        ]
        if not exists.empty:
            st.error("Item already exists in the same ledger folio")
        else:
            items = pd.concat([
                items,
                pd.DataFrame([[item, folio, itype]],
                columns=["Item", "Folio", "Type"])
            ], ignore_index=True)
            save(items, FILES["items"])
            st.success("Item Added")

    st.dataframe(items)

# ---------------- DEPARTMENT MASTER ----------------
elif menu == "Department Master" and role == "Store":
    st.header("Department Master")
    dept = st.text_input("Department Name")

    if st.button("Add Department"):
        depts = pd.concat([
            depts,
            pd.DataFrame([[dept]], columns=["Department"])
        ], ignore_index=True)
        save(depts, FILES["depts"])
        st.success("Department Added")

    st.dataframe(depts)

# ---------------- S-156 ISSUE ----------------
elif menu == "S-156 Issue" and role == "Store":
    st.header("S-156 Issue (Permanent Items)")
    item = st.selectbox(
        "Item",
        items[items["Type"] == "Permanent"]["Item"]
    )
    dept = st.selectbox("Department", depts["Department"])
    qty = st.number_input("Quantity", min_value=1, step=1)

    if st.button("Raise S-156"):
        s156 = pd.concat([
            s156,
            pd.DataFrame([[item, dept, qty, "Pending"]],
            columns=["Item", "Department", "Qty", "Status"])
        ], ignore_index=True)
        save(s156, FILES["s156"])
        st.success("S-156 Raised")

    st.dataframe(s156)

# ---------------- APPROVALS ----------------
elif menu == "Approvals":
    st.header("Approvals")

    for i, row in s156.iterrows():
        st.write(row.to_dict())

        if role == "Department" and row["Status"] == "Pending":
            if st.button(f"Dept Approve {i}"):
                s156.at[i, "Status"] = "Dept Approved"

        if role == "Admin" and row["Status"] == "Dept Approved":
            if st.button(f"Admin Approve {i}"):
                s156.at[i, "Status"] = "Approved"

                ledger = pd.concat([
                    ledger,
                    pd.DataFrame([[row["Item"], row["Department"], row["Qty"]]],
                    columns=["Item", "Department", "Qty"])
                ], ignore_index=True)

                pll = pd.concat([
                    pll,
                    pd.DataFrame([[row["Department"], row["Item"], row["Qty"]]],
                    columns=["Department", "Item", "Qty"])
                ], ignore_index=True)

    save(s156, FILES["s156"])
    save(ledger, FILES["ledger"])
    save(pll, FILES["pll"])

# ---------------- LEDGER ----------------
elif menu == "Ledger":
    st.header("Ledger")
    st.dataframe(ledger)

# ---------------- PLL ----------------
elif menu == "PLL":
    st.header("Permanent Loan Ledger")
    st.dataframe(pll)

# ---------------- CONSUMABLE SUMMARY ----------------
elif menu == "Consumable Summary" and role == "Store":
    st.header("Consumable Summary")
    item = st.selectbox(
        "Consumable Item",
        items[items["Type"] == "Consumable"]["Item"]
    )
    dept = st.selectbox("Department", depts["Department"])
    qty = st.number_input("Quantity Issued", min_value=1)

    if st.button("Add to Summary"):
        summary = pd.concat([
            summary,
            pd.DataFrame([[item, dept, qty]],
            columns=["Item", "Department", "Qty"])
        ], ignore_index=True)
        save(summary, FILES["summary"])
        st.success("Summary Updated")

    st.dataframe(summary)
