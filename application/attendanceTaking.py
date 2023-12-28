import cv2
import numpy as np
import face_recognition
import os
from datetime import datetime, date
from django.shortcuts import render
# Supabase Set Up
# pip install python-dotenv
# pip install supabase
from dotenv import load_dotenv
from ultralytics import YOLO

load_dotenv()
import os
import math

url = "SUPABASE_URL"
key = "SUPABASE_KEY"
from supabase_py import create_client

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)
path = os.path.abspath("FYP_EMS/backend-django/best.pt")

#--------------------------------------------
def attire_detection(img):
    model=YOLO("C:/Users/Acer/Desktop/backend-django/best.pt")
    classNames = ["appropriate", "not_appropriate"]

    results=model.predict(img,stream=True)
    for r in results:
        boxes=r.boxes
        for box in boxes:
            x1,y1,x2,y2=box.xyxy[0]
            x1,y1,x2,y2=int(x1), int(y1), int(x2), int(y2)
            print(x1,y1,x2,y2)

            cv2.rectangle(img, (x1,y1), (x2,y2), (255,0,255),3)
            conf=math.ceil((box.conf[0]*100))/100
            cls=int(box.cls[0])
            class_name=classNames[cls]
            label=f'{class_name}{conf}'
            t_size = cv2.getTextSize(label, 0, fontScale=1, thickness=2)[0]
            print(t_size)
            c2 = x1 + t_size[0], y1 - t_size[1] - 3

            cv2.rectangle(img, (x1,y1), c2, [255,0,255], -1, cv2.LINE_AA)  # filled
            cv2.putText(img, label, (x1,y1-2),0, 1,[255,255,255], thickness=1,lineType=cv2.LINE_AA)
    return img

def take_attendance(exam_venue, subject_code):
    path = os.path.join(os.path.dirname(__file__), 'ImagesAttendance')
    images = []
    classNames = []
    myList = os.listdir(path)
    # print(myList)
    for cls in myList:
        curImg = cv2.imread(f'{path}/{cls}')
        images.append(curImg)
        classNames.append(os.path.splitext(cls)[0])
    print(classNames)

    def findEncodings(images):
        encodeList = []
        for i, img in enumerate(images):
            try:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                encode = face_recognition.face_encodings(img)[0]
                encodeList.append(encode)
            except IndexError:
                print(f"Failed to encode image {i + 1}")
        return encodeList
    
    # Supabase Code Write #

    def markAttendance(id, exam_venue, subject_code):
        now = datetime.now()
        dtString = now.strftime('%H:%M:%S')
        try:
            response = supabase.table('attendance').select("*").eq('id', id.strip()).eq('subjectCode', subject_code.strip()).eq('examVenue', exam_venue.strip()).execute()
            if response.get('error'):
                print(f"Supabase error: {response['error']}")
                

            existing_records = response.get('data', [])
            print(f'Existing Records: {existing_records}')

            record_found = any(record['id'] == id and record['subjectCode'] == subject_code and record['examVenue'] == exam_venue for record in existing_records)
            if record_found:
                print(f'Attendance for {id} in subject {subject_code} at {exam_venue} already recorded.')
                
            else:
                data = supabase.table('attendance').insert([
                    {'id': id, 'time': dtString, 'subjectCode': subject_code, 'examVenue': exam_venue}
                ]).execute()
                print(f'Attendance for {id} recorded successfully at {dtString}.')
                print(f'Data returned from Supabase insert: {data}')

        except Exception as e:
            print(f'Error connecting to Supabase or processing data: {e}')
        
    #########

    encodeListKnown = findEncodings(images)
    # print(len(encodeListKnown))
    print('Encoding Complete')
    cap = cv2.VideoCapture(0)
    window_name = 'Webcam'

    # Set an initial window size
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, 800, 600)

    # try:
    while True:
        success, img = cap.read()
        # To stop the loop
        if not success:
            break

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

        #attire detection
        imgS_with_detection = attire_detection(img)

        facesCurFrame = face_recognition.face_locations(imgS)
        encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

        for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            # print(faceDis)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = classNames[matchIndex]
                # print(name)
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.rectangle(img, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                markAttendance(name, exam_venue, subject_code)

        img_combined = cv2.addWeighted(cv2.resize(imgS_with_detection, (img.shape[1], img.shape[0])), 0.5,
                                       cv2.resize(img, (img.shape[1], img.shape[0])), 0.5, 0)
        cv2.imshow('Webcam', img_combined)
        key = cv2.waitKey(1)

        # Check if 'q' is pressed or window is closed
        if key == ord('q') or cv2.getWindowProperty('Webcam', cv2.WND_PROP_VISIBLE) == -1:
            cv2.destroyAllWindows()
            break
    cap.release()

    # except KeyboardInterrupt:
    # pass



# Rest of your code remains unchanged
def is_correct_exam_date(exam_date, exam_time):
    # Assuming exam_date is a string in the format 'YYYY-MM-DD' and exam_time is in the format 'HH:MM:SS'
    exam_datetime_str = f"{exam_date} {exam_time}"
    exam_datetime = datetime.strptime(exam_datetime_str, '%Y-%m-%d %H:%M:%S')

    # Compare exam date and time with the current date and time or any specific condition
    current_datetime = datetime.now()

    # Adjust the condition as needed
    return exam_datetime > current_datetime

# def enter_exam_venue(request):
#     if request.method == 'POST':
#         form = ExamVenueForm(request.POST)
#         if form.is_valid():
#             exam_venue = form.cleaned_data['exam_venue']
#             subject_code = form.cleaned_data['subject_code']
#
#     else:
#         form = ExamVenueForm()
#     return render(request, 'users/hallInfo.html', {'form': form})









