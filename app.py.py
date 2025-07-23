import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from sklearn.linear_model import LinearRegression
import os

# ---------- CONSTANTS ----------
LOG_FILE_PATH = "email_log.csv"

# ---------- LOAD EXISTING LOG IF AVAILABLE ----------
if os.path.exists(LOG_FILE_PATH):
    st.session_state.email_log = pd.read_csv(LOG_FILE_PATH)
else:
    st.session_state.email_log = pd.DataFrame(columns=["Student Name", "Parent Email", "Date Sent"])

# ---------- SESSION STATES ----------
if "role" not in st.session_state:
    st.session_state.role = None
if "student_name" not in st.session_state:
    st.session_state.student_name = None
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ---------- LOGOUT ----------
if st.session_state.authenticated:
    if st.button("Logout"):
        st.session_state.role = None
        st.session_state.student_name = None
        st.session_state.authenticated = False
        st.rerun()

# ---------- LOGIN ----------
if not st.session_state.authenticated:
    st.title("🔐 Attendance Dashboard Login")
    role = st.radio("Select User Type:", ["Teacher", "Parent"])

    if role == "Teacher":
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login as Teacher"):
            if username == "teacher1" and password == "teacher123":
                st.session_state.role = "teacher"
                st.session_state.authenticated = True
                st.success("Logged in as Teacher")
                st.rerun()
            else:
                st.error("Invalid teacher credentials")

    elif role == "Parent":
        student_name = st.text_input("Enter Your Child's Full Name")
        if st.button("View Attendance"):
            if student_name.strip() == "":
                st.warning("Please enter your child's name")
            else:
                st.session_state.role = "parent"
                st.session_state.student_name = student_name.strip()
                st.session_state.authenticated = True
                st.success(f"Viewing attendance for {student_name}")
                st.rerun()

# ---------- STOP IF NOT LOGGED IN ----------
if not st.session_state.authenticated:
    st.stop()

st.title("📊 Student Attendance Dashboard")

# ====================== TEACHER VIEW ======================
if st.session_state.role == "teacher":
    uploaded_file = st.file_uploader("Upload Attendance CSV", type="csv")
    if uploaded_file is not None:
        st.session_state.data = pd.read_csv(uploaded_file)
        st.success("Attendance data uploaded successfully!")

    if "data" in st.session_state:
        data = st.session_state.data

        # ---- Attendance Calculation ----
        attendance_cols = [col for col in data.columns if "Day" in col]
        data["Total classes"] = len(attendance_cols)
        data["Classes Attended"] = data[attendance_cols].sum(axis=1)
        data["Attendance Percentage"] = (data["Classes Attended"] / data["Total classes"]) * 100

        def remarks(percent):
            if percent >= 80:
                return "Good"
            elif percent >= 60:
                return "Warning"
            else:
                return "Debarr"
        data["Status"] = data["Attendance Percentage"].apply(remarks)

        # ---- Display Processed Data ----
        st.subheader("Processed Attendance Data")
        st.dataframe(data[["Roll No", "Name", "Subject", "Attendance Percentage", "Status"]])

        # ---- Email Warning Section ----
        st.subheader("Send Warning Emails (for all <80% Attendance)")
        low_attendance = data[data["Attendance Percentage"] < 80]

        with st.form("email_form"):
            sender_email = st.text_input("Sender Gmail Address")
            app_password = st.text_input("Gmail App Password", type="password")
            st.write(f"{len(low_attendance)} students found with attendance <80%")
            parent_emails = {}

            for _, row in low_attendance.iterrows():
                if "Parent Email" in data.columns and pd.notna(row.get("Parent Email", None)):
                    parent_emails[row["Name"]] = row["Parent Email"]
                else:
                    parent_emails[row["Name"]] = st.text_input(f"Enter Parent Email for {row['Name']}")

            submitted = st.form_submit_button("Send All Emails")

        if submitted:
            if sender_email and app_password:
                sent_count = 0
                for _, row in low_attendance.iterrows():
                    parent_email = parent_emails[row["Name"]]
                    if not parent_email:
                        st.warning(f"No parent email for {row['Name']} - email skipped")
                        continue

                    subject = f"Official Attendance Warning Notice for {row['Name']}"
                    body = f"""
                    <html>
                        <body style="font-family: Arial, sans-serif; font-size: 14px; color: #333;">
                            <p>Dear Parent/Guardian,</p>
                            <p>Your ward, <strong>{row['Name']}</strong>, has an attendance of <strong>{row['Attendance Percentage']:.2f}%</strong>, below the mandatory <strong>80%</strong>.</p>
                            <p>Continued low attendance may lead to <strong>serious academic consequences</strong>.</p>
                            <p><strong>This is an official warning and requires your urgent attention.</strong></p>
                            <p>Regards,<br>Course Coordinator<br>[Institution Name]</p>
                        </body>
                    </html>
                    """

                    message = MIMEMultipart("alternative")
                    message["From"] = sender_email
                    message["To"] = parent_email
                    message["Subject"] = subject
                    message.attach(MIMEText(body, "html"))

                    try:
                        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
                            server.login(sender_email, app_password)
                            server.sendmail(sender_email, parent_email, message.as_string())
                        sent_count += 1

                        # ---- Log entry (local CSV) ----
                        new_log_entry = pd.DataFrame(
                            [[row['Name'], parent_email, datetime.now().strftime("%Y-%m-%d %I:%M %p")]],
                            columns=["Student Name", "Parent Email", "Date Sent"]
                        )
                        st.session_state.email_log = pd.concat([st.session_state.email_log, new_log_entry], ignore_index=True)
                        if not os.path.isfile(LOG_FILE_PATH):
                            new_log_entry.to_csv(LOG_FILE_PATH, index=False)
                        else:
                            new_log_entry.to_csv(LOG_FILE_PATH, mode='a', header=False, index=False)

                    except Exception as e:
                        st.error(f"Failed to send email to {parent_email}: {e}")
                st.success(f"✅ {sent_count} emails sent successfully.")
            else:
                st.warning("Please enter Gmail & App Password to send emails")

        # ---- Show Local Email Logs ----
        if not st.session_state.email_log.empty:
            st.subheader("Email Log (Saved Locally)")
            st.dataframe(st.session_state.email_log)

# ====================== PARENT VIEW ======================
elif st.session_state.role == "parent":
    if "data" not in st.session_state:
        st.error("No data found. Please contact the teacher.")
        st.stop()

    data = st.session_state.data

    # ---- Find Student ----
    student_data = data[data["Name"].str.lower() == st.session_state.student_name.lower()]
    if student_data.empty:
        st.warning(f"No data found for {st.session_state.student_name}")
        st.stop()

    st.subheader(f"Attendance for {st.session_state.student_name}")
    st.dataframe(student_data[["Roll No", "Name", "Subject", "Attendance Percentage", "Status"]])

    # ---- Subject-wise Attendance ----
    subject_attendance = student_data.groupby("Subject")["Attendance Percentage"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(7, 5))
    sns.barplot(x="Subject", y="Attendance Percentage", data=subject_attendance, ax=ax)
    plt.xticks(rotation=45)
    ax.set_title(f"{st.session_state.student_name} - Attendance by Subject")
    st.pyplot(fig)

    # ---- Predicted Attendance ----
    june_days = [col for col in data.columns if "Day" in col and "June" in col]
    july_days = [col for col in data.columns if "Day" in col and "July" in col]
    august_days = [col for col in data.columns if "Day" in col and "August" in col]

    def calc_percentage(row, day_cols):
        return (row[day_cols].sum() / len(day_cols)) * 100 if len(day_cols) > 0 else 0

    student_data = student_data.copy()
    student_data["June Attendance"] = student_data.apply(lambda r: calc_percentage(r, june_days), axis=1)
    student_data["July Attendance"] = student_data.apply(lambda r: calc_percentage(r, july_days), axis=1)
    student_data["August Attendance"] = student_data.apply(lambda r: calc_percentage(r, august_days), axis=1)

    X = student_data[["June Attendance", "July Attendance", "August Attendance"]]
    y = student_data["August Attendance"]
    model = LinearRegression()
    model.fit(X, y)
    student_data["Predicted September Attendance"] = model.predict(X).clip(0, 100).round(2)

    st.subheader("Predicted September Attendance")
    st.dataframe(student_data[["Roll No", "Name", "Predicted September Attendance"]])

# ---------- WATERMARK ----------
st.markdown(
    """
    <style>
    .watermark {
        position: fixed;
        bottom: 10px;
        right: 20px;
        opacity: 0.6;
        font-size: 14px;
        color: gray;
    }
    </style>
    <div class="watermark">Made by Vinit Puri</div>
    """,
    unsafe_allow_html=True
)
