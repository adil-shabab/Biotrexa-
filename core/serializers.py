
from rest_framework import serializers
from .models import *

class AvailableTimeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailableTime
        fields = '__all__'

class MonthlyTimingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MonthlyTiming
        fields = '__all__'


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        fields = ['id', 'name', 'fee', 'slug']


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'message', 'created_at', 'read_status', 'redirection_url']


class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = ['user', 'role', 'created_at']

    user = serializers.CharField(source='user.username')  # To include the username in the response