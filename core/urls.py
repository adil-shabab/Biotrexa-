from django.urls import path
from . import views
from .views import *
from django.contrib.sitemaps.views import sitemap
from .sitemaps import CareerSitemap, DepartmentSitemap, DoctorSitemap, BlogSitemap, HealthCheckupPlanSitemap, StaticViewSitemap

sitemaps = {
    'departments': DepartmentSitemap,
    'doctors': DoctorSitemap,
    'blogs': BlogSitemap,
    'health_checkups': HealthCheckupPlanSitemap,
    'careers': CareerSitemap,
    'static': StaticViewSitemap,
}


urlpatterns = [

    path('checking/', views.initiate_payment, name='initiate_payment'),


    path('check-new-appointments/', views.check_new_appointments, name='check_new_appointments'),
    path('update-alarm-status/', views.update_alarm_status, name='update_alarm_status'),  # New URL



    path('account/', views.dashboard, name='dashboard'), 
    path('account/banners', views.banners, name='banners'), 
    path('account/banners/create', views.create_banner, name='create_banner'), 
    path('account/banners/update/<str:pk>', views.update_banner, name='update_banner'), 
    path('account/banners/delete/<str:pk>', views.delete_banner, name='delete_banner'), 

    path('account/services/', views.departments, name='departments'), 
    path('account/services/create', views.create_department, name='create_department'), 
    path('account/services/update/<slug:slug>', views.update_department, name='update_department'), 
    path('account/services/delete/<slug:slug>', views.delete_department, name='delete_department'), 

    path('account/facilities/', views.facilities, name='facilities'), 
    path('account/facilities/create', views.create_facility, name='create_facility'), 
    path('account/facilities/update/<slug:slug>', views.update_facility, name='update_facility'), 
    path('account/facilities/delete/<slug:slug>', views.delete_facility, name='delete_facility'), 

    path('account/consultation/', views.consultations, name='consultations'), 
    path('account/consultation/create', views.create_consultation, name='create_consultation'), 
    path('account/consultation/update/<slug:slug>', views.update_consultation, name='update_consultation'), 
    path('account/consultation/delete/<slug:slug>', views.delete_consultation, name='delete_consultation'), 

    path('account/second-banner/', views.ad_banners, name='ad_banners'), 
    path('account/second-banner/create', views.create_adbanner, name='create_adbanner'), 
    path('account/second-banner/update/<slug:slug>', views.update_adbanner, name='update_adbanner'), 
    path('account/second-banner/delete/<slug:slug>', views.delete_adbanner, name='delete_adbanner'), 


    path('account/health-package/', views.health_checkup_plans, name='health_checkup_plans'), 
    path('account/health-package/create', views.create_health_checkup_plans, name='create_health_checkup_plans'), 
    path('account/health-package/update/<slug:slug>', views.update_health_checkup_plans, name='update_health_checkup_plans'), 
    path('account/health-package/appointments/<slug:slug>', views.health_checkup_appointments, name='health_checkup_appointments'), 
    path('account/health-package/delete/<slug:slug>', views.delete_health_checkup_plan, name='delete_health_checkup_plan'), 
    path('account/health-package/appointment/<str:pk>/', views.view_checkup_appointment, name='view_checkup_appointment'), 
    path('account/home-sample-package/appointment/<str:pk>', views.view_home_sample_appointment, name='view_home_sample_appointment'), 


    path('account/gallery/create/', views.create_gallery, name='create_gallery'),
    path('account/gallery/delete/<int:gallery_id>/', views.delete_gallery, name='delete_gallery'),
    path('account/gallery/', views.gallery_list, name='gallery_list'),  \


    path('account/doctors/', views.doctors, name='doctors'), 
    path('account/doctors/create', views.create_doctor, name='create_doctor'), 
    path('account/doctors/update/<slug:slug>', views.update_doctor, name='update_doctor'), 
    path('account/doctors/delete/<slug:slug>', views.delete_doctor, name='delete_doctor'), 

    path('account/doctors/<int:doctor_id>/appointments/', views.doctor_appointments, name='doctor_appointments'),

    path('account/timing/<slug:slug>', views.create_timing, name='create_timing'), 
    path('account/timing/delete/<str:pk>', views.delete_timing, name='delete_timing'), 
    path('account/timing/delete/monthly/<str:pk>', views.delete_timing_monthly, name='delete_timing_monthly'), 
    path('account/timing/monthly/create/<str:pk>', views.create_monthly_timing, name='create_monthly_timing'), 
    path('account/leave/<slug:slug>', views.create_leave, name='create_leave'), 
    path('account/leave/delete/<str:pk>', views.delete_leave, name='delete_leave'), 

    
    
    path('account/blogs/', views.blogs, name='blogs'),
    path('account/blogs/create', views.create_blog, name='create_blog'),
    path('account/blogs/update/<slug:slug>', views.update_blog, name='update_blog'),
    path('account/blogs/delete/<str:pk>', views.delete_blog, name='delete_blog'),
    path('account/blogs/<slug:slug>', views.view_blog_comments, name='view_blog_comments'),
    path('account/blogs/<slug:blogSlug>/comments/<slug:commentSlug>', views.view_blog_comment, name='view_blog_comment'),


    path('account/messages/', views.messages, name='messages'), 
    path('account/messages/<slug:slug>', views.message, name='message'), 


    path('account/careers/', views.careers, name='careers'), 
    path('account/careers/create/', views.create_career, name='create_career'), 
    path('account/careers/update/<slug:slug>/', views.update_career, name='update_career'), 
    path('account/careers/delete/<str:pk>/', views.delete_career, name='delete_career'), 
    path('account/careers/<slug:slug>/', views.view_career_applications, name='view_career_applications'), 
    path('account/careers/<slug:careerslug>/application/<slug:applicationslug>/', views.view_career_application, name='view_career_application'),

    path('account/appointments/cancel/<str:pk>/', views.cancel_appointment, name='cancel_appointment'), 

    
    path('account/login/', views.login, name='login'), 
    path('account/logout', views.logout_user, name='logout_user'), 

    path('account/appointments/', views.appointments, name='appointments'), 
    path('account/appointments/add', views.create_appointment_backend, name='create_appointment_backend'), 
    path('account/appointments/<str:pk>/details', views.view_appointment, name='view_appointment'),
    path('api/doctors/department/', DoctorsByDepartmentAPIView.as_view(), name='doctors-by-department'),

    
    path('appointments/add', views.create_appointement_page, name='create_appointement_page'), 
    path('api/create-appointment/', CreateAppointmentAPIView.as_view(), name='create_appointment_api'),
    path('api/handle-payment/', HandlePaymentAPIView.as_view(), name='handle_payment_api'),
    path('handle-payment/', views.handle_payment, name='handle_payment'),


    path('api/check-timings/<int:doctor_id>/<str:date>/', views.check_available_timings, name='check-available-timings'),

    path('account/payments/', PaymentListView.as_view(), name='payments'),
    path('account/home-sample-collections/', views.home_sample_dashboard, name='home_sample_dashboard'),

    path('account/bookings/', views.checkup_bookings, name='checkup_bookings'), 
    path('collect-cash-package/<int:pk>/', collect_cash_checkup, name='collect_cash_checkup'),
    
    path('account/patients/', views.patients, name='patients'), 
    path('account/patients/<int:patient_id>/appointments/', views.patient_appointments, name='patient_appointments'),
    path('account/patients/<int:patient_id>/appointments/create', views.patient_appointments_create, name='patient_appointments_create'),
    path('api/create-appointment/patient', CreateAppointmentPatientAPIView.as_view(), name='create_appointment_patient'),


    path('account/patients/add', views.create_patient, name='create_patient'), 
    path('account/patients/update/<str:pk>', views.update_patient, name='update_patient'), 


    path('api/notifications/hr/unread/', UnreadHRNotificationsView.as_view(), name='unread-notifications'),
    path('api/notifications/hr/mark-read/<int:notification_id>/', MarkHRNotificationAsReadView.as_view(), name='mark-notification-as-read'),
    path('api/notifications/hr/mark-all-read/', MarkAllHRNotificationsAsReadView.as_view(), name='mark-all-notifications-as-read'),
    

    
    path('api/notifications/unread/', UnreadNotificationsView.as_view(), name='unread-notifications'),
    path('api/notifications/mark-read/<int:notification_id>/', MarkNotificationAsReadView.as_view(), name='mark-notification-as-read'),
    path('api/notifications/mark-all-read/', MarkAllNotificationsAsReadView.as_view(), name='mark-all-notifications-as-read'),
    path('account/notifications/', views.notifications, name='notifications'), 

    path('api/create-timing/<slug:doctor_slug>/', create_timing_api, name='create_timing_api'),

    path('account/health-package', views.health_checkup_plans, name='health_checkup_plans'), 
    path('api/create-health-package-booking/', CreateHealthCheckupBookingAPIView.as_view(), name='create_health_checkup_booking'),
    path('api/create-health-package-booking-done/', CreateHealthCheckupBookingDoneAPIView.as_view(), name='create_health_checkup_booking_done'),
    path('api/handle-health-package-payment/', views.handle_health_checkup_payment, name='handle_health_checkup_payment'),
    path('health-package/payment-success/<int:booking_id>/', views.health_checkup_payment_success, name='health_checkup_payment_success'),
    path('health-package/payment-failure/', views.health_checkup_payment_failure, name='health_checkup_payment_failure'),

    path('account/success/payment/<int:appointment_id>/', views.payment_success_account, name='payment_success_account'),
    path('account/failure/payment/', views.payment_failure_account, name='payment_failure_account'),


    path('privacy-policy/', views.privacy_policy, name='privacy_policy'),
    path('terms-and-condition/', views.terms_condition, name='terms_condition'),
    path('', views.homepage, name='homepage'),
    path('about/', views.about, name='about'),
    path('home-sample-collection/', views.create_home_sample_collection_view, name='home_sample_collection'),
    path('gallery/', views.gallery, name='gallery'),
    path('packages/', views.checkups, name='checkups'),
    path('packages/<slug:slug>', views.single_checkup, name='single_checkup'),
    path('facilities/', views.facilities_frontend, name='facilities_frontend'),
    path('facilities/<slug:slug>/', views.facility_frontend, name='facility_frontend'),
    path('services/', views.services, name='services'),
    path('specialities/', views.specialities, name='specialities'),
    path('specialities/<slug:slug>/', views.speciality_detail, name='speciality_detail'),
    path('services/<slug:slug>', views.service, name='service'),
    path('careers/', views.frontend_careers, name='frontend_careers'),
    path('careers/<slug:slug>', views.single_career, name='single_career'),
    path('blogs/', views.frontend_blogs, name='frontend_blogs'),
    path('blogs/<slug:slug>', views.blog, name='blog'),
    path('contact-us/', views.contact, name='contact'),
    path('doctors/', views.frontend_doctors, name='frontend_doctors'),
    path('doctors/<slug:slug>', views.frontend_doctor, name='frontend_doctor'),

    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),

    path('otp/send/', OTPSendView.as_view(), name='otp_send'),
    path('otp/verify/', OTPVerifyView.as_view(), name='otp_verify'),
    path('bookings/', view_bookings, name='view_bookings'),
    path('logout/', logout, name='logout'),  # Add logout URL pattern
]