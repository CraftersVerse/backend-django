from django.db import models

# Create your models here.
class ExamVenue(models.Model):
    venueID = models.CharField(max_length=20)
    venueNum = models.IntegerField()
    capacity = models.IntegerField()

    #arrange by venueID in the backend
    class Meta:
        ordering = ('venueID',)

    def __str__(self):
        return f"{self.venueID}"
    
class Subject(models.Model):
    subjectID = models.CharField(max_length=255)
    subjectName = models.CharField(max_length=255)
    numOfStudents = models.IntegerField()
    
    #arrange by venueID in the backend
    class Meta:
        ordering = ('subjectID',)

    def __str__(self):
        return f"{self.subjectID} {self.subjectName}"

class ExamArrangement(models.Model):
    date = models.DateField()
    subject_name = models.CharField(max_length=255)
    venue = models.CharField(max_length=255)
    num_of_students = models.IntegerField()

    class Meta:
        ordering = ('date',)

    def __str__(self):
        return f"{self.date} - {self.subject_name} - {self.venue}"


class PredictedImage(models.Model):
    image_data = models.BinaryField()

    def __str__(self):
        return f"Predicted Image {self.id}"