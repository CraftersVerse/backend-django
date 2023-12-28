from django.urls import path
from .views import *


urlpatterns = [
    path('application/exam-venues/', create_exam_venue, name='create_exam_venue'),
    path('application/exam-subject/', create_exam_subject, name='create_exam_subject'),
    path('application/exam-arrange/', generate_exam_arrangement, name='generate_exam_arrangement'),
    # Add other URLs as needed
    path('application/add-photos/', add_photos, name='add_photos'),
    path('application/take-attendance/', take_attendance_views, name='take_attendance'),
    path('application/take-lecturer-attendance/', take_lecturer_attendance_views, name='take_lecturer_attendance'),
    path('application/display-attendance/', display_attendance_views, name='display_attendance'),
    path('application/display-absent/', display_absent_views, name='display_absent'),
    path('application/push-email/', push_email_views, name='push_email'),
    path('application/display-student/', display_student_views, name='display_student'),
    # path('application/predict_objects/', predict_objects, name='predict_image'),
    
]
