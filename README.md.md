# 📊 Student Attendance Dashboard

A Streamlit-based web application for managing and visualizing student attendance.  
Includes role-based access:
- **Teacher**: Upload attendance data, view all records, send automated email warnings, and view analytics.
- **Parent**: View only their child's attendance and subject-wise breakdown.

---

## **Features**
- Upload CSV attendance records.
- Automated email warnings for students with <80% attendance.
- Email log stored locally as `email_log.csv`.
- Predictive model for estimating future attendance.
- Role-based access: 
  - Teachers (full access)  
  - Parents (view only their child's data).

---

## **How to Run Locally**

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/student-attendance-dashboard.git
cd student-attendance-dashboard
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
streamlit run app.py
```

---

## **Usage**
- **Teacher Login:**  
  - Username: `teacher1`  
  - Password: `teacher123`  
- **Parent:** Just enter your child's name to view their attendance.

---

## **Deployment**
This app can be deployed on [Streamlit Cloud](https://streamlit.io/cloud).  
After linking your GitHub repository:
1. Select `app.py` as the main file.
2. Click **Deploy**.

---

## **Project Structure**
```
student-attendance-dashboard/
│
├── app.py                # Main Streamlit app
├── requirements.txt      # Dependencies
└── README.md             # Project documentation
```

---

## **Author**
Developed by **Vinit Puri**  
*Made using Streamlit, Python & Pandas*
