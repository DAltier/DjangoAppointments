from django.shortcuts import get_object_or_404
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.views import View
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Provider, Patient, Topic, Appointment
from .serializers import (
    ProviderSerializer, PatientSerializer, TopicSerializer,
    AppointmentSerializer, PatientAppointmentCreateSerializer, ProviderAppointmentCreateSerializer,
    PatientAppointmentSerializer, ProviderAppointmentSerializer,
    AppointmentCancelSerializer, ProviderNotesSerializer
)

class IsPatient(permissions.BasePermission):
	def has_permission(self, request, view):
		return Patient.objects.filter(user=request.user).exists()
	
	def has_object_permission(self, request, view, obj):
		return obj.patient.user == request.user
	

class IsProvider(permissions.BasePermission):
	def has_permission(self, request, view):
		return Provider.objects.filter(user=request.user).exists()
	
	def has_object_permission(self, request, view, obj):
		return obj.provider.user == request.user
	

class PatientAppointmentViewSet(viewsets.ModelViewSet):
	permission_classes = [permissions.IsAuthenticated, IsPatient]
	serializer_class = PatientAppointmentSerializer
	http_method_names = ['get', 'post', 'patch', 'head', 'options']

	def get_queryset(self):
		try:
			patient = Patient.objects.get(user=self.request.user)
			return Appointment.objects.filter(patient=patient).order_by('start_time')
		except Patient.DoesNotExist:
			return Appointment.objects.none()
		
	def get_serializer_class(self):
		if self.action == 'create':
			return PatientAppointmentCreateSerializer
		elif self.action == 'cancel':
			return AppointmentCancelSerializer
		return self.serializer_class
	
	def create(self, request, *args, **kwargs):
		patient = get_object_or_404(Patient, user=request.user)
		serializer = self.get_serializer(data=request.data, context={'request': request})

		if serializer.is_valid():
			appointment = serializer.save(patient=patient)
			return Response(PatientAppointmentSerializer(appointment, context={'request': request}).data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	
	@action(detail=True, methods=['get', 'post', 'patch'])
	def cancel(self, request, pk=None):
		appointment = self.get_object()

		if appointment.status not in ['Scheduled', 'In Progress']:
			return Response({"error": "Only scheduled or in-progress appointments can be canceled"}, status=status.HTTP_400_BAD_REQUEST)
		
		# GET requests, show a confirmation page
		if request.method == 'GET':
			from django.shortcuts import render
			return render(request, 'api/cancel_confirmation.html', {
				'appointment': appointment,
				'cancel_status': 'UserCanceled',
				'return_url': '/api/patient/appointments/'
			})
		
		# POST requests from the form
		data = {'status': 'UserCanceled'}
		if request.method == 'POST':
			data = request.POST.dict()

		serializer = AppointmentCancelSerializer(
			appointment, 
			data=data,
			partial=True,
			context={'request': request, 'role': 'patient'}
		)

		if serializer.is_valid():
			updated_appointment = serializer.save()
			if request.method == 'POST':
				from django.shortcuts import redirect
				return redirect('/api/patient/appointments/')
			return Response(
				PatientAppointmentSerializer(updated_appointment, context={'request': request}).data
			)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	

class ProviderAppointmentViewSet(viewsets.ModelViewSet):
	permission_classes = [permissions.IsAuthenticated, IsProvider]
	serializer_class = ProviderAppointmentSerializer
	http_method_names = ['get', 'post', 'patch', 'head', 'options']

	def get_queryset(self):
		try:
			provider = Provider.objects.get(user=self.request.user)
			return Appointment.objects.filter(provider=provider).order_by('start_time')
		except Provider.DoesNotExist:
			return Appointment.objects.none()
		
	def get_serializer_class(self):
		if self.action == 'create':
			return ProviderAppointmentCreateSerializer
		elif self.action == 'cancel':
			return AppointmentCancelSerializer
		elif self.action == 'update_notes':
			return ProviderNotesSerializer
		return self.serializer_class
	
	def create(self, request, *args, **kwargs):
		provider = get_object_or_404(Provider, user=request.user)
		serializer = self.get_serializer(data=request.data, context={'request': request})

		if serializer.is_valid():
			appointment = serializer.save(provider=provider)
			return Response(ProviderAppointmentSerializer(appointment, context={'request': request}).data, status=status.HTTP_201_CREATED)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	
	@action(detail=True, methods=['get', 'post', 'patch'])
	def cancel(self, request, pk=None):
		appointment = self.get_object()

		if appointment.status not in ['Scheduled', 'In Progress']:
			return Response({"error": "Only scheduled or in-progress appointments can be canceled"}, status=status.HTTP_400_BAD_REQUEST)
		
		# GET requests, show a confirmation page
		if request.method == 'GET':
			from django.shortcuts import render
			return render(request, 'api/cancel_confirmation.html', {
				'appointment': appointment,
				'cancel_status': 'ProviderCanceled',
				'return_url': '/api/provider/appointments/'
			})
		
		# POST requests from the form
		data = {'status': 'ProviderCanceled'}
		if request.method == 'POST':
			data = request.POST.dict()

		serializer = AppointmentCancelSerializer(
			appointment, 
			data=data,
			partial=True,
			context={'request': request, 'role': 'provider'}
		)

		if serializer.is_valid():
			updated_appointment = serializer.save()
			if request.method == 'POST':
				from django.shortcuts import redirect
				return redirect('/api/provider/appointments/')
			return Response(
				ProviderAppointmentSerializer(updated_appointment, context={'request': request}).data
			)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	
	@action(detail=True, methods=['get', 'post', 'patch'])
	def update_notes(self, request, pk=None):
		appointment = self.get_object()
		
		# GET requests, show a form to edit notes
		if request.method == 'GET':
			from django.shortcuts import render
			return render(request, 'api/update_notes.html', {
				'appointment': appointment,
				'return_url': '/api/provider/appointments/'
			})
		
		# POST requests from the form
		data = {}
		if request.method == 'POST':
			data = request.POST.dict()
		else:
			data=request.data

		serializer = ProviderNotesSerializer(
			appointment, 
			data=data,
			partial=True,
		)

		if serializer.is_valid():
			updated_appointment = serializer.save()
			if request.method == 'POST':
				from django.shortcuts import redirect
				return redirect('/api/provider/appointments/')
			return Response(
				ProviderAppointmentSerializer(updated_appointment, context={'request': request}).data
			)
		return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
	

class TopicViewSet(viewsets.ReadOnlyModelViewSet):
	permission_classes = [permissions.IsAuthenticated]
	serializer_class = TopicSerializer
	queryset = Topic.objects.all()


class CustomLogoutView(View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect('/api/auth/login/')