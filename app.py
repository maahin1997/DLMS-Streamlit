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
items = load(FILES["items"], ["Item","Ledger","Folio","Type"])
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
    st.warning("Valid users: store / dept / admin")
    st.stop()

role = users.loc[users["username"]==username,"role"].values[0]
user_dept = users.loc[users["username"]==username,"department"].values[0]

st.sidebar.success(f"Role: {role}")
st.title("Digital Ledger Management System (DLMS)")
st.caption("MSc IT – Working Prototype")

# ================= MENU =================
menu = st.sidebar.selectbox(
    "Menu",
    [
        "Dashboard",
        "Item Master","Department Master","S-156 Issue",
        "Approvals","Ledger","PLL","Consumable Summary",
        "Return Item","Survey","Write-Off"
    ]
)

# ================= DASHBOARD =================
if menu=="Dashboard":

    if role=="Store":
        st.header("Store Dashboard")
        c1,c2,c3 = st.columns(3)
        c1.metric("Total Items",len(items))
        c2.metric("Permanent Items",len(items[items["Type"]=="Permanent"]))
        c3.metric("Consumable Items",len(items[items["Type"]=="Consumable"]))

        c4,c5,c6 = st.columns(3)
        c4.metric("Total S-156",len(s156))
        c5.metric("Pending S-156",len(s156[s156["Status"]=="Pending"]))
        c6.metric("Ledger Entries",len(ledger))

        c7,c8 = st.columns(2)
        c7.metric("Pending Returns",len(returns[returns["Status"]=="Pending"]))
        c8.metric("Pending Surveys",len(survey[survey["Status"]=="Pending"]))

    elif role=="Department":
        st.header("Department Dashboard")

        dept_pll = pll[pll["Department"]==user_dept]
        dept_s156 = s156[s156["Department"]==user_dept]
        dept_returns = returns[returns["Department"]==user_dept]
        dept_survey = survey[survey["Department"]==user_dept]

        c1,c2,c3 = st.columns(3)
        c1.metric("Items on PLL",dept_pll["Qty"].sum())
        c2.metric("Pending S-156",len(dept_s156[dept_s156["Status"]=="Pending"]))
        c3.metric("Approved Issues",len(dept_s156[dept_s156["Status"]=="Approved"]))

        c4,c5 = st.columns(2)
        c4.metric("Pending Returns",len(dept_returns[dept_returns["Status"]=="Pending"]))
        c5.metric("Surveyed Items",len(dept_survey[dept_survey["Status"]=="Approved"]))

        st.subheader("Your Permanent Loan Ledger")
        st.dataframe(dept_pll)

    elif role=="Admin":
        st.header("Admin Dashboard")
        c1,c2,c3 = st.columns(3)
        c1.metric("Departments",depts["Department"].nunique())
        c2.metric("Dept Approved S-156",len(s156[s156["Status"]=="Dept Approved"]))
        c3.metric("Final Approved",len(s156[s156["Status"]=="Approved"]))

        c4,c5,c6 = st.columns(3)
        c4.metric("Survey Cases",len(survey))
        c5.metric("Write-Offs",len(writeoff))
        c6.metric("Ledger Entries",len(ledger))

        st.subheader("PLL Snapshot")
        st.dataframe(pll.groupby("Department")["Qty"].sum().reset_index())

# ================= ITEM MASTER =================
elif menu=="Item Master" and role=="Store":
    st.header("Item Master")
    item = st.text_input("Item Name")
    ledger_name = st.text_input("Ledger Name")
    folio = st.text_input("Folio No")
    itype = st.selectbox("Type",["Permanent","Consumable"])

    if st.button("Add Item"):
        items.loc[len(items)] = [item,ledger_name,folio,itype]
        save(items,FILES["items"])
        st.success("Item Added")
        st.experimental_rerun()

    st.dataframe(items)

# ================= DEPARTMENT MASTER =================
elif menu=="Department Master" and role=="Store":
    st.header("Department Master")
    dept = st.text_input("Department Name")

    if st.button("Add Department"):
        depts.loc[len(depts)] = [dept]
        pll.loc[len(pll)] = [dept,"",0]
        save(depts,FILES["depts"])
        save(pll,FILES["pll"])
        st.success("Department & PLL Created")
        st.experimental_rerun()

    st.dataframe(depts)

# ================= S-156 ISSUE =================
elif menu=="S-156 Issue" and role=="Store":
    st.header("S-156 Issue")
    item = st.selectbox("Item",items[items["Type"]=="Permanent"]["Item"])
    dept = st.selectbox("Department",depts["Department"])
    qty = st.number_input("Quantity",1)

    if st.button("Raise S-156"):
        s156.loc[len(s156)] = [item,dept,qty,"Pending"]
        save(s156,FILES["s156"])
        st.success("S-156 Raised")

    st.dataframe(s156)

# ================= APPROVALS =================
elif menu=="Approvals":
    st.header("Approvals")

    if role=="Department":
        data = s156[s156["Department"]==user_dept]
    else:
        data = s156

    for i,row in data.iterrows():
        st.write(row.to_dict())

        if role=="Department" and row["Status"]=="Pending":
            if st.button(f"Dept Approve {i}",key=f"d{i}"):
                s156.at[i,"Status"]="Dept Approved"
                save(s156,FILES["s156"])
                st.experimental_rerun()

        if role=="Admin" and row["Status"]=="Dept Approved":
            if st.button(f"Admin Approve {i}",key=f"a{i}"):
                s156.at[i,"Status"]="Approved"
                item_row = items[items["Item"]==row["Item"]].iloc[0]

                ledger.loc[len(ledger)] = [
                    row["Item"],item_row["Ledger"],
                    item_row["Folio"],row["Department"],row["Qty"]
                ]

                pll.loc[len(pll)] = [row["Department"],row["Item"],row["Qty"]]

                save(s156,FILES["s156"])
                save(ledger,FILES["ledger"])
                save(pll,FILES["pll"])
                st.success("Ledger & PLL Updated")
                st.experimental_rerun()

# ================= LEDGER =================
elif menu=="Ledger":
    st.header("Ledger")
    st.dataframe(ledger)

# ================= PLL =================
elif menu=="PLL":
    st.header("Permanent Loan Ledger")
    st.dataframe(pll)

# ================= CONSUMABLE SUMMARY =================
elif menu=="Consumable Summary" and role=="Store":
    st.header("Consumable Summary")
    item = st.selectbox("Consumable Item",items[items["Type"]=="Consumable"]["Item"])
    dept = st.selectbox("Department",depts["Department"])
    qty = st.number_input("Quantity",1)

    if st.button("Add Summary"):
        summary.loc[len(summary)] = [item,dept,qty]
        save(summary,FILES["summary"])
        st.success("Summary Updated")

    st.dataframe(summary)

# ================= RETURN =================
elif menu=="Return Item" and role=="Department":
    st.header("Return Item")
    dept_pll = pll[pll["Department"]==user_dept]
    item = st.selectbox("Item",dept_pll["Item"])
    max_qty = int(dept_pll[dept_pll["Item"]==item]["Qty"].values[0])
    qty = st.number_input("Qty",1,max_qty)

    if st.button("Submit Return"):
        returns.loc[len(returns)] = [user_dept,item,qty,"Pending"]
        save(returns,FILES["returns"])
        st.success("Return Requested")

# ================= SURVEY =================
elif menu=="Survey" and role=="Store":
    st.header("Survey")
    item = st.selectbox("Item",items["Item"])
    dept = st.selectbox("Department",depts["Department"])
    qty = st.number_input("Qty",1)
    ref = st.text_input("Survey Ref")

    if st.button("Initiate Survey"):
        survey.loc[len(survey)] = [item,dept,qty,ref,"Pending"]
        save(survey,FILES["survey"])
        st.success("Survey Initiated")

# ================= WRITE-OFF =================
elif menu=="Write-Off" and role=="Admin":
    st.header("Write-Off")

    for i,row in survey[survey["Status"]=="Pending"].iterrows():
        st.write(row.to_dict())
        if st.button(f"Approve Write-Off {i}",key=f"w{i}"):
            survey.at[i,"Status"]="Approved"
            writeoff.loc[len(writeoff)] = [
                row["Item"],row["Department"],
                row["Qty"],row["SurveyRef"],"Approved"
            ]
            pll.loc[
                (pll["Department"]==row["Department"]) &
                (pll["Item"]==row["Item"]),
                "Qty"
            ] -= row["Qty"]

            save(survey,FILES["survey"])
            save(writeoff,FILES["writeoff"])
            save(pll,FILES["pll"])
            st.success("Item Written Off")
            st.experimental_rerun()


