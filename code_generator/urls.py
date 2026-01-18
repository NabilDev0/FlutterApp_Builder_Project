from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ScreenViewSet, ComponentViewSet, GenerateFlutterView, AuthViewSet

router = DefaultRouter()
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'screens', ScreenViewSet, basename='screen')
router.register(r'components', ComponentViewSet, basename='component')
router.register(r'generate', GenerateFlutterView, basename='generate')
router.register(r'auth', AuthViewSet, basename='auth')

urlpatterns = [
    path('', include(router.urls)),
]
