from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Provider(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)

	def __str__(self):
		return self.user.get_full_name() or self.user.username


class Patient(models.Model):
	user = models.OneToOneField(User, on_delete=models.CASCADE)

	def __str__(self):
		return self.user.get_full_name() or self.user.username


class Topic(models.Model):
	NAME_CHOICES = [
        ('Primary Care Checkup', 'Primary Care Checkup'),
        ('Annual Physical Exam', 'Annual Physical Exam'),
        ('Fatigue', 'Fatigue'),
        ('Headache or Migraine', 'Headache or Migraine'),
        ('Dizziness', 'Dizziness'),
        ('Fever or Chills', 'Fever or Chills'),
        ('Cough or Cold', 'Cough or Cold'),
        ('Bug Bite', 'Bug Bite'),
        ('Rash Evaluation', 'Rash Evaluation'),
        ('Anxiety Counseling', 'Anxiety Counseling'),
        ('Stress Management', 'Stress Management'),
        ('Nutrition Counseling', 'Nutrition Counseling'),
        ('Sleep Disorder Management', 'Sleep Disorder Management'),
    ]
	
	name = models.CharField(max_length=256, choices=NAME_CHOICES, default='Primary Care Checkup')
	duration = models.PositiveIntegerField(help_text="Duration in minutes")

	def __str__(self):
		return f"{self.name} ({self.duration} min)"


class Appointment(models.Model):
	STATUS_CHOICES = [
		('Scheduled', 'Scheduled'),
		('In Progress', 'In Progress'),
		('Completed', 'Completed'),
		('Overdue', 'Overdue'),
		('UserCanceled', 'UserCanceled'),
		('ProviderCanceled', 'ProviderCanceled'),
	]

	provider = models.ForeignKey(Provider, on_delete=models.CASCADE, related_name='appointments')
	patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
	topics = models.ManyToManyField(Topic, related_name='appointments')
	provider_notes = models.TextField(blank=True, null=True)
	status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
	start_time = models.DateTimeField()
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	@property
	def end_time(self):
		"""Calculate end time based on start time and total of all topic durations"""
		total_duration = sum(topic.duration for topic in self.topics.all())
		return self.start_time + timezone.timedelta(minutes=total_duration)
	
	def clean(self):
		"""Validate appointment time is in the future"""
		from django.core.exceptions import ValidationError
		if self.start_time and self.start_time <= timezone.now():
			raise ValidationError("Appointment start time must be in the future")
		
	def __str__(self):
		topics_str = ", ".join(topic.name for topic in self.topics.all())
		return f"{self.provider} - {self.patient} - {topics_str} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"