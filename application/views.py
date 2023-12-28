from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .serializers import ExamVenueSerializer, SubjectSerializer, ExamArrangementSerializer
from supabase_py import create_client, Client
from datetime import timedelta, datetime
from .models import *
from dotenv import load_dotenv
from PIL import Image
from torchvision import transforms,torch
from ultralytics import YOLO
import pickle
import base64
import io


#-------------import the py ----------------------
from .addPhotos import capture_photo, save_photo
from .attendanceTaking import take_attendance
from .lecturerAttendance import lecturer_attendance
from .displayAttendance import display_attendance
from .pushEmail import push_email
from django.views.decorators.csrf import csrf_exempt
import json


#--------------
load_dotenv()
import os

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

# model = YOLO("C:/Users/Acer/Desktop/Book_Custom_Dataset/runs/detect/train2/weights/best.pt")

@api_view(['POST'])
def create_exam_venue(request):
    if request.method == 'POST':
        serializer = ExamVenueSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Save to Supabase
            supabase.table('application_examvenue').insert(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # Return a 405 Method Not Allowed for other methods
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(['POST'])
def create_exam_subject(request):
    if request.method == 'POST':
        serializer = SubjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Save to Supabase
            supabase.table('application_subject').insert(serializer.data)
            print(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    # Return a 405 Method Not Allowed for other methods
    return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

# @api_view(['POST'])
# def predict_objects(request):
#     if request.method == 'POST' and 'images' in request.FILES:
#         # print(request.FILES)
#         predicted_images_base64_data_url = []

#         # Retrieve the uploaded image from Vue
#         uploaded_images = request.FILES.getlist('images')
#         print(uploaded_images)

#         # Perform object detection for each image
#         for uploaded_image in uploaded_images:
#             image = Image.open(uploaded_image)

#             transform = transforms.Compose([
#                 transforms.Resize((416, 416)),
#                 transforms.ToTensor(),
#             ])
#             input_tensor = transform(image)
#             input_tensor = input_tensor.unsqueeze(0)

#             with torch.no_grad():
#                 predictions = model(input_tensor)

#             data_uri = image_to_base64(predictions[0].path)
#             predicted_images_base64_data_url.append(data_uri)

#         return JsonResponse({'predicted_images_base64_data_url': predicted_images_base64_data_url}, status=200)
#     else:
#         return JsonResponse({'error': 'Invalid request'}, status=400)
    
# def image_to_base64(image_path):
#     # Read the image from the path
#     img = Image.open(image_path)

#     # Convert the image to JPEG format
#     buffered = io.BytesIO()
#     img.save(buffered, format="JPEG")

#     # Encode the image in Base64
#     base64_encoded = base64.b64encode(buffered.getvalue()).decode('utf-8')

#     # Build the data URI string
#     data_uri = f'data:image/jpeg;base64,{base64_encoded}'

#     return data_uri

# ------------------code for hall arrangement---------------------------------------------------
@api_view(['POST'])
def generate_exam_arrangement(request):

    # Step 1: Retrieve data from the database (Supabase)
    venues_response = supabase.from_('application_examvenue').select('*').execute()
    subjects_response = supabase.from_('application_subject').select('*').execute()

    venues = venues_response['data']
    subjects = subjects_response['data']

    # Step 2: User input for exam date range
    start_date = datetime.strptime(request.data.get('start_date'), "%Y-%m-%d")
    end_date = datetime.strptime(request.data.get('end_date'), "%Y-%m-%d")

    # Step 3: Check for weekends
    valid_dates = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1) if (start_date + timedelta(days=x)).weekday() < 5]

    # Step 4-6: Allocation algorithm
    arrangements = []

    for date in valid_dates:
        # Sort subjects by the number of students in descending order
        subjects.sort(key=lambda x: x['numOfStudents'], reverse=True)

        for subject in subjects:
            remaining_students = subject['numOfStudents']  # Initialize remaining students for the subject

            # Sort venues with the same venueID by total capacity in descending order
            unique_venue_ids = set(venue['venueID'] for venue in venues)
            for venue_id in unique_venue_ids:
                venues_with_same_id = [venue for venue in venues if venue['venueID'] == venue_id]
                venues_with_same_id.sort(key=lambda x: x['capacity'], reverse=True)

                # Attempt to allocate the subject to the venues with the same venueID
                for venue in venues_with_same_id:
                    if remaining_students > 0 and remaining_students <= venue['capacity']:
                        # Allocate all remaining students to the current venue
                        arrangements.append({
                            'Date': date.strftime("%Y-%m-%d"),
                            'Subject Name': f"{subject['subjectID']}{subject['subjectName']}",
                            'Venue': f"{venue['venueID']}{venue['venueNum']}",
                            'Number of Students': remaining_students
                        })
                        remaining_students = 0  # All students are allocated

                        # Remove the allocated venue and subject
                        venues.remove(venue)
                        subjects.remove(subject)
                    elif remaining_students > 0:
                        # Allocate the venue's capacity and update the remaining students
                        arrangements.append({
                            'Date': date.strftime("%Y-%m-%d"),
                            'Subject Name': f"{subject['subjectID']}{subject['subjectName']}",
                            'Venue': f"{venue['venueID']}{venue['venueNum']}",
                            'Number of Students': venue['capacity']
                        })
                        remaining_students -= venue['capacity']

                        # Remove the allocated venue
                        venues.remove(venue)

    # Save the arrangements to Supabase
    for arrangement in arrangements:
        try:
            arrangement_instance = ExamArrangement(
                date=arrangement['Date'],
                subject_name=arrangement['Subject Name'],
                venue=arrangement['Venue'],
                num_of_students=arrangement['Number of Students']
            )

            # Save the instance to the database
            arrangement_instance.save()
            supabase.table('application_examarrangement').insert(arrangement_instance)
            # print(arrangement)
        except Exception as e:
            print(f"Error inserting data into Supabase: {e}")
    
    if len(subjects) > 0:
        print(len(subjects))
        print(subjects)
        unallocated_subject_names = [f"{subject['subjectID']} {subject['subjectName']}" for subject in subjects]
        message = f"Below subjects could not be allocated: {', '.join(unallocated_subject_names)}"
        return JsonResponse({'arrangements': arrangements, 'message': message})
    else:
        return JsonResponse({'arrangements': arrangements})



#--------------------------------------------------AddPhoto------------------------------------------
@api_view(['POST'])
def add_photos(request):
    if request.method == 'POST':
        student_id = request.data.get('studentId')  # Access the studentId directly from request data
        print(student_id)
        
        if student_id:
            # Capture photo from webcam
            photo = capture_photo()

            # Specify the folder path where you want to store the photos
            folder_path = "C:/Users/Acer/Desktop/temporary/FYP_EMS/backend-django/application/ImagesAttendance"

            # Save the photo with the entered username as the file name
            save_photo(photo, folder_path, student_id)

            return JsonResponse({'message': 'Photo saved successfully.'}, status=201)
        
    return JsonResponse({'error': 'Invalid data or studentId missing.'}, status=400)

#----------------------------------------------------------------------------------------------------

#----------------------------------------------Take Attendnace---------------------------------------
@csrf_exempt
def take_attendance_views(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            exam_venue = data.get('examVenue')
            subject_code = data.get('subjectCode')
            
        
            if exam_venue and subject_code:
                print(f"Received exam venue: {exam_venue}, subject code: {subject_code}")

                response = supabase.table('enrollment').select("*").execute()
                print(response)  # Check the structure of the response

                if isinstance(response.get('data'), list):
                    found = False

                    for exam in response['data']:
                        venues = exam.get('examVenue')
                        codes = exam.get('subjectCode')

                        if venues is not None and codes is not None:
                            if exam_venue in venues and subject_code in codes:
                                print(f"Received exam venue: {venues}, subject code: {codes}")
                                found = True
                                # Perform attendance processing
                                take_attendance(exam_venue, subject_code)


                                #return JsonResponse({'data': attendance_data})
                                return JsonResponse({'success': f'Attendance for {exam_venue} recorded successfully at {subject_code}.'}, status=200)
                                #return render(request, 'components/displayAttendance.vue', {'data': attendance_data})

                    if not found:
                        return JsonResponse({'error': 'No matching exam venue and subject code found.'}, status=404)
                else:
                    return JsonResponse({'error': 'Invalid response format from Supabase.'}, status=500)

        except json.JSONDecodeError as e:
            return JsonResponse({'error': f'Error decoding JSON: {str(e)}'}, status=400)

        return JsonResponse({'error': 'This endpoint only accepts POST requests.'}, status=405)

@csrf_exempt
def take_lecturer_attendance_views(request):
    if request.method == 'POST':
        lecturer_attendance()
        # print("Webcam started successfully")
        return JsonResponse({'success': 'Webcam started successfully.'}, status=200)

    return JsonResponse({'error': 'This endpoint only accepts POST requests.'}, status=405)


#-----------------------------------------------------------------------------------------------------
#-----------------------------------------------ChecK Matched-----------------------------------------

def check_matching_entry(subject_code, exam_venue, enrollment_data):
    # Normalize inputs
    subject_code = subject_code.strip().upper()  # Assuming standardization to uppercase
    exam_venue = exam_venue.strip().upper()  # Assuming standardization to uppercase
    
    for enrollment in enrollment_data:
        # Normalize data from enrollment_data for comparison
        enrollment_subject = enrollment.get('subjectCode', '').strip().upper()
        enrollment_exam_venue = enrollment.get('examVenue', '').strip().upper()

        # Debugging output to check values being compared
        print(f"Comparing: {subject_code} with {enrollment_subject}, {exam_venue} with {enrollment_exam_venue}")
        
        if enrollment_subject == subject_code and enrollment_exam_venue == exam_venue:
            return True
    
    return False


#-----------------------------------------------------------------------------------------------------

#-----------------------------------------------Display Attendance------------------------------------
from django.views.decorators.http import require_http_methods
@require_http_methods(["GET", "POST"])
@csrf_exempt
def display_attendance_views(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            exam_venue = data.get('examVenue')
            subject_code = data.get('subjectCode')
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON data provided'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        attendanceResponse = supabase.table('attendance').select("*").eq('subjectCode', subject_code.strip()).eq('examVenue', exam_venue.strip()).execute()
        print(f"Attendance Data: {attendanceResponse}")

        enrollmentResponse = supabase.table("enrollment").select("*").execute()
        print(f"Enrollment Data: {enrollmentResponse}")

        examVenueResponse = supabase.table("examVenue").select("*").execute()
        print(f"Exam Venue Data: {examVenueResponse}")

        studentResponse = supabase.table("student").select("*").execute()
        print(f"Student Data: {studentResponse}")

        matching_entry = check_matching_entry(subject_code, exam_venue, enrollmentResponse.get('data', []))

        if not matching_entry:
            return JsonResponse({'error': 'No matching exam venue and subject code found in enrollment data.'}, status=404)
        
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
                    print(f"ExamVenue!!!!!!!: {student_info}")    
                        
                    venues_for_subject = [venue for venue in enrollmentResponse.get('data', []) if venue.get('subjectCode') == found_student.get('subjectCode') and venue.get('examVenue') == exam_venue]
                    for venue in venues_for_subject:
                        # if venue.get('subjectCode') == found_student.get('subjectCode'):
                            student_info['subjectName'] = venue.get('subjectName')
                            student_info['examVenue'] = venue.get('examVenue')

                            if exam_venue == student_info['examVenue'].strip():
                                student_info['venue'] = 'Correct'
                            else:
                                student_info['venue'] = 'Wrong'

                            attendance_students.append(student_info)
                            break

                        # Check if a venue match was found for the student, if not, mark it as 'Wrong'
                    if 'venue' not in student_info:
                        student_info['venue'] = 'Wrong'
                        attendance_students.append(student_info)

                    print(f"Student info: {student_info}")

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

                            # if existing_records.get('data'):
                            #     # Delete existing records
                            #     supabase.table('wrongVenue').delete().eq('id', student_info['id']).execute()

                            # # Insert new record
                            # supabase.table('wrongVenue').insert([{
                            #     'id': student_info['id'],
                            #     'name': student_info['name']
                            # }]).execute()
            return JsonResponse({'Attendance Student': attendance_students})

    elif request.method == 'GET':
        return JsonResponse({'message': 'This endpoint only accepts POST requests for data processing.'})

    return JsonResponse({'error': 'Invalid request method.'})

#-----------------------------------------------------------------------------------------------------

#-----------------------------------------------Check+Display Absent----------------------------------------
@require_http_methods(["GET", "POST"])
@csrf_exempt
def display_absent_views(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            exam_venue = data.get('examVenue')
            subject_code = data.get('subjectCode')
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON data provided'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

        enrollmentResponse1 = supabase.table('enrollment').select("*").execute()
        # print(f"Enrollment Data: {enrollmentResponse}")

        # enrolled_students = [enrollment['studentId'] for enrollment in enrollmentResponse['data']]
        # print(f"Enrolled Students: {enrolled_students}")


        enrollmentResponse = supabase.table('enrollment').select("studentId").eq('subjectCode', subject_code.strip()).eq(
        'examVenue', exam_venue.strip()).execute()
        print(f"Enrollment Data: {enrollmentResponse}")

        #enrolled_students = [enrollment['studentId'] for enrollment in enrollmentResponse['data'] if enrollment.get('subjectCode') == subject_code.strip()]
        enrolled_students = [enrollment['studentId'] for enrollment in enrollmentResponse['data']]
        print(f"Matched Students: {enrolled_students}")


        #---------------------------------------------------------
        # Query attendance data from Supabase for the specific examVenue and subjectCode
        attendanceResponse = supabase.table('attendance').select("id").eq('subjectCode', subject_code.strip()).eq('examVenue', exam_venue.strip()).execute()
        attended_students = [attendance['id'] for attendance in attendanceResponse['data']]
        print(f"Attended Students: {attended_students}")

        #------------------------Remove the student from absent when detect he is in the attendance table-------
        # Query and store existing absent students
        existing_absent_students = supabase.table('absent').select('*').eq('subjectCode', subject_code.strip()).eq('examVenue', exam_venue.strip()).execute()
        print(f"Existing Data: {existing_absent_students}")

        matching_entry = check_matching_entry(subject_code, exam_venue, enrollmentResponse1.get('data', []))

        if not matching_entry:
            return JsonResponse({'error': 'No matching exam venue and subject code found in enrollment data.'}, status=404)
            #print(f" No matching exam venue and subject code found in enrollment data")

        if existing_absent_students['data']:
            existing_ids = [student.get('student') for student in existing_absent_students['data']]
            print(f"Existing ID Data: {existing_ids}")
        else:
            existing_ids = []

        # Identify students who are attendance but marked as absent and remove them from absent table
        absent_students_to_remove = [student for student in existing_absent_students['data'] if student['student'] in attended_students]
        print(f"Remove record: {absent_students_to_remove}")

        if absent_students_to_remove:
            for student_to_remove in absent_students_to_remove:
                student_id_to_remove = student_to_remove['student']
                try:
                    remove_response, remove_error = supabase.table('absent').delete().eq('student', student_id_to_remove).execute()
                    if remove_error:
                        print(f"Error removing absent student {student_id_to_remove}: {remove_error}")
                    else:
                        print(f"Removed absent student {student_id_to_remove} successfully.")
                except Exception as e:
                    print(f"An error occurred: {e}")
        else:
            if existing_absent_students['data']:
                print("All absent students attended. No removal needed.")
            else:
                print("No absent students found.")
                # return JsonResponse({'message': 'No absent students found.'}, status=200)
        #----------------------------------------------------------------------------------

        absent_students = [{'studentId': student_id, 'subjectCode': subject_code, 'examVenue': exam_venue}
                            for student_id in enrolled_students if student_id not in attended_students]
        print(f"Absent Students: {absent_students}")

        # Insert absent students into the absent table if they don't exist already
        existing_absent_students = supabase.table('absent').select('*').eq('subjectCode', subject_code.strip()).eq('examVenue', exam_venue.strip()).execute()
        print(f"Existing Data: {existing_absent_students}")

        if existing_absent_students['data']:
            existing_ids = [student.get('student') for student in existing_absent_students['data']]
            print(f"Existing ID Data: {existing_ids}")
        else:
            existing_ids = []

        new_absent_students = [student for student in absent_students if student['studentId'] not in existing_ids]
        print(f"New Student: {new_absent_students}")

        mapped_new_absent_students = [
            {
                'student': student['studentId'],  # Map 'studentId' to 'student'
                'subjectCode': student['subjectCode'],
                'examVenue': student['examVenue']
            }
            for student in new_absent_students
        ]

        print(f"MAPPED: {mapped_new_absent_students}")

        if mapped_new_absent_students:
            response, insert_success = supabase.table("absent").insert(mapped_new_absent_students).execute()
            if insert_success:
                print(f"Success inserting absent students: {insert_success}")
            else:
                print(f"Absent students inserted failed.")
        else:
            print("No new absent students to insert.")

        #-------------------------------Display absent students based on the inputted subjectCode and examVenue-------
        response = supabase.table('absent').select("*").eq('subjectCode', subject_code.strip()).eq('examVenue', exam_venue.strip()).execute()
        print(f"response: {response}")
        absent_students = []

        if response.get('data'):
        
            studentResponse = supabase.table("student").select("*").execute()
            print(f"studentResponse: {studentResponse}")
            students_dict = {student['id']: student for student in studentResponse['data']}
            print(f"studentDDDDD: {students_dict}")

            for absent in response['data']:
                student_id = absent.get('student')
                print(f"Checking for studentId: {student_id}")
                if student_id in students_dict:
                    found_student = students_dict[student_id]
                    student_info = {
                        'id': student_id,
                        'name': found_student.get('name'),
                        'email': found_student.get('email'),
                        'gender': found_student.get('gender'),
                        'phoneNum': found_student.get('phoneNum')
                    }
                    absent_students.append(student_info)
                    print(f"Absent students: {absent_students}")

    if absent_students:
        return JsonResponse({'Absent Student': absent_students})

    elif request.method == 'GET':
        return JsonResponse({'message': 'This endpoint only accepts POST requests for data processing.'})

    return JsonResponse({'error': 'Invalid request method.'})

#-----------------------------------------------------------------------------------------------------

#-------------------------------------------------Push Email------------------------------------------
@require_http_methods(["GET", "POST"])
@csrf_exempt
def push_email_views(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            exam_venue = data.get('examVenue')
            subject_code = data.get('subjectCode')
        except json.JSONDecodeError as e:
            return JsonResponse({'error': 'Invalid JSON data provided'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
        
        enrollmentResponse = supabase.table("enrollment").select("*").execute()
        print(f"Enrollment Data: {enrollmentResponse}")
        
        matching_entry = check_matching_entry(subject_code, exam_venue, enrollmentResponse.get('data', []))

        if not matching_entry:
            return JsonResponse({'error': 'No matching exam venue and subject code found in enrollment data.'}, status=404)
        
        email_data = push_email(subject_code,exam_venue)

    return JsonResponse({'Email Data': email_data})


#-----------------------------------------------------------------------------------------------------

#-------------------------------------------------Display Student(Enrollment)------------------------------------------
@require_http_methods(["POST", "GET"])
def display_student_views(request):
    enrollment_response = supabase.table('enrollment').select("*").execute()
    student_response = supabase.table('student').select("*").execute()
    exam_venue_response = supabase.table("examVenue").select("*").execute()

    enroll_students = []
    unique_records = set()

    for enroll in enrollment_response['data']:
        student_id = enroll.get('studentId')
        subject_code = enroll.get('subjectCode')
        record = (student_id, subject_code)

        # Check for duplicates using a combination of student ID and subject code
        if record in unique_records:
            continue

        found_student = next((student for student in student_response['data'] if student_id == student.get('id')), None)

        if found_student:
            exam_venue_details = next((venue for venue in exam_venue_response['data'] if subject_code == venue.get('subjectCode')), None)
            
            if exam_venue_details:
                date = exam_venue_details.get('date')
                time = exam_venue_details.get('time')

                student_info = {
                    'id': student_id,
                    'name': found_student.get('name'),
                    'subjectCode': subject_code,
                    'subjectName': exam_venue_details.get('subjectName'),
                    'examVenue': enroll.get('examVenue'),  
                    'date': date,
                    'time': time,
                }
                enroll_students.append(student_info)
                unique_records.add(record)

    return JsonResponse({'Enroll Data': enroll_students})


#-----------------------------------------------------------------------------------------------------
