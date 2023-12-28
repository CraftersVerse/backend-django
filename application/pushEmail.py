from dotenv import load_dotenv

load_dotenv()
from supabase_py import create_client
import os

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

from email.message import EmailMessage
import ssl

import smtplib
from email.mime.text import MIMEText


def push_email(subject_code, exam_venue):
    # Query absent students' data from the absent table in Supabase
    absentResponse = supabase.table("absent").select("*").execute()
    #print(f"Absent Response Data: {absentResponse}")


    # Query students' data from the student table in Supabase
    studentResponse = supabase.table("student").select("*").execute()
    #print(f"Student Response Data: {studentResponse}")


    # Query enrollment data from the enrollment table in Supabase
    enrollmentResponse = supabase.table("enrollment").select("*").execute()
    print(f"Enrollment Data: {enrollmentResponse}")


    # # Query exam venue data from the examVenue table in Supabase
    examVenueResponse = supabase.table("examVenue").select("*").execute()
    #print(f"Exam Venue Data: {examVenueResponse}")

    # Compare student IDs with absent student IDs and get the emails
    absent_students_data_by_email = {}

    for absent in absentResponse['data']:
        if (absent['subjectCode'] == subject_code and
                absent['examVenue'] == exam_venue):
            absent_student_id = absent['student']

            # Find the corresponding enrollment data for the absent student
            found_enrollments = [enrollment for enrollment in enrollmentResponse['data'] if enrollment['studentId'] == absent_student_id]
            if found_enrollments:
                for enrollment_data in found_enrollments:
                    enrollment_subject_code = enrollment_data['subjectCode']

                    # Find the corresponding exam venue data for the subject code
                    venue_data = next((venue for venue in examVenueResponse['data'] if venue['subjectCode'] == enrollment_subject_code), None)
                    if venue_data:
                        # Find the corresponding student data for the absent student
                        student_data = next((student for student in studentResponse['data'] if student['id'] == absent_student_id), None)
                        if student_data:
                            # Store absent students' data by email
                            email = student_data['email']
                            if email not in absent_students_data_by_email:
                                absent_students_data_by_email[email] = {
                                    'id': absent_student_id,
                                    'name': student_data['name'],
                                    'email': email,
                                    'subjects': []
                                }

                            # Append details of the absent subject and venue for the student
                            absent_students_data_by_email[email]['subjects'].append({
                                'subject_code': enrollment_subject_code,
                                'subject_name': venue_data['subjectName'],
                                'exam_venue': enrollment_data['examVenue'],
                                'exam_date': venue_data['date'],
                                'exam_time': venue_data['time'],
                            })
    
    matched_students_info = []
    email_sender = 'limml-wm20@student.tarc.edu.my'
    email_password = 'ntntygixzsujqxhp'
    #email_receiver = student_data['email']
    
    # Sending email to absent students
    for email, student_data in absent_students_data_by_email.items():
        filtered_subjects = [
            subject_details for subject_details in student_data['subjects']
            if subject_details['subject_code'] == subject_code and subject_details['exam_venue'] == exam_venue
                
        ]
        print("Subject Codes:")
        for subject_details in filtered_subjects:
            print(subject_details['subject_code'])
        print("Exam Venue:")
        for subject_details in filtered_subjects:
            print(subject_details['exam_venue'])
            
        
        if filtered_subjects:
            student_info = {
                'id': student_data['id'],
                'name': student_data['name'],
                'email': student_data['email'],
            }
            matched_students_info.append(student_info)

        # Construct the email content with the collected details for each student
        subject = f'Important Exam Details for {len(filtered_subjects)} Subjects'
        body = f"Dear {student_data['name']},\n\n"

        # Loop through each absent subject and append details to the email body
        for subject_details in filtered_subjects:
            body += f"You are absent for the upcoming exam for Subject {subject_details['subject_code']}.\n"
            body += f"Exam Details:\n"
            body += f"Subject Code: {subject_details['subject_code']}\n"
            body += f"Subject Name: {subject_details['subject_name']}\n"
            body += f"Exam Venue: {subject_details['exam_venue']}\n"
            body += f"Exam Date: {subject_details['exam_date']}\n"
            body += f"Exam Time: {subject_details['exam_time']}\n\n"

        body += "Please make sure to attend the exam on time. If you have any concerns, please contact your instructor.\n\n"
        body += "Best regards,\nTunku Abdul Rahman University of Management and Technology (TAR UMT)"
        
        
        em = EmailMessage()
        em['From'] = email_sender
        em['To']    =  student_data['email']
        em['Subject'] = subject
        em.set_content(body)

        context = ssl.create_default_context()

        try:
            with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, student_data['email'], em.as_string())
                print(f"Email sent successfully to {student_data['email']}")
        except Exception as e:
            print(f"An error occurred: {e}")

        # print(f"Data:", {absent_students_data_by_email.values})
        print(f"match:{matched_students_info}")
    return matched_students_info

# Call the function to send emails to absent students
#matched_students = push_email("BAIT2203", "R1")
#print(f"MMMMMM: {matched_students}")

