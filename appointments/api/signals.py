from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Appointment

@receiver(post_save, sender=Appointment)
def check_appointment_status(sender, instance, created, **kwargs):
	"""
    Signal to automatically mark appointments as 'Overdue' if they are past their start time and still in 'Scheduled' status.
    """
	if not created and instance.status == 'Scheduled':
		if instance.start_time < timezone.now():
			instance.status = 'Overdue'
			Appointment.objects.filter(pk=instance.pk).update(status='Overdue')