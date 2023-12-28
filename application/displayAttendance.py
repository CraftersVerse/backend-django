import json

#-----------------------------------#
from django.shortcuts import render
# Supabase Set Up
# pip install python-dotenv
# pip install supabase
from dotenv import load_dotenv

load_dotenv()
import os

url = "SUPABASE_URL"
key = "SUPABASE_KEY"
from supabase_py import create_client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

#---------------------------------------------#

def display_attendance(exam_venue, subject_code):
    attendanceResponse = supabase.table('attendance').select("*").eq('subjectCode', subject_code.strip()).eq('examVenue', exam_venue.strip()).execute()
    print(f"Attendance Data: {attendanceResponse}")

    enrollmentResponse = supabase.table("enrollment").select("*").execute()
    print(f"Enrollment Data: {enrollmentResponse}")

    examVenueResponse = supabase.table("examVenue").select("*").execute()
    print(f"Exam Venue Data: {examVenueResponse}")

    studentResponse = supabase.table("student").select("*").execute()
    print(f"Student Data: {studentResponse}")

    processed_student_ids = set()
    attendance_students = []

    if 'data' in attendanceResponse:
        for attendance in attendanceResponse['data']:
            student_id = attendance.get('id')
            print(f"Student ID: {student_id}")

            if student_id in processed_student_ids:
                continue

            found_students = [student for student in enrollmentResponse.get('data', []) if student.get('studentId') == student_id and student.get('subjectCode').strip() == subject_code]

            student_name = next((name.get('name') for name in studentResponse.get('data', []) if name.get('id') == student_id), None)

            print(f"Processing student: {student_id}, Name: {student_name}, Found Students: {found_students}")

            if found_students:
                for found_student in found_students:
                    student_info = {
                        'id': student_id,
                        'name': student_name,
                        'examVenue': found_student.get('examVenue'),
                        'subjectCode': found_student.get('subjectCode'),
                    }

                    for venue in examVenueResponse.get('data', []):
                        if venue.get('subjectCode') == found_student.get('subjectCode'):
                            student_info['subjectName'] = venue.get('subjectName')
                            student_info['examVenue'] = venue.get('examVenue')
                            attendance_students.append(student_info)
                            break

                print(f"Student info after exam venue lookup: {student_info}")

                if exam_venue == student_info['examVenue'].strip():
                    student_info['venue'] = 'Correct'
                else:
                    student_info['venue'] = 'Wrong'

            else:
                student_info = {
                    'id': student_id,
                    'name': student_name,
                    'examVenue': 'No Venue',
                    'subjectCode': 'No Subject Code',
                    'subjectName': 'No Subject Name',
                    'venue': 'Wrong'
                }

                attendance_students.append(student_info)

            print(f"Final student info: {student_info}")

            processed_student_ids.add(student_id)

            if attendance_students:
                print(f"Attendance students: {attendance_students}")

                for student_info in attendance_students:
                    if student_info['venue'] == 'Wrong':
                        existing_record = supabase.table('wrongVenue').select('*').eq('id', student_info['id']).execute()

                        # if existing_record.get('data'):
                        #     supabase.table('wrongVenue').delete().eq('id', student_info['id']).execute()

                        # supabase.table('wrongVenue').insert([{
                        #     'id': student_info['id'],
                        #     'name': student_info['name']
                        # }]).execute()

    return attendance_students


