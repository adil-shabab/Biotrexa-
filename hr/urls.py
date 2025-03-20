from django.urls import path
from .import views


urlpatterns = [
    path('dashboard/', views.hr_dashboard, name='hr_dashboard'),
    path('careers/', views.hr_careers, name='hr_careers'), 
    path('careers/create', views.hr_create_career, name='hr_create_career'), 
    path('careers/update/<slug:slug>', views.hr_update_career, name='hr_update_career'), 
    path('careers/delete/<str:pk>', views.hr_delete_career, name='hr_delete_career'), 
    path('careers/<slug:slug>', views.hr_view_career_applications, name='hr_view_career_applications'), 
    path('careers/<slug:careerslug>/application/<slug:applicationslug>', views.hr_view_career_application, name='hr_view_career_application'),

]