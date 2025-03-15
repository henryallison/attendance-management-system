import streamlit as st
import mysql.connector
from mysql.connector import Error
import random
import string
import smtplib
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import timedelta  # Import timedelta
from datetime import timedelta
import pandas as pd  # Import pandas for efficient table handling
from streamlit_lottie import st_lottie
import requests




# Add this to your custom CSS
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap" rel="stylesheet">
    <style>
    body {
        font-family: 'Roboto', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True)
# Custom CSS for modern design
st.markdown(
    """
    <style>
    /* Main background color */
    .stApp {
        background-color: #f0f2f6;
    }

    /* Sidebar background color */
    .css-1d391kg {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }

    /* Title and header styling */
    h1, h2, h3, h4, h5, h6 {
        color: #2c3e50;
        font-family: 'Arial', sans-serif;
        text-align:center;
    }

    /* Button styling */
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 10px 20px;
        border: none;
        font-size: 16px;
        transition: background-color 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #45a049;
    }

    /* Input field styling */
    .stTextInput>div>div>input, .stSelectbox>div>div>select {
        border-radius: 5px;
        border: 1px solid #ccc;
        padding: 10px;
        font-size: 16px;
    }

    /* Table styling */
    .stDataFrame {
        border-radius: 5px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }

    /* Animation for buttons */
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.05); }
        100% { transform: scale(1); }
    }       
    /* Add this to your custom CSS */
    @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
    }

    .stApp {
    animation: fadeIn 1s ease-in-out;
    }

    /* Hover effect for buttons */
    .stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    
    .stButton>button:active {
        animation: pulse 0.3s;
    }
    /* Add this to your custom CSS */
    .stApp {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    /* Add this to your custom CSS */
    .stTextInput>div>div>input, .stSelectbox>div>div>select {
    border-radius: 10px;
    border: 1px solid #ccc;
    padding: 10px;
    font-size: 16px;
    transition: box-shadow 0.3s ease;
    }

    .stTextInput>div>div>input:focus, .stSelectbox>div>div>select:focus {
    box-shadow: 0 0 8px rgba(52, 152, 219, 0.6);
    border-color: #3498db;
    }
    .sidebar-footer {
    text-align: center;
    padding: 10px;
    font-family: 'Roboto', sans-serif;
    font-size: 12px;
    color: #666;
    border-top: 1px solid #e0e0e0;
    margin-top: auto;
    }

    .sidebar-footer a {
    color: #4CAF50;
    text-decoration: none;
    font-weight: bold;
    }

    .sidebar-footer a:hover {
    text-decoration: underline;
    }
    </style>
    """,
    unsafe_allow_html=True)

# Database connection details
DB_CONFIG = {
    "host": "gateway01.us-west-2.prod.aws.tidbcloud.com",
    "port": 4000,
    "user": "gkP4WFUHJw7TX88.root",
    "password": "9yVCpzqSMgbRuv7r",
    "database": "test"
}


# Function to create a database connection
def create_connection():
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        st.error(f"Error connecting to TiDB: {e}")
        return None

# Admin: Add Course
# Admin: Add Course
def add_course():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()

        # Fetch existing lecturers for the dropdown
        cursor.execute("SELECT lecturer_id, name, email FROM Lecturer")
        lecturers = cursor.fetchall()
        lecturer_options = {lecturer[0]: (lecturer[1], lecturer[2]) for lecturer in lecturers}  # {lecturer_id: (lecturer_name, lecturer_email)}

        if not lecturer_options:
            st.warning("No lecturers found. Please add a lecturer first.")
            return

        # Input fields for adding a new course
        course_name = st.text_input("Course Name")
        selected_lecturer_id = st.selectbox(
            "Select Lecturer",
            options=list(lecturer_options.keys()),
            format_func=lambda x: lecturer_options[x][0]  # Display lecturer names in the dropdown
        )
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")

        if st.button("Add Course"):
            # Check if any field is empty
            if not course_name or not selected_lecturer_id or not start_date or not end_date:
                st.error("All fields are required. Please fill in all the details.")
                return

            try:
                # Insert the new course into the database
                query = "INSERT INTO Course (course_name, lecturer_id, start_date, end_date) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (course_name, selected_lecturer_id, start_date, end_date))
                connection.commit()
                st.success("Course added successfully!")

                # Fetch lecturer details for the email
                lecturer_name, lecturer_email = lecturer_options[selected_lecturer_id]
                course_duration = f"{start_date} to {end_date}"

                # Send email to the lecturer
                lecturer_email_notification(
                    lecturer_email,
                    lecturer_name,
                    course_name,
                    course_duration
                )
            except mysql.connector.errors.IntegrityError as e:
                if "course_name" in str(e.msg).lower():  # Check if the error is related to the course name
                    st.error("A course with this name already exists.")
                else:
                    st.error(f"An error occurred: {e}")
            finally:
                cursor.close()
                connection.close()

def lecturer_email_notification(to_email, lecturer_name, course_name, course_duration):
    """Send an email to the lecturer notifying them of the new course."""
    sender_email = "hyallison5050@gmail.com"  # Replace with your email
    sender_password = "najl nxec rten eibs"  # Replace with your app password

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "New Course Assignment"

    # Add the message body
    body = f"""
    Dear {lecturer_name},

    You have been assigned to teach a new course: {course_name}.
    The course duration is {course_duration}.

    Please review the course details and prepare accordingly.

    Best regards,
    Admin Team
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        # Send the email using Gmail's SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        st.success(f"Email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# Admin: Update Course
def update_course():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()

        # Fetch existing courses for the dropdown
        cursor.execute("SELECT course_id, course_name FROM Course")
        courses = cursor.fetchall()
        course_options = {course[0]: course[1] for course in courses}  # {course_id: course_name}

        if not course_options:
            st.warning("No courses found. Please add a course first.")
            return

        # Dropdown to select a course to update
        selected_course_id = st.selectbox(
            "Select a Course to Update",
            options=list(course_options.keys()),
            format_func=lambda x: course_options[x]  # Display course names in the dropdown
        )

        # Fetch current course details
        cursor.execute("SELECT course_name, lecturer_id, start_date, end_date FROM Course WHERE course_id = %s", (selected_course_id,))
        current_course_details = cursor.fetchone()

        if current_course_details:
            # Fetch existing lecturers for the dropdown
            cursor.execute("SELECT lecturer_id, name, email FROM Lecturer")
            lecturers = cursor.fetchall()
            lecturer_options = {lecturer[0]: (lecturer[1], lecturer[2]) for lecturer in lecturers}  # {lecturer_id: (lecturer_name, lecturer_email)}

            if not lecturer_options:
                st.warning("No lecturers found. Please add a lecturer first.")
                return

            # Dropdown to select a lecturer
            selected_lecturer_id = st.selectbox(
                "Select a Lecturer",
                options=list(lecturer_options.keys()),
                format_func=lambda x: lecturer_options[x][0]  # Display lecturer names in the dropdown
            )

            # Display current course details and allow updates
            st.write("Current Course Details:")
            st.write(f"Course Name: {current_course_details[0]}")
            st.write(f"Lecturer: {lecturer_options.get(current_course_details[1], ('N/A', 'N/A'))[0]}")
            st.write(f"Start Date: {current_course_details[2]}")
            st.write(f"End Date: {current_course_details[3]}")

            # Input fields for updating the course
            new_course_name = st.text_input("New Course Name", value=current_course_details[0])
            new_start_date = st.date_input("New Start Date", value=current_course_details[2])
            new_end_date = st.date_input("New End Date", value=current_course_details[3])

            if st.button("Update Course"):
                # Check if all fields are filled
                if not new_course_name or not new_start_date or not new_end_date or not selected_lecturer_id:
                    st.error("All fields are required. Please fill in all the details.")
                    return

                # Check if the lecturer is being changed
                current_lecturer_id = current_course_details[1]
                if selected_lecturer_id == current_lecturer_id:
                    st.warning("The course is already assigned to this lecturer. No changes made.")
                else:
                    # Fetch previous lecturer details
                    previous_lecturer_name, previous_lecturer_email = lecturer_options.get(current_lecturer_id, ("N/A", "N/A"))

                    # Fetch new lecturer details
                    new_lecturer_name, new_lecturer_email = lecturer_options[selected_lecturer_id]

                    # Update the course in the database
                    query = "UPDATE Course SET course_name = %s, lecturer_id = %s, start_date = %s, end_date = %s WHERE course_id = %s"
                    cursor.execute(query, (new_course_name, selected_lecturer_id, new_start_date, new_end_date, selected_course_id))
                    connection.commit()
                    st.success("Course updated successfully!")

                    # Send unassignment email to the previous lecturer
                    if previous_lecturer_email != "N/A":
                        unassignment_email(
                            previous_lecturer_email,
                            previous_lecturer_name,
                            current_course_details[0]  # Current course name
                        )

                    # Send assignment email to the new lecturer
                    assignment_email(
                        new_lecturer_email,
                        new_lecturer_name,
                        new_course_name,
                        f"{new_start_date} to {new_end_date}"  # Course duration
                    )
        else:
            st.error("Course not found.")

        cursor.close()
        connection.close()

def assignment_email(to_email, lecturer_name, course_name, course_duration):
    """Send an email to the lecturer notifying them of their assignment to the course."""
    sender_email = "hyallison5050@gmail.com"  # Replace with your email
    sender_password = "najl nxec rten eibs"  # Replace with your app password

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "New Course Assignment"

    # Add the message body
    body = f"""
    Dear {lecturer_name},

    You have been assigned to teach a new course: {course_name}.
    The course duration is {course_duration}.

    Please review the course details and prepare accordingly.

    Best regards,
    Admin Team
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        # Send the email using Gmail's SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        st.success(f"Assignment email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send assignment email: {e}")

def unassignment_email(to_email, lecturer_name, course_name):
    """Send an email to the lecturer notifying them of their unassignment from the course."""
    sender_email = "hyallison5050@gmail.com"  # Replace with your email
    sender_password = "najl nxec rten eibs"  # Replace with your app password

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Course Unassignment Notification"

    # Add the message body
    body = f"""
    Dear {lecturer_name},

    You have been unassigned from the course: {course_name}.

    If you have any questions, please contact the admin team.

    Best regards,
    Admin Team
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        # Send the email using Gmail's SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        st.success(f"Unassignment email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send unassignment email: {e}")

# Admin: Add Student
# Admin: Add Student
def add_student(name, registration_number, email):
    # Check if any field is empty
    if not name or not registration_number or not email:
        st.error("All fields are required. Please fill in all the details.")
        return

    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            query = "INSERT INTO Student (name, registration_number, email) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, registration_number, email))
            connection.commit()
            st.success("Student added successfully!")
        except mysql.connector.errors.IntegrityError as e:
            if "email" in str(e.msg).lower():  # Check if the error is related to the email
                st.error("A student with this email already exists.")
            elif "registration_number" in str(e.msg).lower():  # Check if the error is related to the registration number
                st.error("A student with this registration number already exists.")
            else:
                st.error(f"An error occurred: {e}")
        finally:
            cursor.close()
            connection.close()

# Admin: Update Student
# Admin: Update Student
def update_student():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()

        # Fetch existing students for the dropdown
        cursor.execute("SELECT student_id, name FROM Student")
        students = cursor.fetchall()
        student_options = {student[0]: student[1] for student in students}  # {student_id: student_name}

        if not student_options:
            st.warning("No students found. Please add a student first.")
            return

        # Dropdown to select a student to update
        selected_student_id = st.selectbox(
            "Select a Student to Update",
            options=list(student_options.keys()),
            format_func=lambda x: student_options[x]  # Display student names in the dropdown
        )

        # Fetch current student details
        cursor.execute("SELECT name, registration_number, email FROM Student WHERE student_id = %s", (selected_student_id,))
        current_student_details = cursor.fetchone()

        if current_student_details:
            # Display current student details and allow updates
            st.write("Current Student Details:")
            st.write(f"Name: {current_student_details[0]}")
            st.write(f"Registration Number: {current_student_details[1]}")
            st.write(f"Email: {current_student_details[2]}")

            # Input fields for updating the student
            new_name = st.text_input("New Name", value=current_student_details[0])
            new_registration_number = st.text_input("New Registration Number", value=current_student_details[1])
            new_email = st.text_input("New Email", value=current_student_details[2])

            if st.button("Update Student"):
                # Check if any field is empty
                if not new_name or not new_registration_number or not new_email:
                    st.error("All fields are required. Please fill in all the details.")
                    return

                try:
                    # Update the student in the database
                    query = "UPDATE Student SET name = %s, registration_number = %s, email = %s WHERE student_id = %s"
                    cursor.execute(query, (new_name, new_registration_number, new_email, selected_student_id))
                    connection.commit()
                    st.success("Student updated successfully!")
                except mysql.connector.errors.IntegrityError as e:
                    if "email" in str(e.msg).lower():  # Check if the error is related to the email
                        st.error("A student with this email already exists.")
                    elif "registration_number" in str(e.msg).lower():  # Check if the error is related to the registration number
                        st.error("A student with this registration number already exists.")
                    else:
                        st.error(f"An error occurred: {e}")
        else:
            st.error("Student not found.")

        cursor.close()
        connection.close()

# Function to generate a random login key
def generate_login_key(length=8):
    """Generate a random alphanumeric login key of the specified length."""
    characters = string.ascii_letters + string.digits  # A-Z, a-z, 0-9
    return ''.join(random.choice(characters) for _ in range(length))

def is_valid_email(email):
    """Check if the email is in a valid format."""
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def update_email(to_email, lecturer_name, login_key):
    """Send an email to the lecturer with their login key."""
    sender_email = "hyallison5050@gmail.com"
    sender_password = "najl nxec rten eibs"  # App password for Gmail
    subject = "Ines Ruhengeri Student Attendance Management App Update"
    body = f"""
    Dear {lecturer_name},

    Your account has under go some changes.
    
    New Login Key: {login_key}

    Best regards,
    Admin Team
    """

    # Create the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        st.success(f"Email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def students_email(to_email, student_name, message):
    """Send an email to the student with the enrollment details."""
    sender_email = "hyallison5050@gmail.com"  # Replace with your email
    sender_password = "najl nxec rten eibs"  # Replace with your app password

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Enrollment Confirmation"

    # Add the message body
    body = f"""
    {message}
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        # Send the email using Gmail's SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        st.success(f"Email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")


# Function to send email
def send_email(to_email, lecturer_name, login_key):
    """Send an email to the lecturer with their login key."""
    sender_email = "hyallison5050@gmail.com"
    sender_password = "najl nxec rten eibs"  # App password for Gmail
    subject = "Welcome to Ines Ruhengeri Student Attendance Management App"
    body = f"""
    Dear {lecturer_name},

    You have just been added to the Ines Ruhengeri Student Attendance Management App. Below is your unique login key. Do not lose it.

    Login Key: {login_key}

    Best regards,
    Admin Team
    """

    # Create the email
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    try:
        # Send the email
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, message.as_string())
        st.success(f"Email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

# Admin: Add Lecturer
def add_lecturer():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()

        # Input fields for adding a new lecturer
        name = st.text_input("Lecturer Name")
        email = st.text_input("Lecturer Email")

        # Automatically generate a unique login key
        login_key = generate_login_key()

        # Display the generated login key (read-only)
        st.text_input("Generated Login Key", value=login_key, disabled=True)

        if st.button("Add Lecturer"):
            # Check if any field is empty
            if not name or not email:
                st.error("All fields are required. Please fill in all the details.")
                return

            # Validate email format
            if not is_valid_email(email):
                st.error("Invalid email format. Please enter a valid email address.")
                return

            try:
                # Check if the email already exists
                cursor.execute("SELECT email FROM Lecturer WHERE email = %s", (email,))
                if cursor.fetchone():
                    st.error("A lecturer with this email already exists.")
                    return

                # Ensure the generated login key is unique
                while True:
                    cursor.execute("SELECT login_key FROM Lecturer WHERE login_key = %s", (login_key,))
                    if not cursor.fetchone():
                        break  # Login key is unique
                    login_key = generate_login_key()  # Generate a new key if the current one exists

                # Insert the new lecturer into the database
                query = "INSERT INTO Lecturer (name, email, login_key) VALUES (%s, %s, %s)"
                cursor.execute(query, (name, email, login_key))
                connection.commit()
                st.success("Lecturer added successfully!")
                st.write(f"Generated Login Key: {login_key}")  # Display the login key to the admin

                # Send email to the lecturer
                send_email(email, name, login_key)
            except mysql.connector.errors.IntegrityError as e:
                st.error(f"An error occurred: {e}")
            finally:
                cursor.close()
                connection.close()

# Admin: Update Lecturer
# Admin: Update Lecturer
def update_lecturer():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()

        # Fetch existing lecturers for the dropdown
        cursor.execute("SELECT lecturer_id, name FROM Lecturer")
        lecturers = cursor.fetchall()
        lecturer_options = {lecturer[0]: lecturer[1] for lecturer in lecturers}  # {lecturer_id: lecturer_name}

        if not lecturer_options:
            st.warning("No lecturers found. Please add a lecturer first.")
            return

        # Dropdown to select a lecturer to update
        selected_lecturer_id = st.selectbox(
            "Select a Lecturer to Update",
            options=list(lecturer_options.keys()),
            format_func=lambda x: lecturer_options[x]  # Display lecturer names in the dropdown
        )

        # Fetch current lecturer details
        cursor.execute("SELECT name, email, login_key FROM Lecturer WHERE lecturer_id = %s", (selected_lecturer_id,))
        current_lecturer_details = cursor.fetchone()

        if current_lecturer_details:
            # Display current lecturer details and allow updates
            st.write("Current Lecturer Details:")
            st.write(f"Name: {current_lecturer_details[0]}")
            st.write(f"Email: {current_lecturer_details[1]}")
            st.write(f"Login Key: {current_lecturer_details[2]}")

            # Input fields for updating the lecturer
            new_name = st.text_input("New Name", value=current_lecturer_details[0])
            new_email = st.text_input("New Email", value=current_lecturer_details[1])
            new_login_key = st.text_input("New Login Key", value=current_lecturer_details[2])

            if st.button("Update Lecturer"):
                # Check if any field is empty
                if not new_name or not new_email or not new_login_key:
                    st.error("All fields are required. Please fill in all the details.")
                    return

                # Validate email format
                if not is_valid_email(new_email):
                    st.error("Invalid email format. Please enter a valid email address.")
                    return

                try:
                    # Check if the new email already exists (excluding the current lecturer)
                    cursor.execute("SELECT email FROM Lecturer WHERE email = %s AND lecturer_id != %s", (new_email, selected_lecturer_id))
                    if cursor.fetchone():
                        st.error("A lecturer with this email already exists.")
                        return

                    # Check if the new login key already exists (excluding the current lecturer)
                    cursor.execute("SELECT login_key FROM Lecturer WHERE login_key = %s AND lecturer_id != %s", (new_login_key, selected_lecturer_id))
                    if cursor.fetchone():
                        st.error("A lecturer with this login key already exists.")
                        return

                    # Update the lecturer in the database
                    query = "UPDATE Lecturer SET name = %s, email = %s, login_key = %s WHERE lecturer_id = %s"
                    cursor.execute(query, (new_name, new_email, new_login_key, selected_lecturer_id))
                    connection.commit()
                    st.success("Lecturer updated successfully!")

                    # Send email notification if email or login key is updated
                    if new_email != current_lecturer_details[1] or new_login_key != current_lecturer_details[2]:
                        update_email(
                            new_email,
                            new_name,
                            f"{new_login_key}"
                        )
                except mysql.connector.errors.IntegrityError as e:
                    st.error(f"An error occurred: {e}")
                finally:
                    cursor.close()
                    connection.close()
        else:
            st.error("Lecturer not found.")


# Admin: Enroll Student in Course
def enroll_student():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()

        # Fetch existing students for the dropdown
        cursor.execute("SELECT student_id, name, email FROM Student")
        students = cursor.fetchall()
        student_options = {student[0]: (student[1], student[2]) for student in students}  # {student_id: (name, email)}

        if not student_options:
            st.warning("No students found. Please add a student first.")
            return

        # Fetch existing courses for the dropdown
        cursor.execute("SELECT course_id, course_name, start_date, end_date FROM Course")
        courses = cursor.fetchall()
        course_options = {course[0]: (course[1], course[2], course[3]) for course in courses}  # {course_id: (course_name, start_date, end_date)}

        if not course_options:
            st.warning("No courses found. Please add a course first.")
            return

        # Dropdown to select a student
        selected_student_id = st.selectbox(
            "Select a Student",
            options=list(student_options.keys()),
            format_func=lambda x: student_options[x][0]  # Display student names in the dropdown
        )

        # Dropdown to select a course
        selected_course_id = st.selectbox(
            "Select a Course",
            options=list(course_options.keys()),
            format_func=lambda x: course_options[x][0]  # Display course names in the dropdown
        )

        if st.button("Enroll Student"):
            try:
                # Check if the student is already enrolled in the course
                cursor.execute("SELECT * FROM Enrollment WHERE student_id = %s AND course_id = %s", (selected_student_id, selected_course_id))
                if cursor.fetchone():
                    st.error("This student is already enrolled in the selected course.")
                    return

                # Enroll the student in the course
                query = "INSERT INTO Enrollment (student_id, course_id) VALUES (%s, %s)"
                cursor.execute(query, (selected_student_id, selected_course_id))
                connection.commit()
                st.success("Student enrolled successfully!")

                # Fetch student and course details for the email
                student_name, student_email = student_options[selected_student_id]
                course_name, start_date, end_date = course_options[selected_course_id]
                course_duration = f"{start_date} to {end_date}"

                # Send email to the student using the students_email function
                students_email(
                    student_email,
                    student_name,
                    f"Dear {student_name},\n\nYou have just been enrolled in {course_name}. The duration of the course is {course_duration}.\n\nBest regards,\nAdmin Team"
                )
            except mysql.connector.errors.IntegrityError as e:
                st.error(f"An error occurred: {e}")
            finally:
                cursor.close()
                connection.close()

# Admin: Update Enrollment
def update_enrollment(enrollment_id, student_id, course_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Update the enrollment
            query = "UPDATE Enrollment SET student_id = %s, course_id = %s WHERE enrollment_id = %s"
            cursor.execute(query, (student_id, course_id, enrollment_id))
            connection.commit()
            st.success("Enrollment updated successfully!")

            # Fetch all students enrolled in the updated course
            cursor.execute("""
                SELECT s.name, s.email 
                FROM Student s
                JOIN Enrollment e ON s.student_id = e.student_id
                WHERE e.course_id = %s
            """, (course_id,))
            enrolled_students = cursor.fetchall()

            # Fetch course details
            cursor.execute("SELECT course_name, start_date, end_date FROM Course WHERE course_id = %s", (course_id,))
            course_details = cursor.fetchone()
            if course_details:
                course_name, start_date, end_date = course_details
                course_duration = f"{start_date} to {end_date}"

                # Notify all enrolled students
                for student in enrolled_students:
                    student_name, student_email = student
                    message = f"""
                    Dear {student_name},

                    This is to inform you that there has been an update to the enrollment for the course: {course_name}.
                    The course duration is {course_duration}.

                    If you have any questions, please contact the admin team.

                    Best regards,
                    Admin Team
                    """
                    ustudent_email(student_email, student_name, message)  # Send email to each student

        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            cursor.close()
            connection.close()


def ustudent_email(to_email, student_name, message):
    """Send an email to the student with the enrollment details."""
    sender_email = "hyallison5050@gmail.com"  # Replace with your email
    sender_password = "najl nxec rten eibs"  # Replace with your app password

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Enrollment Update Notification"

    # Add the message body
    body = f"""
    {message}
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        # Send the email using Gmail's SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        st.success(f"Email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")
# Lecturer: Mark Attendance
def mark_attendance(student_id, course_id, date, status):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = "INSERT INTO Attendance (student_id, course_id, date, status) VALUES (%s, %s, %s, %s)"
        cursor.execute(query, (student_id, course_id, date, status))
        connection.commit()
        st.success("Attendance marked successfully!")
        cursor.close()
        connection.close()

def update_attendance(attendance_id, status):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = "UPDATE Attendance SET status = %s WHERE attendance_id = %s"
        cursor.execute(query, (status, attendance_id))
        connection.commit()
        st.success("Attendance updated successfully!")
        cursor.close()
        connection.close()

def lecturer_attendance():
    connection = create_connection()
    if connection:
        cursor = connection.cursor()

        # Fetch existing courses for the dropdown
        cursor.execute("SELECT course_id, course_name, start_date, end_date FROM Course")
        courses = cursor.fetchall()
        course_options = {course[0]: (course[1], course[2], course[3]) for course in courses}  # {course_id: (course_name, start_date, end_date)}

        if not course_options:
            st.warning("No courses found. Please add a course first.")
            return

        # Dropdown to select a course
        selected_course_id = st.selectbox(
            "Select a Course",
            options=list(course_options.keys()),
            format_func=lambda x: course_options[x][0]  # Display course names in the dropdown
        )

        # Fetch course details
        course_name, start_date, end_date = course_options[selected_course_id]

        # Fetch all students enrolled in the selected course
        cursor.execute("""
            SELECT s.student_id, s.name, s.registration_number 
            FROM Student s
            JOIN Enrollment e ON s.student_id = e.student_id
            WHERE e.course_id = %s
        """, (selected_course_id,))
        enrolled_students = cursor.fetchall()

        if not enrolled_students:
            st.warning("No students enrolled in this course.")
            return

        # Display enrolled students in a table
        st.write(f"Students Enrolled in {course_name}:")
        student_data = []
        for student in enrolled_students:
            student_id, name, registration_number = student
            # Fetch attendance history for the student
            cursor.execute("""
                SELECT attendance_id, date, status 
                FROM Attendance 
                WHERE student_id = %s AND course_id = %s
            """, (student_id, selected_course_id))
            attendance_history = cursor.fetchall()
            for record in attendance_history:
                student_data.append({
                    "Student Name": name,
                    "Registration Number": registration_number,
                    "Date": record[1],
                    "Attendance": record[2]
                })

        # Display the table
        st.table(student_data)

        # Dropdown to select a student
        selected_student_id = st.selectbox(
            "Select a Student",
            options=[student[0] for student in enrolled_students],
            format_func=lambda x: next(student[1] for student in enrolled_students if student[0] == x)  # Display student names in the dropdown
        )

        # Fetch attendance records for the selected student
        cursor.execute("""
            SELECT attendance_id, date, status 
            FROM Attendance 
            WHERE student_id = %s AND course_id = %s
        """, (selected_student_id, selected_course_id))
        attendance_records = cursor.fetchall()

        # Dropdown to select an attendance record to edit
        if attendance_records:
            selected_attendance_id = st.selectbox(
                "Select an Attendance Record to Edit",
                options=[record[0] for record in attendance_records],
                format_func=lambda x: f"{next(record[1] for record in attendance_records if record[0] == x)} - {next(record[2] for record in attendance_records if record[0] == x)}"
            )
        else:
            selected_attendance_id = None

        # Input fields for marking/updating attendance
        attendance_date = st.date_input("Attendance Date", min_value=start_date, max_value=end_date)
        attendance_status = st.selectbox("Attendance Status", ["Present", "Absent"])

        if st.button("Mark/Update Attendance"):
            # Check if all fields are filled
            if not attendance_date or not attendance_status:
                st.error("All fields are required. Please fill in all the details.")
                return

            if selected_attendance_id:
                # Update existing attendance
                update_attendance(selected_attendance_id, attendance_status)
            else:
                # Mark new attendance
                mark_attendance(selected_student_id, selected_course_id, attendance_date, attendance_status)

        cursor.close()
        connection.close()

# Lecturer: Generate Exam Eligibility Report
def generate_report(course_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = """
        SELECT s.name, COUNT(a.status) AS absences
        FROM Student s
        JOIN Enrollment e ON s.student_id = e.student_id
        LEFT JOIN Attendance a ON s.student_id = a.student_id AND a.course_id = %s AND a.status = 'Absent'
        WHERE e.course_id = %s
        GROUP BY s.student_id
        HAVING COUNT(a.status) < 2
        """
        cursor.execute(query, (course_id, course_id))
        result = cursor.fetchall()
        st.write("Students eligible to sit for the exam:")
        for row in result:
            st.write(row[0])
        cursor.close()
        connection.close()

# Admin Login
def admin_login(username, password):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        query = "SELECT admin_id FROM Admin WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        cursor.close()
        connection.close()
        if result:
            return True
    return False

def unenroll_email(to_email, student_name, course_name):
    """Send an email to the student notifying them of unenrollment."""
    sender_email = "hyallison5050@gmail.com"  # Replace with your email
    sender_password = "najl nxec rten eibs"  # Replace with your app password

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Unenrollment Notification"

    # Add the message body
    body = f"""
    Dear {student_name},

    This is to inform you that you have been unenrolled from the course: {course_name}.

    If you have any questions, please contact the admin team.

    Best regards,
    Admin Team
    """
    msg.attach(MIMEText(body, "plain"))

    try:
        # Send the email using Gmail's SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        st.success(f"Email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def unenroll_student(enrollment_id):
    connection = create_connection()
    if connection:
        cursor = connection.cursor()
        try:
            # Fetch student and course details before unenrolling
            cursor.execute("""
                SELECT s.name, s.email, c.course_name 
                FROM Enrollment e
                JOIN Student s ON e.student_id = s.student_id
                JOIN Course c ON e.course_id = c.course_id
                WHERE e.enrollment_id = %s
            """, (enrollment_id,))
            enrollment_details = cursor.fetchone()

            if enrollment_details:
                student_name, student_email, course_name = enrollment_details

                # Unenroll the student
                query = "DELETE FROM Enrollment WHERE enrollment_id = %s"
                cursor.execute(query, (enrollment_id,))
                connection.commit()
                st.success("Student unenrolled successfully!")

                # Send unenrollment email
                unenroll_email(student_email, student_name, course_name)
            else:
                st.error("Enrollment not found.")

        except Exception as e:
            st.error(f"An error occurred: {e}")
        finally:
            cursor.close()
            connection.close()
def astudent_email(to_email, student_name, message):
    """Send an email to the student with the attendance details."""
    sender_email = "hyallison5050@gmail.com"  # Replace with your email
    sender_password = "najl nxec rten eibs"  # Replace with your app password

    # Create the email
    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Attendance Record Notification"

    # Add the message body as HTML
    msg.attach(MIMEText(message, "html"))

    try:
        # Send the email using Gmail's SMTP server
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Secure the connection
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        st.success(f"Email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send email: {e}")

def main():
    st.title("Welcome to INES Ruhengeri students attendance Management System")
    menu = ["Admin", "Lecturer"]
    choice = st.sidebar.selectbox("Login As", menu)

    if choice == "Admin":
        # Only show the login form if the admin is not logged in
        if not st.session_state.get("admin_logged_in"):
            st.subheader("Admin Login")

            # Input fields for username and password with unique keys
            username = st.text_input("Username", key="admin_username_input")
            password = st.text_input("Password", type="password", key="admin_password_input")

            # Login button with a unique key
            if st.button("Login", key="admin_login_button"):
                # Form validation
                if not username or not password:
                    st.error("Please fill in all fields.")  # Show error if any field is empty
                else:
                    # Proceed with login logic if all fields are filled
                    if admin_login(username, password):
                        st.session_state.admin_logged_in = True
                        st.success("Logged in successfully!")
                        st.rerun()  # Rerun the app to reflect the changes
                    else:
                        st.error("Invalid username or password")
        else:
            # Show admin functionalities if logged in
            st.subheader("Admin Panel")
            admin_action = st.selectbox("Select Action",
                                        ["Add Course", "Update Course", "Add Student", "Update Student", "Add Lecturer",
                                         "Update Lecturer", "Enroll Student", "Update Enrollment", "Unenroll Student"],
                                        key="admin_action_selectbox")

            if admin_action == "Add Course":
                add_course()  # Call the function without arguments

            elif admin_action == "Update Course":
                update_course()  # Call the function without arguments

            elif admin_action == "Add Student":
                st.write("Add a New Student")
                name = st.text_input("Student Name", key="add_student_name_input")
                registration_number = st.text_input("Student Registration Number", key="add_student_registration_input")
                email = st.text_input("Student Email", key="add_student_email_input")
                if st.button("Add Student", key="add_student_button"):
                    add_student(name, registration_number, email)

            elif admin_action == "Update Student":
                update_student()  # Call the function without arguments

            elif admin_action == "Add Lecturer":
                add_lecturer()  # Call the function without arguments

            elif admin_action == "Update Lecturer":
                update_lecturer()  # Call the function without arguments

            elif admin_action == "Enroll Student":
                enroll_student()  # Call the function without arguments

            elif admin_action == "Update Enrollment":
                st.write("Update an Existing Enrollment")
                connection = create_connection()
                if connection:
                    cursor = connection.cursor()

                    # Fetch all enrollments for the dropdown
                    cursor.execute("""
                        SELECT e.enrollment_id, s.name AS student_name, c.course_name 
                        FROM Enrollment e
                        JOIN Student s ON e.student_id = s.student_id
                        JOIN Course c ON e.course_id = c.course_id
                    """)
                    enrollments = cursor.fetchall()
                    enrollment_options = {enrollment[0]: f"{enrollment[1]} - {enrollment[2]}" for enrollment in
                                          enrollments}  # {enrollment_id: "Student Name - Course Name"}

                    if not enrollment_options:
                        st.warning("No enrollments found. Please enroll a student first.")
                    else:
                        # Dropdown to select an enrollment to update
                        selected_enrollment_id = st.selectbox(
                            "Select an Enrollment to Update",
                            options=list(enrollment_options.keys()),
                            format_func=lambda x: enrollment_options[x],
                            # Display "Student Name - Course Name" in the dropdown
                            key="update_enrollment_selectbox"
                        )

                        # Fetch all students for the dropdown
                        cursor.execute("SELECT student_id, name FROM Student")
                        students = cursor.fetchall()
                        student_options = {student[0]: student[1] for student in
                                           students}  # {student_id: "Student Name"}

                        if not student_options:
                            st.warning("No students found. Please add a student first.")
                        else:
                            # Dropdown to select a new student
                            selected_student_id = st.selectbox(
                                "Select a New Student",
                                options=list(student_options.keys()),
                                format_func=lambda x: student_options[x],  # Display student names in the dropdown
                                key="update_student_selectbox"
                            )

                            # Fetch all courses for the dropdown
                            cursor.execute("SELECT course_id, course_name FROM Course")
                            courses = cursor.fetchall()
                            course_options = {course[0]: course[1] for course in courses}  # {course_id: "Course Name"}

                            if not course_options:
                                st.warning("No courses found. Please add a course first.")
                            else:
                                # Dropdown to select a new course
                                selected_course_id = st.selectbox(
                                    "Select a New Course",
                                    options=list(course_options.keys()),
                                    format_func=lambda x: course_options[x],  # Display course names in the dropdown
                                    key="update_course_selectbox"
                                )

                                if st.button("Update Enrollment", key="update_enrollment_button"):
                                    update_enrollment(selected_enrollment_id, selected_student_id, selected_course_id)

                    cursor.close()
                    connection.close()

            elif admin_action == "Unenroll Student":
                st.write("Unenroll a Student from a Course")
                connection = create_connection()
                if connection:
                    cursor = connection.cursor()

                    # Fetch all enrollments for the dropdown
                    cursor.execute("""
                        SELECT e.enrollment_id, s.name AS student_name, c.course_name 
                        FROM Enrollment e
                        JOIN Student s ON e.student_id = s.student_id
                        JOIN Course c ON e.course_id = c.course_id
                    """)
                    enrollments = cursor.fetchall()
                    enrollment_options = {enrollment[0]: f"{enrollment[1]} - {enrollment[2]}" for enrollment in
                                          enrollments}  # {enrollment_id: "Student Name - Course Name"}

                    if not enrollment_options:
                        st.warning("No enrollments found. Please enroll a student first.")
                    else:
                        # Dropdown to select an enrollment to unenroll
                        selected_enrollment_id = st.selectbox(
                            "Select an Enrollment to Unenroll",
                            options=list(enrollment_options.keys()),
                            format_func=lambda x: enrollment_options[x],
                            # Display "Student Name - Course Name" in the dropdown
                            key="unenroll_selectbox"
                        )

                        if st.button("Unenroll Student", key="unenroll_button"):
                            unenroll_student(selected_enrollment_id)

                    cursor.close()
                    connection.close()

            # Add a Logout Button
            if st.button("Logout", key="admin_logout_button"):
                st.session_state.admin_logged_in = False  # Reset the admin logged-in state
                st.success("Logged out successfully!")  # Show a success message
                st.rerun()  # Rerun the app to reflect the changes




    elif choice == "Lecturer":

        st.subheader("Lecturer Panel")

        # Initialize session state variables if they don't exist

        if "lecturer_logged_in" not in st.session_state:
            st.session_state.lecturer_logged_in = False

        if "lecturer_id" not in st.session_state:
            st.session_state.lecturer_id = None

        if "lecturer_name" not in st.session_state:
            st.session_state.lecturer_name = None

        if "selected_course_id" not in st.session_state:
            st.session_state.selected_course_id = None

        if not st.session_state.lecturer_logged_in:

            # Lecturer login form

            lecturer_key = st.text_input("Enter Your Login Key")

            if st.button("Login"):

                # Enhanced form validation

                if not lecturer_key:

                    st.error("Please enter your login key.")

                elif not lecturer_key.isalnum():  # Check if the login key is alphanumeric

                    st.error("Login key must be alphanumeric.")

                elif len(lecturer_key) != 8:  # Check if the login key is 8 characters long

                    st.error("Login key must be 8 characters long.")

                else:

                    # Proceed with login logic if the field is filled and valid

                    connection = create_connection()

                    if connection:

                        cursor = connection.cursor()

                        query = "SELECT lecturer_id, name FROM Lecturer WHERE login_key = %s"

                        cursor.execute(query, (lecturer_key,))

                        result = cursor.fetchone()

                        if result:

                            st.session_state.lecturer_id = result[0]

                            st.session_state.lecturer_name = result[1]

                            st.session_state.lecturer_logged_in = True

                            st.success(

                                f"Welcome {st.session_state.lecturer_name} to the INES Ruhengeri Student Management App!"

                            )

                        else:

                            st.error("Invalid Login Key")

                        cursor.close()

                        connection.close()

        else:

            # Lecturer is logged in

            st.success(f"Welcome {st.session_state.lecturer_name} to the INES Ruhengeri Student Management App!")

            # Fetch courses taught by the lecturer

            connection = create_connection()

            if connection:

                cursor = connection.cursor()

                query = "SELECT course_id, course_name, start_date, end_date FROM Course WHERE lecturer_id = %s"

                cursor.execute(query, (st.session_state.lecturer_id,))

                courses = cursor.fetchall()

                course_options = {course[0]: (course[1], course[2], course[3]) for course in
                                  courses}  # {course_id: (course_name, start_date, end_date)}

                if not course_options:

                    st.warning("No courses found for this lecturer.")

                else:

                    # Dropdown to select a course

                    selected_course_id = st.selectbox(

                        "Select Course",

                        options=list(course_options.keys()),

                        format_func=lambda x: course_options[x][0]  # Display course names in the dropdown

                    )

                    # Store the selected course ID in session state

                    st.session_state.selected_course_id = selected_course_id

                    # Fetch course details

                    if st.session_state.selected_course_id in course_options:

                        course_name, start_date, end_date = course_options[st.session_state.selected_course_id]

                        # Fetch all students enrolled in the selected course

                        cursor.execute("""

                                SELECT s.student_id, s.name, s.registration_number, s.email 

                                FROM Student s

                                JOIN Enrollment e ON s.student_id = e.student_id

                                WHERE e.course_id = %s

                            """, (st.session_state.selected_course_id,))

                        enrolled_students = cursor.fetchall()

                        if not enrolled_students:

                            st.warning("No students enrolled in this course.")

                        else:

                            # Fetch all attendance records for the selected course

                            cursor.execute("""

                                    SELECT student_id, date, status 

                                    FROM Attendance 

                                    WHERE course_id = %s AND date BETWEEN %s AND %s

                                """, (st.session_state.selected_course_id, start_date, end_date))

                            attendance_records = cursor.fetchall()

                            # Create a dictionary to store attendance data

                            attendance_dict = {}

                            for record in attendance_records:

                                student_id, date, status = record

                                if student_id not in attendance_dict:
                                    attendance_dict[student_id] = {}

                                attendance_dict[student_id][date] = status

                            # Generate all dates within the course duration

                            unique_dates = []

                            current_date = start_date

                            while current_date <= end_date:
                                unique_dates.append(current_date)

                                current_date += timedelta(days=1)

                            # Create a DataFrame for the attendance table

                            attendance_data = []

                            for student in enrolled_students:

                                student_id, name, registration_number, email = student

                                student_row = {"Student Name": name, "Registration Number": registration_number,
                                               "Email": email}

                                total_absent = 0

                                for date in unique_dates:

                                    status = attendance_dict.get(student_id, {}).get(date, "N/A")

                                    student_row[date] = status

                                    if status == "Absent":
                                        total_absent += 1

                                # Add "Allowed to sit for exam?" column

                                student_row["Allowed to sit for exam?"] = "Yes" if total_absent < 2 else "No"

                                attendance_data.append(student_row)

                            # Convert to DataFrame for better performance

                            df = pd.DataFrame(attendance_data)

                            # Display the table

                            st.write(f"Students Enrolled in {course_name}:")

                            st.dataframe(df)  # Use st.dataframe for better performance with large datasets

                            # Button to generate and submit the attendance list

                            # Button to generate and submit the attendance list
                            if st.button("Generate and Submit Attendance List"):
                                for student in enrolled_students:
                                    student_id, name, registration_number, email = student

                                    # Filter the DataFrame for the current student
                                    student_df = df[df["Student Name"] == name]

                                    # Convert the DataFrame to an HTML table
                                    attendance_table = student_df.to_html(index=False, border=1)

                                    # Prepare the email message in HTML format
                                    message = f"""
                                                               <html>
                                                                   <body>
                                                                       <p>Dear {name},</p>
                                                                       <p>Below is your attendance record for the course: <strong>{course_name}</strong>.</p>
                                                                       {attendance_table}
                                                                       <p><strong>Allowed to sit for exam?</strong> {"Yes" if student_df["Allowed to sit for exam?"].values[0] == "Yes" else "No"}</p>
                                                                       <p>Best regards,</p>
                                                                       <p>Admin Team</p>
                                                                   </body>
                                                               </html>
                                                               """

                                    # Send the email
                                    astudent_email(email, name, message)

                                st.success("Attendance list submitted to all students successfully!")
                            # Dropdown to select a student

                            selected_student_id = st.selectbox(

                                "Select a Student",

                                options=[student[0] for student in enrolled_students],

                                format_func=lambda x: next(
                                    student[1] for student in enrolled_students if student[0] == x)
                                # Display student names in the dropdown

                            )

                            # Toggle for updating or adding attendance

                            update_existing = st.checkbox("Update Existing Attendance Record")

                            if update_existing:

                                # Fetch attendance records for the selected student

                                cursor.execute("""

                                        SELECT attendance_id, date, status 

                                        FROM Attendance 

                                        WHERE student_id = %s AND course_id = %s

                                    """, (selected_student_id, st.session_state.selected_course_id))

                                attendance_records = cursor.fetchall()

                                if attendance_records:

                                    # Dropdown to select an attendance record to edit

                                    selected_attendance_id = st.selectbox(

                                        "Select an Attendance Record to Edit",

                                        options=[record[0] for record in attendance_records],

                                        format_func=lambda
                                            x: f"{next(record[1] for record in attendance_records if record[0] == x)} - {next(record[2] for record in attendance_records if record[0] == x)}"

                                    )

                                    # Input fields for updating attendance

                                    new_status = st.selectbox("New Status", ["Present", "Absent"])

                                    if st.button("Update Attendance"):
                                        update_attendance(selected_attendance_id, new_status)

                                else:

                                    st.warning("No attendance records found for this student.")

                            else:

                                # Input fields for adding new attendance

                                attendance_date = st.date_input("Attendance Date", min_value=start_date,
                                                                max_value=end_date)

                                attendance_status = st.selectbox("Attendance Status", ["Present", "Absent"])

                                if st.button("Mark Attendance"):

                                    # Check if all fields are filled

                                    if not attendance_date or not attendance_status:

                                        st.error("All fields are required. Please fill in all the details.")

                                    else:

                                        mark_attendance(selected_student_id, st.session_state.selected_course_id,
                                                        attendance_date, attendance_status)

                    else:

                        st.error("Invalid course selected. Please try again.")

                cursor.close()

                connection.close()

            # Logout button

            if st.button("Logout"):
                st.session_state.lecturer_logged_in = False

                st.session_state.lecturer_id = None

                st.session_state.lecturer_name = None

                st.session_state.selected_course_id = None

                st.success("Logged out successfully.")
    # Footer with copyright notice
    st.sidebar.markdown(
        """
        <div class="sidebar-footer">
            &copy; 2025 All rights reserved. This system was built by <a href="https://mail.google.com/mail/u/0/#inbox" target="_blank">Henry Allison</a>.
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()