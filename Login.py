import streamlit as st
import mysql.connector
import hashlib
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt


# ---------------------- DATABASE ----------------------
def db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Shadow@44",
        database="cqms_db"
    )


# ---------------------- HELPERS ----------------------
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()


def query_db(sql, values=None, fetch=False, dict_cursor=False):
    try:
        conn = db()
        cursor = conn.cursor(dictionary=dict_cursor)
        cursor.execute(sql, values or ())
        if fetch:
            result = cursor.fetchall()
            cursor.close()
            conn.close()
            return result
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        st.error(f"Database Error: {e}")
        return None


# ---------------------- AUTH ----------------------
def register_user(username, password, role):
    exists = query_db(
        "SELECT * FROM users WHERE username=%s",
        (username,), fetch=True
    )
    if exists:
        st.warning("Username already exists.")
        return False

    hashed = hash_password(password)
    return query_db(
        "INSERT INTO users (username, hashed_password, role) VALUES (%s,%s,%s)",
        (username, hashed, role)
    )


def verify_login(username, password):
    hashed = hash_password(password)
    user = query_db(
        "SELECT * FROM users WHERE username=%s AND hashed_password=%s",
        (username, hashed),
        fetch=True, dict_cursor=True
    )
    return user[0] if user else None


# ---------------------- QUERY ACTIONS ----------------------
def insert_query(email, mobile, heading, desc, creator):
    return query_db("""
        INSERT INTO queries(email,mobile,query_heading,query_description,query_created_time,status,created_by)
        VALUES (%s,%s,%s,%s,%s,'Open',%s)
    """, (email, mobile, heading, desc, datetime.now(), creator))


def get_queries(status=None):
    if status and status != "All":
        return query_db(
            "SELECT * FROM queries WHERE status=%s ORDER BY query_created_time DESC",
            (status,), fetch=True, dict_cursor=True
        )
    return query_db(
        "SELECT * FROM queries ORDER BY query_created_time DESC",
        fetch=True, dict_cursor=True
    )


def update_status(q_id, status):
    if status == "Closed":
        return query_db(
            "UPDATE queries SET status=%s, query_closed_time=%s WHERE id=%s",
            (status, datetime.now(), q_id)
        )
    return query_db(
        "UPDATE queries SET status=%s, query_closed_time=NULL WHERE id=%s",
        (status, q_id)
    )


# ---------------------- UI ----------------------
st.set_page_config(page_title="Client Query Management System", layout="wide")
st.title("Client Query Management System")

menu = st.sidebar.selectbox("Menu", ["Register", "Login"])


# ---------------------- REGISTER ----------------------
if menu == "Register":
    st.header("Create Account")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    r = st.selectbox("Role", ["Client", "Support"])

    if st.button("Register"):
        if u and p:
            if register_user(u, p, r):
                st.success("Registration successful! You may login.")
        else:
            st.warning("Fill all fields.")


# ---------------------- LOGIN ----------------------
elif menu == "Login":
    st.header("Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        user = verify_login(u, p)
        if user:
            st.session_state['user'] = user
            st.success(f"Welcome {user['username']}")
        else:
            st.error("Incorrect username or password.")


# ==========================================================
#     MAIN APP (AFTER LOGIN)
# ==========================================================
if 'user' in st.session_state:
    user = st.session_state['user']
    role = user['role']

    st.sidebar.markdown(f"**Logged in as:** {user['username']} ({role})")
    if st.sidebar.button("Logout"):
        st.session_state.clear()
        st.rerun()

    # ---------------------- CLIENT PAGE ----------------------
    if role == "Client":
        st.header("Submit Query")

        with st.form("qform"):
            email = st.text_input("Email")
            mobile = st.text_input("Mobile")
            heading = st.text_input("Query Heading")
            desc = st.text_area("Query Description")
            submit = st.form_submit_button("Submit")

        if submit:
            if email and mobile and heading and desc:
                insert_query(email, mobile, heading, desc, user['username'])
                st.success("Query submitted.")
            else:
                st.warning("Fill all fields.")

        st.markdown("---")
        st.subheader("My Queries")

        df = pd.DataFrame(get_queries())
        df = df[df['created_by'] == user['username']]

        if df.empty:
            st.info("No queries found.")
        else:
            st.dataframe(df.sort_values("query_created_time", ascending=False))


    # ---------------------- SUPPORT PAGE ----------------------
    elif role == "Support":
        st.header("Support Dashboard")

        # FILTER
        status = st.selectbox("Filter by Status", ["All", "Open", "Closed", "In Progress"])
        rows = get_queries(status)
        df = pd.DataFrame(rows)

        # ---------------------- SUPPORT LOAD CHART ----------------------
        st.subheader("Support Load (Matplotlib)")

        if not df.empty:
            load = df.groupby("created_by").size().reset_index(name="query_count")

            if not load.empty:
                fig, ax = plt.subplots()
                ax.bar(load["created_by"], load["query_count"])
                ax.set_xlabel("User")
                ax.set_ylabel("Queries")
                ax.set_title(f"Support Load - Showing: {status} Queries")
                st.pyplot(fig)
            else:
                st.info("No data available for this status filter.")
        else:
            st.info("No data found for this filter.")

        # ---------------------- EDIT STATUS TABLE ----------------------
        st.markdown("---")
        st.subheader("Update Query Status")

        if not df.empty:
            for _, row in df.iterrows():
             with st.container():
                 st.write(f"### Query ID: {row['id']}")
                 st.write(f"**Heading:** {row['query_heading']}")
                 st.write(f"**Description:** {row['query_description']}")
                 st.write(f"**Status:** {row['status']}")
                 st.write(f"**Created By:** {row['created_by']}")
                 st.write(f"**Created On:** {row['query_created_time']}")

            # ✅ Close button (only shown if query is NOT already closed)
                 if row["status"] != "Closed":
                    if st.button(f"Close Query {row['id']}"):
                        update_status(row["id"], "Closed")
                        st.success(f"Query {row['id']} closed successfully.")
                        st.rerun()

                 st.markdown("---")
else:
    st.info("No queries to display.")