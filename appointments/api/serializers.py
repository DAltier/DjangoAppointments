from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Provider, Patient, Topic, Appointment
from django.utils import timezone


class UserSerializer(serializers.ModelSerializer):
	class Meta:
		model = User
		fields = ['id', 'username', 'first_name', 'last_name', 'email']


class ProviderSerializer(serializers.ModelSerializer):
	user = UserSerializer(read_only=True)
	
	class Meta:
		model = Provider
		fields = ['id', 'user']
		

class PatientSerializer(serializers.ModelSerializer):
	user = UserSerializer(read_only=True)
	
	class Meta:
		model = Patient
		fields = ['id', 'user']


class TopicSerializer(serializers.ModelSerializer):
	class Meta:
		model = Topic
		fields = ['id', 'name', 'duration']


class AppointmentSerializer(serializers.ModelSerializer):
	end_time = serializers.SerializerMethodField()
	
	class Meta:
		model = Appointment
		fields = ['id', 'provider', 'patient', 'topics', 'provider_notes', 'status', 'start_time', 'end_time', 'created_at', 'updated_at']
		read_only_fields = ['created_at', 'updated_at']
		
	def get_end_time(self, obj):
		return obj.end_time
	
	def validate_start_time(self, value):
		if value <= timezone.now():
			raise serializers.ValidationError("Appointment start time must be in the future")
		return value


class PatientAppointmentSerializer(AppointmentSerializer):
	provider = ProviderSerializer(read_only=True)
	topics = TopicSerializer(many=True, read_only=True)
	cancel_url = serializers.SerializerMethodField()
	
	class Meta(AppointmentSerializer.Meta):
		fields = AppointmentSerializer.Meta.fields + ['cancel_url']
		read_only_fields = ['provider', 'provider_notes', 'created_at', 'updated_at']
		
	def get_cancel_url(self, obj):
		if obj.status in ['Scheduled', 'In Progress']:
			request = self.context.get('request')
			if request:
				return request.build_absolute_uri(f'/api/patient/appointments/{obj.id}/cancel')
			

class ProviderAppointmentSerializer(AppointmentSerializer):
	patient = PatientSerializer(read_only=True)
	topics = TopicSerializer(many=True, read_only=True)
	cancel_url = serializers.SerializerMethodField()
	update_notes_url = serializers.SerializerMethodField()
	
	class Meta(AppointmentSerializer.Meta):
		fields = AppointmentSerializer.Meta.fields + ['cancel_url', 'update_notes_url']
		read_only_fields = ['patient', 'created_at', 'updated_at']
		
	def get_cancel_url(self, obj):
		if obj.status in ['Scheduled', 'In Progress']:
			request = self.context.get('request')
			if request:
				return request.build_absolute_uri(f'/api/provider/appointments/{obj.id}/cancel')
			
	def get_update_notes_url(self, obj):
		request = self.context.get('request')
		if request:
			return request.build_absolute_uri(f'/api/provider/appointments/{obj.id}/update_notes')
		

class PatientAppointmentCreateSerializer(serializers.ModelSerializer):
	topics = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), many=True)
	
	class Meta:
		model = Appointment
		fields = ['provider', 'topics', 'start_time']
		
	def validate_start_time(self, value):
		if value <= timezone.now():
			raise serializers.ValidationError("Appointment start time must be in the future")
		return value
	
	def validate_topics(self, value):
		if not value:
			raise serializers.ValidationError("At least one topic must be selected")
		return value
	

class ProviderAppointmentCreateSerializer(serializers.ModelSerializer):
	topics = serializers.PrimaryKeyRelatedField(queryset=Topic.objects.all(), many=True)
	
	class Meta:
		model = Appointment
		fields = ['patient', 'topics', 'start_time']
		
	def validate_start_time(self, value):
		if value <= timezone.now():
			raise serializers.ValidationError("Appointment start time must be in the future")
		return value
	
	def validate_topics(self, value):
		if not value:
			raise serializers.ValidationError("At least one topic must be selected")
		return value
	

class AppointmentCancelSerializer(serializers.ModelSerializer):
	class Meta:
		model = Appointment
		fields = ['status']
		read_only_fields = ['provider', 'patient', 'topic', 'start_time', 'provider_notes']

	def validate_status(self, value):
		request = self.context.get('request')
		role = self.context.get('role')
		
		if role == 'patient' and value != 'UserCanceled':
			raise serializers.ValidationError("Patient can only change status to UserCanceled")
		elif role == 'provider' and value != 'ProviderCanceled':
			raise serializers.ValidationError("Provider can only change status to ProviderCanceled")
		
		return value
	

class ProviderNotesSerializer(serializers.ModelSerializer):
	class Meta:
		model = Appointment
		fields = ['provider_notes']
		read_only_fields = ['provider', 'patient', 'topic', 'start_time', 'status']