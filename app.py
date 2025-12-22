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

def safe_rerun():
    try:
        st.rerun()
    except Exception:
        pass

def deny_access():
    st.error("You are not authorised to access this module.")
    st.stop()

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

role = users.loc[users["username"]==username,"role"].values[0]
user_dept = users.loc[users["username"]==username,"department"].values[0]

st.sidebar.success(f"Role: {role}")
if role=="Department":
    st.sidebar.info(f"Department: {user_dept}")

st.title("Digital Ledger Management System (DLMS)")
st.caption("MSc IT – Final Hardened Prototype")

# ================= ROLE-BASED MENU =================
if role == "Department":
    menu_options = [
        "Dashboard",
        "Available Stock / Raise S-156",
        "Pending Actions",
        "Ledger",
        "PLL",
        "Consumable Summary",
        "Return Item"
    ]
elif role == "Store":
    menu_options = [
        "Dashboard",
        "Store Approvals",
        "Pending Actions",
        "Ledger",
        "PLL",
        "Consumable Summary",
        "Survey"
    ]
elif role == "Admin":
    menu_options = [
        "Dashboard",
        "Pending Actions",
        "Ledger",
        "PLL",
        "Write-Off"
    ]

menu = st.sidebar.selectbox("Menu", menu_options)

# ================= DASHBOARD =================
if menu=="Dashboard":

    if role=="Store":
        st.header("Store Dashboard")
        st.metric("Total Items", len(items))
        st.metric("Available Stock", int(items["Stock"].sum()))
        st.metric("Pending Requests", len(s156[s156["Status"]=="Requested"]))

    elif role=="Department":
        st.header("Department Dashboard")
        dept_pll = pll[pll["Department"]==user_dept]
        st.metric("Items on PLL", int(dept_pll["Qty"].sum()))
        st.metric("Pending Requests", len(
            s156[(s156["Department"]==user_dept)&(s156["Status"]!="Received")]
        ))
        st.dataframe(dept_pll if not dept_pll.empty else pd.DataFrame())

    elif role=="Admin":
        st.header("Admin Dashboard")
        st.metric("Departments", depts["Department"].nunique())
        st.metric("Pending Surveys", len(survey[survey["Status"]=="Pending"]))
        st.metric("Write-Offs", len(writeoff))

# ================= AVAILABLE STOCK / S-156 =================
elif menu=="Available Stock / Raise S-156":
    if role!="Department":
        deny_access()

    st.header("Available Stock (Store)")
    available = items[(items["Type"]=="Permanent")&(items["Stock"]>0)]

    if available.empty:
        st.info("No items available in store.")
    else:
        st.dataframe(available)

        item = st.selectbox("Item", available["Item"])
        max_qty = int(available[available["Item"]==item]["Stock"].values[0])
        qty = st.number_input("Quantity",1,max_qty)

        if st.button("Raise S-156 Request"):
            s156.loc[len(s156)] = [item,user_dept,qty,"Requested"]
            save(s156,FILES["s156"])
            st.success("S-156 Request Raised")
            safe_rerun()

# ================= STORE APPROVALS =================
elif menu=="Store Approvals":
    if role!="Store":
        deny_access()

    st.header("Store Approvals")
    pending = s156[s156["Status"]=="Requested"]

    if pending.empty:
        st.info("No requests pending approval.")
    else:
        for i,row in pending.iterrows():
            st.write(row.to_dict())
            if st.button(f"Approve {i}",key=f"sa{i}"):

                stock = items.loc[items["Item"]==row["Item"],"Stock"].values[0]
                if stock < row["Qty"]:
                    st.error("Insufficient stock")
                    st.stop()

                items.loc[items["Item"]==row["Item"],"Stock"] -= row["Qty"]
                s156.at[i,"Status"]="Store Approved"

                save(items,FILES["items"])
                save(s156,FILES["s156"])
                safe_rerun()

# ================= PENDING ACTIONS =================
elif menu=="Pending Actions":
    st.header("Pending Actions")

    if role=="Department":
        pending = s156[
            (s156["Department"]==user_dept)&
            (s156["Status"]=="Store Approved")
        ]

        if pending.empty:
            st.info("No items pending receipt confirmation.")
        else:
            for i,row in pending.iterrows():
                st.write(row.to_dict())
                if st.button(f"Confirm Receipt {i}",key=f"rcv{i}"):

                    s156.at[i,"Status"]="Received"

                    item_row = items[items["Item"]==row["Item"]].iloc[0]
                    ledger.loc[len(ledger)] = [
                        row["Item"],item_row["Ledger"],
                        item_row["Folio"],row["Department"],row["Qty"]
                    ]

                    mask = (pll["Department"]==row["Department"])&(pll["Item"]==row["Item"])
                    if mask.any():
                        pll.loc[mask,"Qty"] += row["Qty"]
                    else:
                        pll.loc[len(pll)] = [row["Department"],row["Item"],row["Qty"]]

                    save(s156,FILES["s156"])
                    save(ledger,FILES["ledger"])
                    save(pll,FILES["pll"])
                    st.success("Receipt confirmed. Ledger & PLL updated.")
                    safe_rerun()

    elif role=="Store":
        data = s156[s156["Status"]=="Requested"]
        st.dataframe(data if not data.empty else pd.DataFrame())

    elif role=="Admin":
        data = survey[survey["Status"]=="Pending"]
        st.dataframe(data if not data.empty else pd.DataFrame())

# ================= LEDGER =================
elif menu=="Ledger":
    st.header("Ledger")
    data = ledger if role!="Department" else ledger[ledger["Department"]==user_dept]
    st.dataframe(data if not data.empty else pd.DataFrame())

# ================= PLL =================
elif menu=="PLL":
    st.header("Permanent Loan Ledger")
    data = pll if role!="Department" else pll[pll["Department"]==user_dept]
    st.dataframe(data if not data.empty else pd.DataFrame())

# ================= CONSUMABLE SUMMARY =================
elif menu=="Consumable Summary":
    st.header("Consumable Summary")
    data = summary if role=="Store" else summary[summary["Department"]==user_dept]
    st.dataframe(data if not data.empty else pd.DataFrame())

# ================= RETURN ITEM =================
elif menu=="Return Item":
    if role!="Department":
        deny_access()

    st.header("Return Item")
    dept_pll = pll[pll["Department"]==user_dept]

    if dept_pll.empty:
        st.info("No items available for return.")
    else:
        st.dataframe(dept_pll)
        item = st.selectbox("Item",dept_pll["Item"])
        max_qty = int(dept_pll[dept_pll["Item"]==item]["Qty"].values[0])
        qty = st.number_input("Return Qty",1,max_qty)

        if st.button("Submit Return"):
            returns.loc[len(returns)] = [user_dept,item,qty,"Pending"]
            save(returns,FILES["returns"])
            st.success("Return submitted")
            safe_rerun()

# ================= SURVEY =================
elif menu=="Survey":
    if role!="Store":
        deny_access()

    st.header("Survey")
    item = st.selectbox("Item",items["Item"])
    dept = st.selectbox("Department",depts["Department"])
    qty = st.number_input("Qty",1)
    ref = st.text_input("Survey Ref")

    if st.button("Initiate Survey"):
        survey.loc[len(survey)] = [item,dept,qty,ref,"Pending"]
        save(survey,FILES["survey"])
        st.success("Survey initiated")
        safe_rerun()

# ================= WRITE-OFF =================
elif menu=="Write-Off":
    if role!="Admin":
        deny_access()

    st.header("Write-Off Approval")

    pending = survey[survey["Status"]=="Pending"]
    if pending.empty:
        st.info("No surveys pending write-off.")
    else:
        for i,row in pending.iterrows():
            st.write(row.to_dict())
            if st.checkbox(f"Confirm write-off for {row['Item']} ({i})"):
                if st.button(f"Approve {i}",key=f"wo{i}"):

                    survey.at[i,"Status"]="Approved"
                    writeoff.loc[len(writeoff)] = [
                        row["Item"],row["Department"],
                        row["Qty"],row["SurveyRef"],"Approved"
                    ]

                    mask = (pll["Department"]==row["Department"])&(pll["Item"]==row["Item"])
                    if mask.any():
                        pll.loc[mask,"Qty"] -= row["Qty"]

                    save(survey,FILES["survey"])
                    save(writeoff,FILES["writeoff"])
                    save(pll,FILES["pll"])
                    safe_rerun()
