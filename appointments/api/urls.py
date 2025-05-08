from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PatientAppointmentViewSet, ProviderAppointmentViewSet, TopicViewSet, CustomLogoutView

router = DefaultRouter()
router.register(r'patient/appointments', PatientAppointmentViewSet, basename='patient-appointment')
router.register(r'provider/appointments', ProviderAppointmentViewSet, basename='provider-appointment')
router.register(r'topics', TopicViewSet, basename='topic')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    path('auth/logout/', CustomLogoutView.as_view(), name='logout'),
]
