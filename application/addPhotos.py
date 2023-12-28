import os
import cv2

def capture_photo():
    # Capture photo from webcam
    webcam = cv2.VideoCapture(0)
    _, photo = webcam.read()
    webcam.release()
    return photo


def save_photo(photo, folder_path, username=None):
    # Generate a unique file name for the photo
    file_name = f"{username}.jpg"  # Use the entered username as the file name

    # Construct the full file path
    file_path = os.path.join(folder_path, file_name)

    # Save the photo to the folder
    cv2.imwrite(file_path, photo)
    print("Photo saved successfully.")


# Specify the folder path where you want to store the photos
folder_path = "C:/Users/Acer/Desktop/temporary/FYP_EMS/backend-django/application/ImagesAttendance"

# Capture and save a photo
#photo = capture_photo()
#save_photo(photo, folder_path)