import streamlit as st
import pandas as pd
import os

# ================= FILES =================
FILES = {
    "users": "users.csv",
    "items": "items.csv",
    "depts": "departments.csv",
    "s156": "s156.csv",
    "ledger": "ledger.csv",
    "pll": "pll.csv",
    "summary": "summary.csv",
    "returns": "returns.csv",
    "survey": "survey.csv",
    "writeoff": "writeoff.csv"
}

# ================= HELPERS =================
def load(file, cols):
    if os.path.exists(file):
        return pd.read_csv(file)
    return pd.DataFrame(columns=cols)

def save(df, file):
    df.to_csv(file, index=False)

# ================= LOAD DATA =================
users = load(FILES["users"], ["username","role","department"])
items = load(FILES["items"], ["Item","Ledger","Folio","Type","Stock"])
depts = load(FILES["depts"], ["Department"])
s156 = load(FILES["s156"], ["Item","Department","Qty","Status"])
ledger = load(FILES["ledger"], ["Item","Ledger","Folio","Department","Qty"])
pll = load(FILES["pll"], ["Department","Item","Qty"])
summary = load(FILES["summary"], ["Item","Department","Qty"])
returns = load(FILES["returns"], ["Department","Item","Qty","Status"])
survey = load(FILES["survey"], ["Item","Department","Qty","SurveyRef","Status"])
writeoff = load(FILES["writeoff"], ["Item","Department","Qty","SurveyRef","Status"])

# ================= LOGIN =================
st.sidebar.title("Login")
username = st.sidebar.text_input("Username")

if username not in users["username"].values:
    st.warning("Enter valid username")
    st.stop()

role = users.loc[users["username"] == username, "role"].values[0]
user_dept = users.loc[users["username"] == username, "department"].values[0]

st.sidebar.success(f"Role: {role}")
if role == "Department":
    st.sidebar.info(f"Department: {user_dept}")

st.title("Digital Ledger Management System (DLMS)")
st.caption("MSc IT – Working Prototype")

# ================= MENU =================
menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Available Stock",
        "Pending Actions",
        "Store Approvals",
        "Item Master",
        "Department Master",
        "Ledger",
        "PLL",
        "Consumable Summary",
        "Return Item",
        "Survey",
        "Write-Off"
    ]
)

# ================= DASHBOARD =================
if menu == "Dashboard":

    if role == "Store":
        st.header("Store Dashboard")
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Items", len(items))
        c2.metric("Available Stock", int(items["Stock"].sum()))
        c3.metric("Ledger Entries", len(ledger))

        c4,c5,c6 = st.columns(3)
        c4.metric("Pending Requests", len(s156[s156["Status"]=="Requested"]))
        c5.metric("Pending Returns", len(returns[returns["Status"]=="Pending"]))
        c6.metric("Pending Surveys", len(survey[survey["Status"]=="Pending"]))

    elif role == "Department":
        st.header("Department Dashboard")

        dept_pll = pll[pll["Department"] == user_dept]
        dept_s156 = s156[s156["Department"] == user_dept]
        dept_returns = returns[returns["Department"] == user_dept]
        dept_survey = survey[survey["Department"] == user_dept]

        c1,c2,c3 = st.columns(3)
        c1.metric("Items on PLL", int(dept_pll["Qty"].sum()))
        c2.metric("Pending Requests", len(dept_s156[dept_s156["Status"]!="Received"]))
        c3.metric("Pending Returns", len(dept_returns[dept_returns["Status"]=="Pending"]))

        st.subheader("Your PLL")
        st.dataframe(dept_pll)

    elif role == "Admin":
        st.header("Admin Dashboard")
        c1,c2,c3 = st.columns(3)
        c1.metric("Departments", depts["Department"].nunique())
        c2.metric("Pending Surveys", len(survey[survey["Status"]=="Pending"]))
        c3.metric("Write-Offs", len(writeoff))

        st.subheader("PLL Snapshot")
        st.dataframe(pll.groupby("Department")["Qty"].sum().reset_index())

# ================= AVAILABLE STOCK =================
elif menu == "Available Stock" and role == "Department":
    st.header("Available Stock (Store)")

    available = items[(items["Type"]=="Permanent") & (items["Stock"]>0)]
    st.dataframe(available)

    item = st.selectbox("Item", available["Item"])
    max_qty = int(available[available["Item"]==item]["Stock"].values[0])
    qty = st.number_input("Quantity", 1, max_qty)

    if st.button("Raise S-156 Request"):
        s156.loc[len(s156)] = [item, user_dept, qty, "Requested"]
        save(s156, FILES["s156"])
        st.success("S-156 Request Submitted")

# ================= STORE APPROVALS =================
elif menu == "Store Approvals" and role == "Store":
    st.header("Store Approvals")

    pending = s156[s156["Status"]=="Requested"]
    for i,row in pending.iterrows():
        st.write(row.to_dict())
        if st.button(f"Approve {i}", key=f"ap{i}"):
            s156.at[i,"Status"] = "Store Approved"
            items.loc[items["Item"]==row["Item"],"Stock"] -= row["Qty"]
            save(items, FILES["items"])
            save(s156, FILES["s156"])
            st.experimental_rerun()

# ================= PENDING ACTIONS =================
elif menu == "Pending Actions":
    st.header("Pending Actions")

    if role == "Department":
        st.dataframe(s156[(s156["Department"]==user_dept) & (s156["Status"]!="Received")])

    elif role == "Store":
        st.dataframe(s156[s156["Status"]=="Requested"])

    elif role == "Admin":
        st.dataframe(survey[survey["Status"]=="Pending"])

# ================= LEDGER =================
elif menu == "Ledger":
    st.header("Ledger")
    if role == "Department":
        st.dataframe(ledger[ledger["Department"]==user_dept])
    else:
        st.dataframe(ledger)

# ================= PLL =================
elif menu == "PLL":
    st.header("Permanent Loan Ledger")
    if role == "Department":
        st.dataframe(pll[pll["Department"]==user_dept])
    else:
        st.dataframe(pll)

# ================= CONSUMABLE SUMMARY =================
elif menu == "Consumable Summary":
    st.header("Consumable Summary")
    if role == "Store":
        st.dataframe(summary)
    elif role == "Department":
        st.dataframe(summary[summary["Department"]==user_dept])

# ================= RETURN ITEM =================
elif menu == "Return Item" and role == "Department":
    st.header("Return Item")

    dept_pll = pll[pll["Department"]==user_dept]
    st.dataframe(dept_pll)

    item = st.selectbox("Item", dept_pll["Item"])
    max_qty = int(dept_pll[dept_pll["Item"]==item]["Qty"].values[0])
    qty = st.number_input("Return Qty",1,max_qty)

    if st.button("Submit Return"):
        returns.loc[len(returns)] = [user_dept,item,qty,"Pending"]
        save(returns, FILES["returns"])
        st.success("Return Requested")

# ================= SURVEY =================
elif menu == "Survey":
    st.header("Survey")

    if role == "Store":
        item = st.selectbox("Item", items["Item"])
        dept = st.selectbox("Department", depts["Department"])
        qty = st.number_input("Qty",1)
        ref = st.text_input("Survey Ref")

        if st.button("Initiate Survey"):
            survey.loc[len(survey)] = [item,dept,qty,ref,"Pending"]
            save(survey, FILES["survey"])
            st.success("Survey Initiated")

    elif role == "Department":
        st.dataframe(survey[survey["Department"]==user_dept])

# ================= WRITE-OFF =================
elif menu == "Write-Off":
    st.header("Write-Off")

    if role == "Admin":
        for i,row in survey[survey["Status"]=="Pending"].iterrows():
            st.write(row.to_dict())
            if st.button(f"Approve {i}", key=f"wo{i}"):
                survey.at[i,"Status"]="Approved"
                writeoff.loc[len(writeoff)] = [
                    row["Item"],row["Department"],row["Qty"],row["SurveyRef"],"Approved"
                ]
                pll.loc[
                    (pll["Department"]==row["Department"]) &
                    (pll["Item"]==row["Item"]),
                    "Qty"
                ] -= row["Qty"]

                save(survey, FILES["survey"])
                save(writeoff, FILES["writeoff"])
                save(pll, FILES["pll"])
                st.experimental_rerun()
    else:
        st.warning("Admin access only")
