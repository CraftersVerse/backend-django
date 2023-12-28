import cv2
import numpy as np
import face_recognition
import os
import time
from datetime import datetime
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

def lecturer_attendance():
    path = os.path.join(os.path.dirname(__file__), 'Lecturer')
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

    def markAttendance(id):
        now = datetime.now()
        dtString = now.strftime('%H:%M:%S')
        try:
            response = supabase.table('lecturer_attendance').select("*").eq('id', id.strip()).execute()
            if response.get('error'):
                print(f"Supabase error: {response['error']}")
                

            data = supabase.table('lecturer_attendance').insert([
                {'id': id, 'time': dtString}
            ]).execute()
            print(f'Attendance for {id} recorded successfully at {dtString}.')
            print(f'Data returned from Supabase insert: {data}')

            return True

        except Exception as e:
            print(f'Error connecting to Supabase or processing data: {e}')
            return False
        
    #########

    encodeListKnown = findEncodings(images)
    # print(len(encodeListKnown))
    print('Encoding Complete')
    cap = cv2.VideoCapture(0)

    should_continue = True
    attendance_marked = False

    # while not attendance_marked:
    while not attendance_marked:
        success, img = cap.read()
        # To stop the loop
        if not success:
            break

        imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

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
                # if markAttendance(name):
                #     should_continue = not markAttendance(name)
                if not attendance_marked:
                    attendance_marked = markAttendance(name)
                # condition = markAttendance(name)
                time.sleep(10)
                # if condition:
                #     break
                # time.sleep(10)
            # break

        
        cv2.imshow('Webcam', img)
        key = cv2.waitKey(1)

        # Check if 'q' is pressed or window is closed
        if key == ord('q') or cv2.getWindowProperty('Webcam', cv2.WND_PROP_VISIBLE) == -1:
            cv2.destroyAllWindows()
            break
    cv2.destroyAllWindows()
    cap.release()