from rest_framework import serializers
from .models import ExamVenue, Subject, ExamArrangement

class ExamVenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExamVenue
        # fields = (
        #     "venueID",
        #     "venueNum",
        #     "capacity"
        # )
        fields = '__all__'

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = (
            "subjectID",
            "subjectName",
            "numOfStudents"
        )

class ExamArrangementSerializer(serializers.ModelSerializer):
    class Meta:
        model: ExamArrangement
        fields = '__all__'  