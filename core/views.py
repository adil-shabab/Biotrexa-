from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .forms import *
from .models import *
from .serializers import *
from django.contrib import messages as msg
from django.utils.text import slugify
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse, HttpResponseBadRequest
import datetime
from django.utils import timezone
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import razorpay
from django.conf import settings
import json
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import AvailableTimeSerializer, MonthlyTimingSerializer, DoctorSerializer, NotificationSerializer
import logging
from rest_framework import status
from rest_framework.views import APIView
import uuid
from .filters import RazorpayPaymentDetailsFilter
from django_filters.views import FilterView
from django.db.models import Sum
from datetime import timedelta  # Import timedelta
from django.db.models import Count
from django.utils.decorators import method_decorator
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.urls import reverse
from django.utils.dateformat import DateFormat
from django.core.paginator import Paginator
from django.db.models import Q
from django.db.models.functions import ExtractMonth

from django.views.decorators.http import require_POST
from django.views.decorators.http import require_POST
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
from hr.models import *


import requests
import uuid
from django.conf import settings
from django.shortcuts import render, redirect
from phonepe.sdk.pg.payments.v1.models.request.pg_pay_request import PgPayRequest
from phonepe.sdk.pg.env import Env
import requests, hashlib, base64, json

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend



payment_url_phonephe = "https://api.phonepe.com/apis/hermes/pg/v1/pay"
merchant_id_phonephe = "M1NPYDEI1MD3"
salt_key_phonephe = "94f6e054-eb38-4153-b225-bb87da447a8d"
phonephe_Env = "PROD"
salt_index_phonephe = 1



def initiate_payment(request):
    
    merchant_transaction_id = "MT7854386455115104"  # Replace with a dynamically generated transaction ID if needed
    request.session['merchantTransactionId'] = merchant_transaction_id  # Store in session for later use


    
    payload = {
        "merchantId": "M1NPYDEI1MD3",  # Ensure this is the correct sandbox merchant ID
        "merchantTransactionId": merchant_transaction_id,
        "merchantUserId": "MUID123",
        "amount": 100,
        "redirectUrl": "https://ngrhealthcare.com/handle-payment/",
        "redirectMode": "REDIRECT",
        "callbackUrl": "https://ngrhealthcare.com/handle-payment/",
        "mobileNumber": "9999999999",
        "paymentInstrument": {"type": "PAY_PAGE"}
    }



    # Encode payload to Base64
    payload_str = json.dumps(payload)
    base64_payload = base64.b64encode(payload_str.encode()).decode()


    # Compute the checksum
    salt_key = "94f6e054-eb38-4153-b225-bb87da447a8d"  # Make sure this is the correct sandbox salt key
    salt_index = "1"  # Ensure this matches PhonePe's sandbox configuration
    checksum_str = f"{base64_payload}/pg/v1/pay{salt_key}"
    checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + "###" + salt_index

    # Headers
    headers = {
        "accept": "application/json",
        "Content-Type": "application/json",
        "X-VERIFY": checksum
    }

    # Send the request
    response = requests.post(payment_url_phonephe, json={"request": base64_payload}, headers=headers)
    
    try:
        response_data = response.json()
        if response_data.get("success"):
            payment_url = response_data["data"]["instrumentResponse"]["redirectInfo"]["url"]
            return HttpResponseRedirect(payment_url)
        else:
            return JsonResponse({"error": "Failed to initiate payment", "details": response_data})
    except ValueError:
        return JsonResponse({"error": "Non-JSON response", "details": response.text})









def check_new_appointments(request):
    # Fetch notifications that are unread and not yet alarmed
    unread_notifications = Notification.objects.filter(type='appointment', read_status=False, is_alarmed=False)
    
    # Count the number of such notifications
    count = unread_notifications.count()
    
    # Get the IDs of the notifications
    notification_ids = list(unread_notifications.values_list('id', flat=True))
    
    return JsonResponse({'new_appointments': count, 'notification_ids': notification_ids})






@csrf_exempt
@require_POST
def update_alarm_status(request):
    try:
        data = json.loads(request.body)
        notification_ids = data.get('notification_ids', [])
        
        # Update the is_alarmed field to True for the notifications
        Notification.objects.filter(id__in=notification_ids).update(is_alarmed=True)
        
        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})





class FetchProfile(APIView):
    def get(self, request):
        try:
            profile = Summary.objects.get(user=request.user)
            print(request.user)
        except Summary.DoesNotExist:
            raise Http404("Profile does not exist")

        serializer = SummarySerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)




@method_decorator(login_required, name='dispatch')
class UnreadNotificationsView(APIView):
    def get(self, request):
        notifications = Notification.objects.filter(read_status=False).order_by('-created_at')
        notifications_data = [
            {
                'id': notification.id,
                'message': notification.message,
                'created_at': naturaltime(notification.created_at),
                'redirection_url': notification.redirection_url
            }
            for notification in notifications
        ]
        return Response(notifications_data, status=status.HTTP_200_OK)



@method_decorator(login_required, name='dispatch')
class MarkNotificationAsReadView(APIView):
    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id)
        notification.read_status = True
        notification.first_read_by = request.user
        notification.save()
        return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)


@method_decorator(login_required, name='dispatch')
class MarkAllNotificationsAsReadView(APIView):
    def post(self, request):
        Notification.objects.filter(read_status=False).update(read_status=True)
        return Response({'message': 'All notifications marked as read.'}, status=status.HTTP_200_OK)








class UnreadHRNotificationsView(APIView):
    def get(self, request):
    
        notifications = NotificationHR.objects.filter(read_status=False,).order_by('-created_at')
        notifications_data = [
            {
                'id': notification.id,
                'message': notification.message,
                'created_at': naturaltime(notification.created_at),
                'redirection_url': notification.redirection_url
            }
            for notification in notifications
        ]
        return Response(notifications_data, status=status.HTTP_200_OK)

class MarkHRNotificationAsReadView(APIView):
    def post(self, request, notification_id):
        notification = get_object_or_404(NotificationHR, id=notification_id)   
        notification.read_status = True
        notification.save()
        return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)


class MarkAllHRNotificationsAsReadView(APIView):
    def post(self, request):
        NotificationHR.objects.filter(read_status=False).update(read_status=True)
        return Response({'message': 'All notifications marked as read.'}, status=status.HTTP_200_OK)









# message view 
@login_required(login_url='login')
def notifications(request):
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    notifications = Notification.objects.all().order_by('-created_at')
    context = {'notifications': notifications,}
    return render(request, 'backend/notifications.html', context)







@login_required(login_url='login')
def dashboard(request):

    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')


    today = timezone.now()
    start_of_month = today.replace(day=1)
    start_of_last_month = (start_of_month - timedelta(days=1)).replace(day=1)
    end_of_last_month = start_of_month - timedelta(days=1)

    # Appointments and Patients
    this_month_appointments = Appointment.objects.filter(date__gte=start_of_month, status='COMPLETED').count()
    last_month_appointments = Appointment.objects.filter(date__gte=start_of_last_month, date__lte=end_of_last_month, status='COMPLETED').count()
    this_month_patients = Patient.objects.filter(created_at__gte=start_of_month).count()
    last_month_patients = Patient.objects.filter(created_at__gte=start_of_last_month, created_at__lte=end_of_last_month).count()

    appointments_percentage_change = 0
    if last_month_appointments > 0:
        appointments_percentage_change = ((this_month_appointments - last_month_appointments) / last_month_appointments) * 100
    elif this_month_appointments > 0:
        appointments_percentage_change = 100

    patients_percentage_change = 0
    if last_month_patients > 0:
        patients_percentage_change = ((this_month_patients - last_month_patients) / last_month_patients) * 100
    elif this_month_patients > 0:
        patients_percentage_change = 100

    # Payments
    this_month_payments = RazorpayPaymentDetails.objects.filter(created_at__gte=start_of_month)
    total_this_month_payments = this_month_payments.aggregate(Sum('amount'))['amount__sum'] or 0
    last_month_payments = RazorpayPaymentDetails.objects.filter(created_at__gte=start_of_last_month, created_at__lte=end_of_last_month)
    total_last_month_payments = last_month_payments.aggregate(Sum('amount'))['amount__sum'] or 0

    payments_percentage_change = 0
    if total_last_month_payments > 0:
        payments_percentage_change = ((total_this_month_payments - total_last_month_payments) / total_last_month_payments) * 100
    elif total_this_month_payments > 0:
        payments_percentage_change = 100

    # Total payments of all time
    total_all_time_payments = RazorpayPaymentDetails.objects.aggregate(Sum('amount'))['amount__sum'] or 0

    # Payment method percentages for this month
    total_this_month_payments_cash = this_month_payments.filter(payment_method='cash').aggregate(Sum('amount'))['amount__sum'] or 0
    total_this_month_payments_online = this_month_payments.filter(payment_method='online').aggregate(Sum('amount'))['amount__sum'] or 0
    total_this_month_payments_sum = total_this_month_payments_cash + total_this_month_payments_online

    cash_payments_percentage = 0
    online_payments_percentage = 0
    if total_this_month_payments_sum > 0:
        cash_payments_percentage = (total_this_month_payments_cash / total_this_month_payments_sum) * 100
        online_payments_percentage = (total_this_month_payments_online / total_this_month_payments_sum) * 100

    # Payment method percentages for all time
    total_all_time_payments_cash = RazorpayPaymentDetails.objects.filter(payment_method='cash').aggregate(Sum('amount'))['amount__sum'] or 0
    total_all_time_payments_online = RazorpayPaymentDetails.objects.filter(payment_method='online').aggregate(Sum('amount'))['amount__sum'] or 0

    total_cash_payments_percentage = 0
    total_online_payments_percentage = 0
    if total_all_time_payments > 0:
        total_cash_payments_percentage = (total_all_time_payments_cash / total_all_time_payments) * 100
        total_online_payments_percentage = (total_all_time_payments_online / total_all_time_payments) * 100

    # Prepare data for charts
    appointments_per_month = Appointment.objects.filter(status='COMPLETED')\
        .annotate(month=ExtractMonth('date'))\
        .values('month')\
        .annotate(count=Count('id'))\
        .order_by('month')

    monthly_appointments_data = [0] * 12
    for item in appointments_per_month:
        monthly_appointments_data[item['month'] - 1] = item['count']




    
    today = timezone.now().date()
    appointments = Appointment.objects.filter(status='COMPLETED', date=today)
    upcoming_appointments = []

    now = timezone.now()

    for appointment in appointments:
        # Get the RazorpayPaymentDetails for each appointment
        payment_details = RazorpayPaymentDetails.objects.filter(appointment=appointment).first()

        # Get the related object (AvailableTime or MonthlyTiming)
        content_type = appointment.content_type
        related_object = content_type.get_object_for_this_type(id=appointment.object_id)

        # Determine if the appointment is past or upcoming
        if isinstance(related_object, AvailableTime):
            # Combine appointment date with the start time from AvailableTime
            appointment_datetime = timezone.datetime.combine(appointment.date, related_object.start_time)
        else:
            # Combine the date and start time from MonthlyTiming
            appointment_datetime = timezone.datetime.combine(related_object.date, related_object.start_time)

        # Make appointment_datetime timezone-aware
        appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())

        detailed_appointment = {
            'appointment': appointment,
            'payment_details': payment_details,
            'related_object': related_object
        }

        upcoming_appointments.append(detailed_appointment)


    
    total_patients = Patient.objects.all().count()
    total_doctors = Doctor.objects.all().count()

    context = {
        'this_month_appointments': this_month_appointments,
        'appointments_percentage_change': int(appointments_percentage_change),
        'this_month_patients': this_month_patients,
        'total_patients': total_patients,
        'total_doctors': total_doctors,
        'patients_percentage_change': int(patients_percentage_change),
        'total_this_month_payments': total_this_month_payments / 100,  # convert paise to rupees
        'payments_percentage_change': int(payments_percentage_change),
        'cash_payments_percentage': int(cash_payments_percentage),
        'online_payments_percentage': int(online_payments_percentage),
        'total_all_time_payments': total_all_time_payments / 100,  # convert paise to rupees
        'total_cash_payments_percentage': int(total_cash_payments_percentage),
        'total_online_payments_percentage': int(total_online_payments_percentage),
        'monthly_appointments_data': monthly_appointments_data,
        'upcoming_appointments': upcoming_appointments
    }

    return render(request, 'backend/dashboard.html', context)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_timing_api(request, doctor_slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    doctor = get_object_or_404(Doctor, slug=doctor_slug)
    selected_slots = request.data.get('selected_slots', [])
    slot_count = request.data.get('slot', 1)

    if not selected_slots:
        return Response({"error": "No slots selected"}, status=status.HTTP_400_BAD_REQUEST)

    for slot in selected_slots:
        day, times = slot.split(' ', 1)
        start_time, end_time = times.split('-')

        # Convert strings to time objects
        start_time_obj = datetime.datetime.strptime(start_time.strip(), '%H:%M').time()
        end_time_obj = datetime.datetime.strptime(end_time.strip(), '%H:%M').time()

        # Check for overlapping times
        overlapping_timings = AvailableTime.objects.filter(
            doctor=doctor,
            day=day,
            status='active',
            start_time__lt=end_time_obj,
            end_time__gt=start_time_obj
        )

        if overlapping_timings.exists():
            return Response(
                {"error": f"The doctor already has another timing in this time range for {day}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create the available time object
        AvailableTime.objects.create(
            doctor=doctor,
            day=day,
            start_time=start_time_obj,
            end_time=end_time_obj,
            slot=slot_count,
            status='active',
            remaining_slots=slot_count
        )

    return Response({"success": "Timings added successfully"}, status=status.HTTP_201_CREATED)




@login_required(login_url='login')
def gallery_list(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    gallery = Gallery.objects.all().order_by('-created_at')
    return render(request, 'backend/gallery.html', {'gallery': gallery})



# Create View for Gallery
@login_required(login_url='login')
def create_gallery(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    if request.method == 'POST':
        form = GalleryForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            msg.success(request, "Gallery Image Uploaded")
            return redirect('gallery_list')  # Redirect to the gallery list page after creation
    else:
        form = GalleryForm()
    return render(request, 'backend/gallery-form.html', {'form': form})


# Delete View for Gallery
@login_required(login_url='login')
def delete_gallery(request, gallery_id):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    gallery = get_object_or_404(Gallery, id=gallery_id)
    gallery.delete()
    msg.success(request, "Gallery Image Deleted Successfully")
    return redirect('gallery_list')  # Redirect to the gallery list page after deletion






    


# department view 
@login_required(login_url='login')  
def ad_banners(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    ad_banners = AdBanner.objects.all()
    context ={ 'ad_banners': ad_banners }
    return render(request, 'backend/ad-banners.html', context)



@login_required(login_url='login')
def create_adbanner(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    if request.method == 'POST':
        form = AdBannerForm(request.POST, request.FILES)
        if form.is_valid():
            msg.success(request, "Ad Banner Created Successfully")
            adbanner = form.save()
            # After saving, you can redirect to the list of AdBanners or any other appropriate page
            return redirect('ad_banners')  # Replace with the correct URL name
    else:
        form = AdBannerForm()

    context = {
        'form': form,
    }
    return render(request, 'backend/create-ad-banner.html', context)




@login_required(login_url='login')
def update_adbanner(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    banner = get_object_or_404(AdBanner, slug=slug)
    if request.method == 'POST':
        form = AdBannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            msg.success(request, "Ad Banner Updated Successfully")
            return redirect('ad_banners')  # Replace with the correct URL name for your list view
    else:
        form = AdBannerForm(instance=banner)

    context = {
        'form': form,
        'banner': banner,
    }
    return render(request, 'backend/update-ad-banner.html', context)



@login_required(login_url='login')
def delete_adbanner(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    adbanner = get_object_or_404(AdBanner, slug=slug)
    adbanner.delete()
    msg.success(request, "Ad Banner Deleted Successfully")
    return redirect('ad_banners')  # Replace with the correct URL name for your list view



# banner view 
@login_required(login_url='login')
def banners(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    banners = Banner.objects.all()
    context = {'banners': banners}
    return render(request, 'backend/banners.html',context)


@login_required(login_url='login')
def create_banner(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            msg.success(request, "Banner Created Successfully")
            return redirect('banners')  
        else:
           msg.error(request, 'Failed to Create banner. Please check the form for errors.')
            
    else:
        form = BannerForm()
    return render(request, 'backend/create-banner.html', {'form': form})
    

@login_required(login_url='login')
def update_banner(request, pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    banner = get_object_or_404(Banner, id=pk)
    print(type(banner.status))
    if request.method == 'POST':
        form = BannerForm(request.POST, request.FILES, instance=banner)
        if form.is_valid():
            form.save()
            msg.success(request, 'Banner Updated Successfully')
            return redirect('banners')  
        else:
            msg.error(request, 'Failed to update banner. Please check the form for errors.')
    else:
        form = BannerForm(instance=banner)
    return render(request, 'backend/update-banner.html', {'form': form, 'banner': banner})




@login_required(login_url='login')
def delete_banner(request, pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    try:
        banner = Banner.objects.get(pk=pk)
        banner.delete()
        msg.success(request, 'Banner deleted successfully.')
        return redirect('banners')
    except Banner.DoesNotExist:
        msg.error(request, 'Banner not found.')
        return redirect('banners')















# doctors view 
@login_required(login_url='login')
def doctors(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    doctors = Doctor.objects.all().order_by('priority')
    context ={ 'doctors': doctors }
    return render(request, 'backend/doctors.html', context)


@login_required(login_url='login')
def create_doctor(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.slug = slugify(doctor.name)
            original_slug = doctor.slug
            counter = 1
            while Doctor.objects.filter(slug=doctor.slug).exists():
                doctor.slug = f'{original_slug}-{counter}'
                counter += 1
            doctor.save()
            msg.success(request, "Doctor Added Successfully")
            return redirect('doctors')  # Replace with your redirect URL
    else:
        form = DoctorForm()
    return render(request, 'backend/create-doctor.html', {'form': form})


@login_required(login_url='login')
def update_doctor(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    doctor = Doctor.objects.get(slug=slug)
    if request.method == 'POST':
        form = DoctorForm(request.POST, request.FILES, instance=doctor)
        if form.is_valid():
            doctor = form.save(commit=False)
            doctor.slug = slugify(doctor.name)
            original_slug = doctor.slug
            counter = 1
            while Doctor.objects.filter(slug=doctor.slug).exists():
                doctor.slug = f'{original_slug}-{counter}'
                counter += 1
            doctor.save()
            msg.success(request, "Doctor Updated Successfully")
            return redirect('doctors')  # Replace with your redirect URL
    else:
        form = DoctorForm(instance =doctor)
    return render(request, 'backend/update-doctor.html', {'form': form, 'doctor':doctor})


@login_required(login_url='login')
def delete_doctor(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    try:
        doctor = Doctor.objects.get(slug=slug)
        doctor.delete()
        msg.success(request, 'Doctor deleted successfully.')
        return redirect('doctors')
    except Doctor.DoesNotExist:
        msg.error(request, 'doctor not found.')
        return redirect('doctor')



@login_required(login_url='login')
def create_monthly_timing(request, pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    if request.method == 'POST':
        form2 = MonthlyTimeForm(request.POST)
        if form2.is_valid():
            timing = form2.save(commit=False)
            doctor = get_object_or_404(Doctor, id=pk)
            timing.doctor = doctor  # Assign the doctor to the timing instance
            timing.remaining_slots = timing.slot


            # Check if the start date is today or in the future
            if timing.date < timezone.now().date():
                msg.error(request, "The date must be today or in the future. Past dates are not allowed.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            # Check if the start time is less than end time
            if timing.start_time >= timing.end_time:
                msg.error(request, "Ending Time must be greater than Starting Time.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            # Check if the same doctor has any other timing in this time range
            overlapping_timings = MonthlyTiming.objects.filter(
                doctor=doctor,
                date=timing.date,
                start_time__lt=timing.end_time,
                end_time__gt=timing.start_time
            )

            if overlapping_timings.exists():
                msg.error(request, "The doctor already has another timing in this time range. Please choose a different time.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

            # If all checks pass, save the timing
            timing.save()
            msg.success(request, "Timing Updated Successfully")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            # Gather all form errors
            error_messages = "Please correct the errors below:\n"
            for field, errors in form2.errors.items():
                for error in errors:
                    error_messages += f"{field}: {error}\n"
            msg.error(request, error_messages)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    
            
@login_required(login_url='login')
def create_timing(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    doctor = get_object_or_404(Doctor, slug=slug)
    timings = AvailableTime.objects.filter(doctor=doctor, status='active').order_by('day', 'start_time')
    monthly_timing = MonthlyTiming.objects.filter(doctor=doctor, status='active')

    if request.method == 'POST':
        form = AvailableTimeForm(request.POST)
        form2 = MonthlyTimeForm(request.POST)
        if form.is_valid():
            timing = form.save(commit=False)
            timing.doctor = doctor
            timing.remaining_slots = timing.slot

            # Check if the same doctor has any other timing in this time
            overlapping_timings = AvailableTime.objects.filter(
                doctor=doctor,
                day=timing.day,
                status='active',
                start_time__lt=timing.end_time,
                end_time__gt=timing.start_time
            )

            # Check if the start time is less than end time
            if timing.start_time >= timing.end_time:
                msg.error(request, "Ending Time must be greater than Starting Time.")
            elif overlapping_timings.exists():
                msg.error(request, "The doctor already has another timing in this time range. Please choose a different time.")
            else:
                timing.save()
                msg.success(request, "Timing Updated Successfully")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
        else:
            error_messages = "Please correct the errors below:<br>"
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages += f"{field}: {error}<br>"
            msg.error(request, error_messages)
    else:
        form = AvailableTimeForm()
        form2 = MonthlyTimeForm()

    return render(request, 'backend/create-timing.html', {'doctor': doctor, 'form': form, 'timings': timings, 'form2': form2, 'monthly_timing': monthly_timing})


@login_required(login_url='login')
def delete_timing(request, pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    try:
        timing = AvailableTime.objects.get(id=pk)
        
        # Check if there are any appointments for this timing
        appointments = Appointment.objects.filter(content_type=ContentType.objects.get_for_model(AvailableTime), object_id=timing.id)
        
        # Separate past and upcoming appointments
        upcoming_appointments = appointments.filter(date__gte=timezone.now())
        past_appointments = appointments.filter(date__lt=timezone.now())

        if upcoming_appointments.exists():
            # Make status inactive for upcoming appointments and provide a message
            timing.status = 'inactive'
            timing.save()
            msg.warning(request, f'Timing has {upcoming_appointments.count()} upcoming appointment(s). The timing is now inactive, and new appointments cannot be created. Please attend to the already booked appointments.')
        else:
            # Delete timing if there are no upcoming appointments
            timing.status = 'inactive'
            timing.save()
            msg.success(request, 'Timing deleted successfully.')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except AvailableTime.DoesNotExist:
        msg.error(request, 'Timing not found.')
        return redirect('doctor')



@login_required(login_url='login')
def delete_timing_monthly(request, pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    try:
        timing = MonthlyTiming.objects.get(id=pk)
        
        # Check if there are any appointments for this timing
        appointments = Appointment.objects.filter(content_type=ContentType.objects.get_for_model(MonthlyTiming), object_id=timing.id)
        
        # Separate past and upcoming appointments
        upcoming_appointments = appointments.filter(date__gte=timezone.now())
        past_appointments = appointments.filter(date__lt=timezone.now())

        if upcoming_appointments.exists():
            # Make status inactive for upcoming appointments and provide a message
            timing.status = 'inactive'
            timing.save()
            msg.warning(request, f'This iming has {upcoming_appointments.count()} upcoming appointment(s). The timing is now inactive, and new appointments cannot be created. Please attend to the already booked appointments.')
        else:
            # Delete timing if there are no upcoming appointments
            timing.status = 'inactive'
            timing.save()
            msg.success(request, 'Timing deleted successfully.')
        
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    except MonthlyTiming.DoesNotExist:
        msg.error(request, 'Timing not found.')
        return redirect('doctor')





# blog View Section 
@login_required(login_url='login')
def blogs(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    blogs = Blog.objects.all()
    context = {'blogs': blogs}
    return render(request, 'backend/blogs.html', context)


@login_required(login_url='login')
def delete_blog(request,pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    blog = Blog.objects.get(id=pk)
    blog.delete()
    msg.success(request, "Blog Deleted Successfully")
    return redirect("blogs")




@login_required(login_url='login')
def create_blog(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            msg.success(request, "Blog created successfully")
            return redirect('blogs')
        else:
            msg.error(request, "There were errors in your form. Please correct them.")
            print(form.errors)
    else:
        form = BlogForm()
    return render(request, 'backend/create-blog.html', {'form': form})


@login_required(login_url='login')
def update_blog(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    blog = Blog.objects.get(slug=slug)
    if request.method == 'POST':
        form = BlogForm(request.POST, request.FILES, instance=blog)
        if form.is_valid():
            form.save()
            msg.success(request,"Blog Updated Successfully")
            return redirect('blogs')  
        else:
            msg.error(request, "There were errors in your form. Please correct them.")
            print(form.errors)
    else:
        form = BlogForm(instance=blog)
    return render(request, 'backend/update-blog.html', {'form': form, 'blog': blog} )




@login_required(login_url='login')
def view_blog_comments(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    blog = Blog.objects.get(slug=slug)
    comments = BlogComment.objects.filter(blog=blog)
    comments_count = BlogComment.objects.filter(blog=blog).count()
    now = datetime.datetime.now().strftime('%I:%M %p')
    context = {'blog': blog, 'comments': comments, 'comments_count':comments_count,'now':now}
    return render(request, 'backend/blog-comments-view.html', context)



@login_required(login_url='login')
def view_blog_comment(request, blogSlug, commentSlug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    blog = get_object_or_404(Blog, slug=blogSlug)
    comment = get_object_or_404(BlogComment, slug=commentSlug)
    comments_count = BlogComment.objects.all().count()
    now = datetime.datetime.now().strftime('%I:%M %p')
    context = {
        'blog': blog,
        'comment': comment,
        'comments_count': comments_count,
        'now': now,
        'rating_range': range(1, 6)  # Pass a range of 1 to 5 for star ratings
    }
    return render(request, 'backend/blog-comments-view-inner.html', context)




@login_required(login_url='login')  
def health_checkup_plans(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    plans = HealthCheckupPlan.objects.all().order_by('-created_at')
    
    context = {
        'plans': plans
    }
    return render(request, 'backend/checkup-plans.html', context)


@login_required(login_url='login')  
def health_checkup_appointments(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    plan = HealthCheckupPlan.objects.get(slug=slug)
    appointments = HealthCheckupBooking.objects.filter(plan=plan,  status='COMPLETED').order_by('-created_at')
    
    context = {
        'plan': plan,
        'appointments': appointments
    }
    return render(request, 'backend/checkup-appointments.html', context)






@login_required(login_url='login')  
def checkup_bookings(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    appointments = HealthCheckupBooking.objects.filter(status='COMPLETED').order_by('-created_at')
    
    context = {
        'appointments': appointments
    }
    return render(request, 'backend/checkup-bookings.html', context)




@login_required(login_url='login')  
def collect_cash_checkup(request, pk):
    booking = get_object_or_404(HealthCheckupBooking, id=pk)
    payment = RazorpayPaymentDetails.objects.filter(booking=booking).first()

    if not payment:
        msg.error(request, "No payment record found for this booking.")
        return redirect('some_view_name')  # Redirect to a relevant page

    # Mark payment as completed
    payment.status = 'COMPLETED'
    payment.order_id = str(uuid.uuid4())  # Generates a unique order ID
    payment.payment_id = str(uuid.uuid4())  # Generates a unique payment ID
    payment.save()


    booking.payment_id = str(uuid.uuid4())
    booking.save()

    msg.success(request, "Payment marked as completed successfully!")
    return redirect('checkup_bookings')  # Redirect to a relevant page


@login_required(login_url='login')  
def home_sample_dashboard(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    appointments = HomeSampleCollection.objects.all().order_by('-created_at')
    
    context = {
        'appointments': appointments
    }
    return render(request, 'backend/home-sample-collection.html', context)


def view_checkup_appointment(request, pk):
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request, 'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else:
        return redirect('homepage')

    appointment = get_object_or_404(HealthCheckupBooking, id=pk)
    print(appointment.home_sample_collection)
    payment_details = RazorpayPaymentDetails.objects.filter(booking=appointment).first()
    detailed_appointment = {
        'appointment': appointment,
        'payment_details': payment_details,
    }


    if request.method == "POST" and request.FILES.get("report"):
        appointment.report = request.FILES["report"]
        appointment.save()
        msg.success(request, "Report uploaded successfully!")
        return redirect('view_checkup_appointment', pk=appointment.id)  # Stay on the same page

    return render(request, 'backend/view-checkup-booking.html', {'detailed_appointment': detailed_appointment})






def view_home_sample_appointment(request, pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    appointment = get_object_or_404(HomeSampleCollection, id=pk)
    detailed_appointment = {
        'appointment': appointment,
    }

    return render(request, 'backend/view-home-sample-booking.html', {'detailed_appointment': detailed_appointment})





@login_required(login_url='login')
def create_health_checkup_plans(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    if request.method == 'POST':
        form = CheckupForm(request.POST, request.FILES)
        if form.is_valid():
            plan = form.save(commit=False)
            original_slug = slugify(plan.title)
            unique_slug = original_slug
            counter = 1
            while HealthCheckupPlan.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{original_slug}-{counter}'
                counter += 1
            plan.slug = unique_slug
            plan.save()
            msg.success(request, "Health Checkup Plan Created Successfully")
            return redirect('health_checkup_plans')  # Replace with your redirect URL

    else:
        form = CheckupForm()
    return render(request, 'backend/create-plan.html', {'form': form})





@login_required(login_url='login')
def update_health_checkup_plans(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    plan = get_object_or_404(HealthCheckupPlan, slug=slug)
    if request.method == 'POST':
        form = CheckupForm(request.POST, request.FILES, instance=plan)
        if form.is_valid():
            plan = form.save(commit=False)
            original_slug = slugify(plan.title)
            unique_slug = original_slug
            counter = 1
            while HealthCheckupPlan.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{original_slug}-{counter}'
                counter += 1
            plan.slug = unique_slug
            plan.save()
            
            msg.success(request, "Health Checkup plan Updated Successfully")
            return redirect('health_checkup_plans')  # Replace with your redirect URL
        else:
            msg.error(request, 'Failed to update Plan. Please check the form for errors.')
    else:
        form = CheckupForm(instance=plan)
    return render(request, 'backend/update-plan.html', {'form': form, 'plan': plan})



@login_required(login_url='login')
def delete_health_checkup_plan(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    try:
        plan = HealthCheckupPlan.objects.get(slug=slug)
        plan.delete()
        msg.success(request, 'Health checkup plan deleted successfully.')
        return redirect('health_checkup_plans')
    except HealthCheckupPlan.DoesNotExist:
        msg.error(request, 'Plan not found.')
        return redirect('health_checkup_plans')







# department view 
@login_required(login_url='login')  
def departments(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    departments = Department.objects.all().order_by('priority')
    context ={ 'departments': departments }
    return render(request, 'backend/departments.html', context)



@login_required(login_url='login')
def create_department(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    if request.method == 'POST':
        form = DepartmentForm(request.POST, request.FILES)
        if form.is_valid():
            department = form.save(commit=False)
            original_slug = slugify(department.title)
            unique_slug = original_slug
            counter = 1
            while Department.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{original_slug}-{counter}'
                counter += 1
            department.slug = unique_slug
            department.save()
            msg.success(request, "Department Created Successfully")
            return redirect('departments')  # Replace with your redirect URL
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    msg.error(request, f"Error in {field}: {error}")
    else:
        form = DepartmentForm()
    return render(request, 'backend/create-department.html', {'form': form})



@login_required(login_url='login')
def update_department(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    department = get_object_or_404(Department, slug=slug)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, request.FILES, instance=department)
        if form.is_valid():
            department = form.save(commit=False)
            original_slug = slugify(department.title)
            unique_slug = original_slug
            counter = 1
            while Department.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{original_slug}-{counter}'
                counter += 1
            department.slug = unique_slug
            department.save()
            
            msg.success(request, "Department Updated Successfully")
            return redirect('departments')  # Replace with your redirect URL
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    msg.error(request, f"Error in {field}: {error}")
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'backend/update-department.html', {'form': form, 'department': department})



@login_required(login_url='login')
def delete_department(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    try:
        department = Department.objects.get(slug=slug)
        department.delete()
        msg.success(request, 'Department deleted successfully.')
        return redirect('departments')
    except Department.DoesNotExist:
        msg.error(request, 'department not found.')
        return redirect('department')











# message view 
@login_required(login_url='login')
def messages(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    inbox = Message.objects.all().order_by('-created_at')
    inbox_count = Message.objects.all().count()
    now = datetime.datetime.now().strftime('%I:%M %p')
    context = {'inbox': inbox, 'now':now, 'inbox_count': inbox_count}
    return render(request, 'backend/messages.html', context)

@login_required(login_url='login')
def message(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    message = Message.objects.get(slug=slug)
    inbox_count = Message.objects.all().count()
    now = datetime.datetime.now().strftime('%I:%M %p')
    context = {'message':message,'now':now, 'inbox_count': inbox_count}
    return render(request, 'backend/message-view.html', context)





# career view 
@login_required(login_url='login')
def careers(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    careers = Career.objects.all()
    context ={'careers': careers}
    return render(request, 'backend/careers.html', context)


@login_required(login_url='login')
def create_career(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    if request.method == 'POST':
        form = CareerForm(request.POST)
        if form.is_valid():
            form.save()
            msg.success(request, 'Career created successfully!')
            return redirect('careers')  # Redirect to a list of careers or any other appropriate view
    else:
        form = CareerForm()
    
    return render(request, 'backend/create-career.html', {'form': form})


@login_required(login_url='login')
def update_career(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    career = Career.objects.get(slug=slug)
    if request.method == 'POST':
        form = CareerForm(request.POST, instance=career)
        if form.is_valid():
            form.save()
            msg.success(request, 'Career Updated successfully!')
            return redirect('careers')  # Redirect to a list of careers or any other appropriate view
    else:
        form = CareerForm(instance=career)
    
    return render(request, 'backend/update-career.html', {'form': form})


@login_required(login_url='login')
def delete_career(request, pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    try:
        career = Career.objects.get(id=pk)
        career.delete()
        msg.success(request, 'Career deleted successfully.')
        return redirect('careers')
    except Career.DoesNotExist:
        msg.error(request, 'Career not found.')
        return redirect('careers')
    
    

@login_required(login_url='login')
def view_career_applications(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    career = Career.objects.get(slug=slug)
    applications = CareerApplication.objects.filter(job=career)
    application_count = CareerApplication.objects.all().count()
    now = datetime.datetime.now().strftime('%I:%M %p')
    context = {'career': career, 'applications': applications, 'application_count':application_count,'now':now}
    return render(request, 'backend/career-application-view.html', context)


@login_required(login_url='login')
def view_career_application(request, careerslug, applicationslug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    career = get_object_or_404(Career, slug=careerslug)
    application = get_object_or_404(CareerApplication, slug=applicationslug)
    application_count = CareerApplication.objects.count()
    now = datetime.datetime.now().strftime('%I:%M %p')
    file_type = 'pdf' if application.cv and application.cv.name.endswith('.pdf') else 'image'

    context = {
        'career': career,
        'application': application,
        'application_count': application_count,
        'now': now,
        'file_type': file_type  # Add file type to the context

    }
    return render(request, 'backend/career-application-view-inner.html', context)




@login_required(login_url='login')
def create_leave(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    doctor = get_object_or_404(Doctor, slug=slug)
    leaves = Leave.objects.filter(doctor=doctor)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')
        
        # Convert the dates to actual date objects
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d').date()

        # Ensure the start date is today or in the future
        if start_date < timezone.now().date():
            msg.error(request, "The leave start date must be today or in the future.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # Ensure the end date is not before the start date
        if end_date < start_date:
            msg.error(request, "The end date cannot be before the start date.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

        # Create leave entries for each day in the range
        current_date = start_date
        while current_date <= end_date:
            if Leave.objects.filter(doctor=doctor, date=current_date).exists():
                msg.error(request, f"The doctor already has a leave on {current_date}. Please choose a different date.")
                return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
            Leave.objects.create(doctor=doctor, date=current_date, reason=reason)
            current_date += datetime.timedelta(days=1)

        msg.success(request, "Leave created successfully.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    return render(request, 'backend/leave-request.html', {'doctor': doctor, 'leaves': leaves})

    

@login_required(login_url='login')
def delete_leave(request, pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    leave = get_object_or_404(Leave, id=pk)
    
    # Check if the leave date is in the past
    if leave.date < timezone.now().date():
        msg.error(request, "You cannot delete this leave because this leave is already taken.")
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    
    leave.delete()
    msg.success(request, "Leave deleted successfully.")
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


# Create your views here.

def login(request):

    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            auth_login(request, user)
            msg.success(request, "Logged In")
            return redirect('dashboard')
            
        else:
            print("Error")
            msg.error(request, 'Invalid Credential')
            return render(request, 'backend/login.html')
    return render(request, 'backend/login.html')


# logout 
@login_required(login_url='login')
def logout_user(request):
    logout(request)
    return redirect('login')





@login_required(login_url='login')
def patients(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)

    # Filter patients based on the search query
    patients = Patient.objects.all()
    if search_query:
        patients = patients.filter(
            Q(name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(disease__icontains=search_query) |
            Q(gender__icontains=search_query)
        )

    # Pagination: Show 10 patients per page
    paginator = Paginator(patients, 10)
    paginated_patients = paginator.get_page(page_number)

    context = {
        'patients': paginated_patients,
        'search_query': search_query,
    }
    return render(request, 'backend/patients.html', context)










@login_required(login_url='login')
def appointments(request):
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request, 'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role == 'media':
            return redirect('media_dashboard')  # Correctly redirect to media dashboard
        elif profile.role not in ['frontdesk', 'admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    search_upcoming = request.GET.get('search_upcoming', '')
    search_completed = request.GET.get('search_completed', '')
    search_cancelled = request.GET.get('search_cancelled', '')
    now = timezone.now()
    active_tab = request.GET.get('tab', 'upcoming')

    # Get all appointments
    completed_appointments = Appointment.objects.filter(status="COMPLETED").order_by('date')
    cancelled_appointments = Appointment.objects.filter(status="CANCELLED").order_by('date')

    past_appointments = []
    upcoming_appointments_list = []
    cancelled_appointments_list = []



    # Process completed appointments
    for appointment in completed_appointments:
        payment_details = RazorpayPaymentDetails.objects.filter(status='COMPLETED', appointment=appointment).first()
        content_type = appointment.content_type
        
        try:
            related_object = content_type.get_object_for_this_type(id=appointment.object_id)
        except ObjectDoesNotExist:
            related_object = 'Timing deleted'  # Set to 'Timing deleted' if object doesn't exist
        
        # Determine the appointment_datetime
        if isinstance(related_object, AvailableTime):
            appointment_datetime = timezone.datetime.combine(appointment.date, related_object.start_time)
        elif isinstance(related_object, str) and related_object == 'Timing deleted':
            # Handle the 'Timing deleted' case by assigning a default datetime for comparison
            appointment_datetime = timezone.datetime.combine(appointment.date, timezone.datetime.min.time())
        else:
            appointment_datetime = timezone.datetime.combine(related_object.date, related_object.start_time)

        appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())

        detailed_appointment = {
            'appointment': appointment,
            'payment_details': payment_details,
            'related_object': related_object
        }

        if appointment_datetime < now:
            past_appointments.append(detailed_appointment)
        else:
            upcoming_appointments_list.append(detailed_appointment)

    # Process cancelled appointments
    for appointment in cancelled_appointments:
        payment_details = RazorpayPaymentDetails.objects.filter(status = 'COMPLETED',appointment=appointment).first()
        content_type = appointment.content_type
        related_object = content_type.get_object_for_this_type(id=appointment.object_id)

        detailed_appointment = {
            'appointment': appointment,
            'payment_details': payment_details,
            'related_object': related_object
        }
        cancelled_appointments_list.append(detailed_appointment)

    # Apply search filters
    past_appointments = [appt for appt in past_appointments if search_completed.lower() in (appt['appointment'].patient.name.lower() or appt['appointment'].patient.phone_number or appt['appointment'].patient.email or appt['appointment'].selected_doctor.name.lower())]
    upcoming_appointments_list = [appt for appt in upcoming_appointments_list if search_upcoming.lower() in (appt['appointment'].patient.name.lower() or appt['appointment'].patient.phone_number or appt['appointment'].patient.email or appt['appointment'].selected_doctor.name.lower())]
    cancelled_appointments_list = [appt for appt in cancelled_appointments_list if search_cancelled.lower() in (appt['appointment'].patient.name.lower() or appt['appointment'].patient.phone_number or appt['appointment'].patient.email or appt['appointment'].selected_doctor.name.lower())]

    # Pagination for past appointments
    paginator_past = Paginator(past_appointments, 25)
    page_number_past = request.GET.get('page_past')
    page_past_obj = paginator_past.get_page(page_number_past)

    # Pagination for upcoming appointments
    paginator_upcoming = Paginator(upcoming_appointments_list, 25)
    page_number_upcoming = request.GET.get('page_upcoming')
    page_upcoming_obj = paginator_upcoming.get_page(page_number_upcoming)

    # Pagination for cancelled appointments
    paginator_cancelled = Paginator(cancelled_appointments_list, 25)
    page_number_cancelled = request.GET.get('page_cancelled')
    page_cancelled_obj = paginator_cancelled.get_page(page_number_cancelled)

    context = {
        'past_appointments': page_past_obj,
        'upcoming_appointments': page_upcoming_obj,
        'cancelled_appointments': page_cancelled_obj,
        'search_upcoming': search_upcoming,
        'search_completed': search_completed,
        'search_cancelled': search_cancelled,
        'active_tab': active_tab
    }
    return render(request, 'backend/appointments.html', context)







@login_required(login_url='login')
def patient_appointments(request, patient_id):
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role == 'media':
            return redirect('media_dashboard')
        elif profile.role not in ['frontdesk', 'admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')

    patient = get_object_or_404(Patient, id=patient_id)
    search_query = request.GET.get('search', '')
    active_tab = request.GET.get('tab', 'upcoming')  # Default to upcoming tab
    now = timezone.now()

    # Get all appointments for the patient
    completed_appointments = Appointment.objects.filter(patient=patient, status='COMPLETED').order_by('date')
    cancelled_appointments = Appointment.objects.filter(patient=patient, status='CANCELLED').order_by('date')

    # Apply search filter
    if search_query:
        completed_appointments = completed_appointments.filter(
            Q(patient__name__icontains=search_query) |
            Q(patient__email__icontains=search_query) |
            Q(patient__phone_number__icontains=search_query) |
            Q(selected_doctor__name__icontains=search_query)
        )
        cancelled_appointments = cancelled_appointments.filter(
            Q(patient__name__icontains=search_query) |
            Q(patient__email__icontains=search_query) |
            Q(patient__phone_number__icontains=search_query) |
            Q(selected_doctor__name__icontains=search_query)
        )

    past_appointments = []
    upcoming_appointments = []
    cancelled_appointments_list = []

    for appointment in completed_appointments:
        content_type = appointment.content_type
        related_object = content_type.get_object_for_this_type(id=appointment.object_id)

        if isinstance(related_object, AvailableTime):
            appointment_datetime = timezone.datetime.combine(appointment.date, related_object.start_time)
        else:
            appointment_datetime = timezone.datetime.combine(related_object.date, related_object.start_time)

        appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())

        payment_details = RazorpayPaymentDetails.objects.filter(status = 'COMPLETED',appointment=appointment).first()
        
        detailed_appointment = {
            'appointment': appointment,
            'related_object': related_object,
            'payment_details': payment_details
        }

        if appointment_datetime < now:
            past_appointments.append(detailed_appointment)
        else:
            upcoming_appointments.append(detailed_appointment)

    # Process cancelled appointments
    for appointment in cancelled_appointments:
        content_type = appointment.content_type
        related_object = content_type.get_object_for_this_type(id=appointment.object_id)

        payment_details = RazorpayPaymentDetails.objects.filter(status = 'COMPLETED',appointment=appointment).first()

        detailed_appointment = {
            'appointment': appointment,
            'related_object': related_object,
            'payment_details': payment_details
        }

        cancelled_appointments_list.append(detailed_appointment)

    # Paginate results
    paginator_past = Paginator(past_appointments, 10)
    paginator_upcoming = Paginator(upcoming_appointments, 10)
    paginator_cancelled = Paginator(cancelled_appointments_list, 10)

    page_number_past = request.GET.get('page_past')
    page_number_upcoming = request.GET.get('page_upcoming')
    page_number_cancelled = request.GET.get('page_cancelled')

    past_appointments_paginated = paginator_past.get_page(page_number_past)
    upcoming_appointments_paginated = paginator_upcoming.get_page(page_number_upcoming)
    cancelled_appointments_paginated = paginator_cancelled.get_page(page_number_cancelled)

    context = {
        'patient': patient,
        'past_appointments': past_appointments_paginated,
        'upcoming_appointments': upcoming_appointments_paginated,
        'cancelled_appointments': cancelled_appointments_paginated,
        'search_query': search_query,
        'active_tab': active_tab,  # Pass the active tab to the template
    }
    return render(request, 'backend/patient-appointments.html', context)








@login_required(login_url='login')
def doctor_appointments(request, doctor_id):
    # Check if the user has a profile
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request, 'Profile does not exist. You cannot access here.')
        return redirect('login')

    # Check user role and redirect accordingly
    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role == 'media':
            return redirect('media_dashboard')
        elif profile.role not in ['frontdesk', 'admin']:
            return redirect('homepage')
    else:
        return redirect('homepage')

    # Fetch the doctor
    doctor = get_object_or_404(Doctor, id=doctor_id)
    search_query = request.GET.get('search', '')
    active_tab = request.GET.get('tab', 'upcoming')  # Default to upcoming tab
    now = timezone.now()

    # Filter appointments for the doctor based on status
    completed_appointments = Appointment.objects.filter(selected_doctor=doctor, status='COMPLETED').order_by('date')
    cancelled_appointments = Appointment.objects.filter(selected_doctor=doctor, status='CANCELLED').order_by('date')

    # Apply search query if provided
    if search_query:
        completed_appointments = completed_appointments.filter(
            Q(patient__name__icontains=search_query) |
            Q(patient__email__icontains=search_query) |
            Q(patient__phone_number__icontains=search_query) |
            Q(selected_doctor__name__icontains=search_query)
        )
        cancelled_appointments = cancelled_appointments.filter(
            Q(patient__name__icontains=search_query) |
            Q(patient__email__icontains=search_query) |
            Q(patient__phone_number__icontains=search_query) |
            Q(selected_doctor__name__icontains=search_query)
        )

    past_appointments = []
    upcoming_appointments = []
    cancelled_appointments_list = []

    # Process completed appointments
    for appointment in completed_appointments:
        content_type = appointment.content_type

        try:
            related_object = content_type.get_object_for_this_type(id=appointment.object_id)
        except ObjectDoesNotExist:
            related_object = 'Timing deleted'  # Handle missing object case

        # Determine the appointment datetime and timing details
        if isinstance(related_object, AvailableTime):
            appointment_datetime = timezone.datetime.combine(appointment.date, related_object.start_time)
            timing_details = f"{related_object.start_time.strftime('%I:%M %p')} to {related_object.end_time.strftime('%I:%M %p')}"
        elif isinstance(related_object, str) and related_object == 'Timing deleted':
            appointment_datetime = timezone.datetime.combine(appointment.date, timezone.datetime.min.time())
            timing_details = "Timing deleted"
        else:
            appointment_datetime = timezone.datetime.combine(related_object.date, related_object.start_time)
            timing_details = f"{related_object.start_time.strftime('%I:%M %p')} to {related_object.end_time.strftime('%I:%M %p')}"

        # Make appointment_datetime timezone-aware
        appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())

        payment_details = RazorpayPaymentDetails.objects.filter(status='COMPLETED', appointment=appointment).first()

        detailed_appointment = {
            'appointment': appointment,
            'related_object': related_object,
            'payment_details': payment_details,
            'timing_details': timing_details
        }

        if appointment_datetime < now:
            past_appointments.append(detailed_appointment)
        else:
            upcoming_appointments.append(detailed_appointment)

    # Process cancelled appointments
    for appointment in cancelled_appointments:
        content_type = appointment.content_type
        
        try:
            related_object = content_type.get_object_for_this_type(id=appointment.object_id)
        except ObjectDoesNotExist:
            related_object = 'Timing deleted'  # Handle missing object case

        # Determine timing details
        if isinstance(related_object, AvailableTime):
            timing_details = f"{related_object.start_time.strftime('%I:%M %p')} to {related_object.end_time.strftime('%I:%M %p')}"
        elif isinstance(related_object, str) and related_object == 'Timing deleted':
            timing_details = "Timing deleted"
        else:
            timing_details = f"{related_object.start_time.strftime('%I:%M %p')} to {related_object.end_time.strftime('%I:%M %p')}"

        payment_details = RazorpayPaymentDetails.objects.filter(status='COMPLETED', appointment=appointment).first()

        detailed_appointment = {
            'appointment': appointment,
            'related_object': related_object,
            'payment_details': payment_details,
            'timing_details': timing_details
        }

        cancelled_appointments_list.append(detailed_appointment)

    # Pagination setup
    paginator_past = Paginator(past_appointments, 10)  # Show 10 past appointments per page
    paginator_upcoming = Paginator(upcoming_appointments, 10)  # Show 10 upcoming appointments per page
    paginator_cancelled = Paginator(cancelled_appointments_list, 10)  # Show 10 cancelled appointments per page

    page_number_past = request.GET.get('page_past')
    page_number_upcoming = request.GET.get('page_upcoming')
    page_number_cancelled = request.GET.get('page_cancelled')

    past_appointments_paginated = paginator_past.get_page(page_number_past)
    upcoming_appointments_paginated = paginator_upcoming.get_page(page_number_upcoming)
    cancelled_appointments_paginated = paginator_cancelled.get_page(page_number_cancelled)

    context = {
        'doctor': doctor,
        'past_appointments': past_appointments_paginated,
        'upcoming_appointments': upcoming_appointments_paginated,
        'cancelled_appointments': cancelled_appointments_paginated,
        'search_query': search_query,
        'active_tab': active_tab,
    }
    return render(request, 'backend/doctor-appointment.html', context)




@login_required(login_url='login')
def create_patient(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            msg.success(request, 'Patient created successfully.')
            return redirect('patients')  # Redirect to the patient list view or any other view
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            msg.error(request, ' '.join(error_messages))
    else:
        form = PatientForm()
    
    return render(request, 'backend/create-patient.html', {'form': form})



@login_required(login_url='login')
def update_patient(request, pk):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    patient = Patient.objects.get(id=pk)
    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            form.save()
            msg.success(request, 'Patient upated successfully.')
            return redirect('patients')  # Redirect to the patient list view or any other view
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            msg.error(request, ' '.join(error_messages))
    else:
        form = PatientForm(instance=patient)
    
    return render(request, 'backend/update-patient.html', {'form': form})











logger = logging.getLogger(__name__)

@api_view(['GET'])
def check_available_timings(request, doctor_id, date):
    logger.info(f"Checking available timings for doctor {doctor_id} on date {date}")
    
    try:
        # Parse the date
        try:
            date_obj = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        except ValueError:
            logger.error(f"Invalid date format: {date}")
            return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=400)

        # Get the doctor
        doctor = get_object_or_404(Doctor, id=doctor_id)
        logger.info(f"Doctor found: {doctor}")

        # Check for monthly timings with remaining slots
        monthly_timings = MonthlyTiming.objects.filter(doctor=doctor, status='active', date=date_obj, remaining_slots__gte=1).order_by('start_time')
        monthly_serializer = MonthlyTimingSerializer(monthly_timings, many=True)

        # Check for available times based on the day of the week
        day_of_week = date_obj.strftime('%A').lower()
        available_times = AvailableTime.objects.filter(doctor=doctor, status='active', day=day_of_week)
        
        # Filter available times based on remaining slots
        valid_available_times = []
        for available_time in available_times:
            appointments_on_same_day = Appointment.objects.filter(
                date=date_obj,
                selected_doctor=doctor,
                status='COMPLETED',
                content_type=ContentType.objects.get_for_model(AvailableTime),
                object_id=available_time.id
            ).count()
            remaining_slots = available_time.slot - appointments_on_same_day
            if remaining_slots >= 1:
                valid_available_times.append(available_time)
        
        # Sort the valid available times by start time before serialization
        valid_available_times.sort(key=lambda x: x.start_time)
        available_times_serializer = AvailableTimeSerializer(valid_available_times, many=True)

        # Combine both sets of timings
        combined_timings = {
            'monthly_timings': monthly_serializer.data,
            'weekly_timings': available_times_serializer.data
        }

        logger.info(f"Timings found: {combined_timings}")
        return Response({'timings': combined_timings}, status=200)

    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
        return Response({'error': 'An internal server error occurred.'}, status=500)


@login_required(login_url='login')
def create_appointment_backend(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    doctors = Doctor.objects.all().order_by('priority')
    departments = Department.objects.all().order_by('priority')
    available_times = AvailableTime.objects.all()
    monthly_timings = MonthlyTiming.objects.all()
    return render(request, 'backend/create-appointment.html', {
        'doctors': doctors,
        'departments': departments,
        'available_times': available_times,
        'monthly_timings': monthly_timings
    })


@login_required(login_url='login')
def patient_appointments_create(request, patient_id):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    departments = Department.objects.all().order_by('priority')
    patient = Patient.objects.get(id=patient_id)
    return render(request, 'backend/create-appointment-patient.html', {
        'patient': patient,
        'departments': departments
    })


@login_required(login_url='login')
def create_appointement_page(request):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role not in ['admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    doctors = Doctor.objects.all().order_by('priority')
    departments = Department.objects.all().order_by('priority')
    available_times = AvailableTime.objects.all()
    monthly_timings = MonthlyTiming.objects.all()
    return render(request, 'frontend/create-appointement.html', {
        'doctors': doctors,
        'departments': departments,
        'available_times': available_times,
        'monthly_timings': monthly_timings
    })



@login_required(login_url='login')
def cancel_appointment(request, pk):
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        msg.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if profile:
        if profile.role == 'hr':
            return redirect('hr_dashboard')
        elif profile.role == 'media':
            return redirect('media_dashboard')  # Correctly redirect to media dashboard
        elif profile.role not in ['frontdesk', 'admin']:
            return redirect('homepage')
    else: 
        return redirect('homepage')
    
    
    try:
        appointment = Appointment.objects.get(id=pk)
        appointment.status = 'CANCELLED'
        appointment.save()
        msg.success(request, "Appointment Cancelled")
    except Appointment.DoesNotExist:
        msg.error(request, "Appointment does not exist.")

    # Redirect back to the same page
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    





class DoctorsByDepartmentAPIView(APIView):
    def get(self, request, *args, **kwargs):
        department_id = request.query_params.get('department_id')
        
        if not department_id:
            return Response({"error": "department_id query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        department = get_object_or_404(Department, id=department_id)
        doctors = Doctor.objects.filter(department=department, status='active').order_by('priority')
        
        serializer = DoctorSerializer(doctors, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)





class PaymentListView(FilterView):
    model = RazorpayPaymentDetails
    template_name = 'backend/payments.html'
    context_object_name = 'payments'
    filterset_class = RazorpayPaymentDetailsFilter

    # Override the get_queryset method to apply ordering and filter by status 'COMPLETED'
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(status='COMPLETED').order_by('-created_at')  # Filter by 'COMPLETED' and order by created_at descending

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = context['payments']

        formatted_payments = []
        total_amount = 0

        # Utility function to format time
        def format_time(time):
            if time:
                formatted_time = time.strftime('%I:%M %p')
                return formatted_time.lstrip("0")  # Remove leading zero
            return None

        # Process each payment
        for payment in payments:
            total_amount += payment.amount / 100  # Convert paise to rupees

            # Handle appointments
            if payment.appointment:
                appointment = payment.appointment
                content_type = appointment.content_type
                related_object = None

                # Safely retrieve the related object
                try:
                    model_class = content_type.model_class()
                    related_object = model_class.objects.get(id=appointment.object_id)
                    appointment.schedule = related_object
                except ObjectDoesNotExist:
                    related_object = 'Timing deleted'

                # Handle both cases with valid or missing related object
                formatted_payment = {
                    'patient_name': appointment.patient.name,
                    'order_id': payment.order_id,
                    'disease': appointment.patient.disease,
                    'appointment_date': appointment.date,
                    'appointment_start_time': format_time(appointment.schedule.start_time) if related_object != 'Timing deleted' and hasattr(appointment.schedule, 'start_time') else None,
                    'appointment_end_time': format_time(appointment.schedule.end_time) if related_object != 'Timing deleted' and hasattr(appointment.schedule, 'end_time') else None,
                    'doctor_name': appointment.selected_doctor.name,
                    'doctor_photo_url': appointment.selected_doctor.photo.url if appointment.selected_doctor.photo else None,
                    'paid_date': payment.created_at.strftime('%B %d %Y'),
                    'paid_amount': payment.amount / 100,
                    'payment_method': payment.payment_method,
                    'type': 'Appointment'
                }
                formatted_payments.append(formatted_payment)

            # Handle health checkup bookings
            elif payment.booking:
                booking = payment.booking
                plan = booking.plan

                formatted_payment = {
                    'patient_name': booking.patient.name,
                    'order_id': payment.order_id,
                    'disease': 'Health Checkup',
                    'appointment_date': booking.created_at.strftime('%B %d %Y'),
                    'appointment_start_time': None,
                    'appointment_end_time': None,
                    'doctor_name': plan.title,
                    'plan_title': plan.title,
                    'doctor_photo_url': None,
                    'paid_date': payment.created_at.strftime('%B %d %Y'),
                    'paid_amount': payment.amount / 100,
                    'payment_method': payment.payment_method,
                    'type': 'Health Checkup'
                }
                formatted_payments.append(formatted_payment)

            # Handle special offers
            elif payment.offer:
                booking = payment.offer
                plan = booking.plan

                formatted_payment = {
                    'patient_name': booking.patient.name,
                    'order_id': payment.order_id,
                    'disease': 'Health Checkup (World Heart Day)',
                    'appointment_date': booking.created_at.strftime('%B %d %Y'),
                    'appointment_start_time': None,
                    'appointment_end_time': None,
                    'doctor_name': booking.plan.title,
                    'plan_title': booking.plan.title,
                    'doctor_photo_url': None,
                    'paid_date': payment.created_at.strftime('%B %d %Y'),
                    'paid_amount': payment.amount / 100,
                    'payment_method': booking.payment_method,
                    'type': 'Health Checkup (World Heart Day)'
                }
                formatted_payments.append(formatted_payment)

        # Apply pagination
        paginator = Paginator(formatted_payments, 25)  # Show 10 payments per page
        page_number = self.request.GET.get('page')
        paginated_payments = paginator.get_page(page_number)

        # Pass data to context
        context['formatted_payments'] = paginated_payments
        context['total_amount'] = total_amount
        return context




        
class CreateAppointmentPatientAPIView(APIView):
    def post(self, request, *args, **kwargs):
        patient_id = request.data.get('patient_id')
        date = request.data.get('date')
        message = request.data.get('message') or ''
        department_id = request.data.get('department')
        doctor_id = request.data.get('selected_doctor')
        payment_method = request.data.get('payment_method', 'online')  # Default to 'online' if not provided
        schedule_id = request.data.get('schedule_id')
        registration_fee_include = request.data.get('registration_fee')
        discount_percentage = float(request.data.get('discount', 0))

        registration_fee = 'paid'
        if registration_fee_include == 'on':
            registration_fee = 'unpaid'

        # Debug statements
        print(f"Patient ID: {patient_id}, Date: {date}, Message: {message}, Department: {department_id}")
        print(f"Doctor: {doctor_id}, Payment Method: {payment_method}, Schedule ID: {schedule_id}")

        # Check if all required fields are present
        if not all([patient_id, date, department_id, doctor_id, schedule_id]):
            return Response({"error": "Missing one or more required fields."}, status=status.HTTP_400_BAD_REQUEST)

        doctor = get_object_or_404(Doctor, id=doctor_id)
        leave_exists = Leave.objects.filter(doctor=doctor, date=date).exists()
        if leave_exists:
            return Response({"error": "The selected doctor is on leave on the specified date."}, status=status.HTTP_400_BAD_REQUEST)

        # Get patient
        patient = get_object_or_404(Patient, id=patient_id)

        # Get department and doctor
        department = get_object_or_404(Department, id=department_id)
        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Determine if the schedule is monthly or weekly
        try:
            monthly_timing = MonthlyTiming.objects.get(uuid=schedule_id)
            content_type = ContentType.objects.get_for_model(MonthlyTiming)
            object_id = monthly_timing.id
            start_time = monthly_timing.start_time
        except MonthlyTiming.DoesNotExist:
            available_time = get_object_or_404(AvailableTime, uuid=schedule_id)
            content_type = ContentType.objects.get_for_model(AvailableTime)
            object_id = available_time.id
            start_time = available_time.start_time

        # Combine date and start_time to form a datetime
        appointment_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        appointment_datetime = timezone.datetime.combine(appointment_date, start_time)
        appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())

        if appointment_datetime <= timezone.now():
            return Response({"error": "The appointment datetime must be in the future."}, status=status.HTTP_400_BAD_REQUEST)

        # Create appointment
        appointment = Appointment.objects.create(
            date=date,
            message=message,
            payment_id='',  # This will be filled after Razorpay payment if online
            payment_method=payment_method,
            patient=patient,
            department=department,
            selected_doctor=doctor,
            content_type=content_type,
            object_id=object_id,
            status='PENDING' if payment_method == 'online' else 'COMPLETED',
            discount=discount_percentage  # Store the discount percentage in the appointment
        )

        amount = int(doctor.fee) * 100  # amount in paise
        if registration_fee != 'paid':
            amount += 27000  # add registration fee in paise

        discount_amount = (amount * discount_percentage) / 100
        amount -= int(discount_amount)

        if payment_method == 'cash':
            
            if not request.user.is_superuser:
                Notification.objects.create(
                    message=f"{appointment.patient.name} booked an appointment with {appointment.selected_doctor.name} for ₹ {amount / 100}",
                    read_status=False,
                    redirection_url=reverse('view_appointment', args=[appointment.id]),
                    object_id=appointment.id,
                    type='appointment'
                )

            msg.success(request, 'Appointment created successfully with cash payment.')

        if payment_method == 'online':





            
            print("Coming Here -------------------------------------- Yes")
            merchant_transaction_id = str(uuid.uuid4())  # Generates a unique UUID string
            request.session['merchantTransactionId'] = merchant_transaction_id  # Store in session for later use
            request.session['appointmentId'] = appointment.id  # Store in session for later use
            print("Appointment ID", appointment.id)
            
            payload = {
                "merchantId": merchant_id_phonephe,  # Ensure this is the correct sandbox merchant ID
                "merchantTransactionId": merchant_transaction_id,
                "merchantUserId": "MUID123",
                "amount": amount,
                "redirectUrl": "https://ngrhealthcare.com/handle-payment/",
                "redirectMode": "REDIRECT",
                "callbackUrl": "https://ngrhealthcare.com/handle-payment/",
                "mobileNumber": patient.phone_number,
                "paymentInstrument": {"type": "PAY_PAGE"}
            }

            # Encode payload to Base64
            payload_str = json.dumps(payload)
            base64_payload = base64.b64encode(payload_str.encode()).decode()

            # Compute the checksum
            salt_key = salt_key_phonephe  # M ake sure this is the correct sandbox salt key
            salt_index = "1"  # Ensure this matches PhonePe's sandbox configuration
            checksum_str = f"{base64_payload}/pg/v1/pay{salt_key}"
            checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + "###" + salt_index

            # Headers
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json",
                "X-VERIFY": checksum
            }

            # Send the request
            response = requests.post(payment_url_phonephe, json={"request": base64_payload}, headers=headers)
            
            try:
                response_data = response.json()
                print(response_data)
                if response_data.get("success"):
                    print("Coming Here inside response")
                    # Update appointment with Razorpay order ID
                    appointment.payment_id = merchant_transaction_id
                    appointment.save()
                    payment_url = response_data["data"]["instrumentResponse"]["redirectInfo"]["url"]
                    print("URL", payment_url)

                    # Save Razorpay payment details
                    RazorpayPaymentDetails.objects.create(
                        payment_id=merchant_transaction_id,
                        order_id=merchant_transaction_id,
                        signature='',  # This will be filled after payment verification
                        amount=amount,
                        currency='INR',
                        payment_method=payment_method,
                        status='PENDING',  # Initial status
                        appointment=appointment
                    )
                    return JsonResponse({'url':payment_url}) 
                else:
                    return JsonResponse({"error": "Failed to initiate payment", "details": response_data})
            except ValueError:
                return JsonResponse({"error": "Non-JSON response", "details": response.text})









        else:
            # Create RazorpayPaymentDetails with custom ID for cash payments
            RazorpayPaymentDetails.objects.create(
                payment_id=str(uuid.uuid4()),  # Generate a custom UUID
                order_id='',
                signature='',
                amount=amount,
                currency='INR',
                payment_method='cash',
                status='COMPLETED',  # Directly mark as completed for cash payments
                appointment=appointment
            )

        # Return response for non-online payment method
        return Response({
            'appointment_id': appointment.id,
            'name': patient.name,
            'email': patient.email,
            'phone_number': patient.phone_number,
            'description': 'Appointment Booking'
        }, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        doctors = Doctor.objects.all().order_by('priority')
        departments = Department.objects.all().order_by('priority')
        available_times = AvailableTime.objects.all()
        monthly_timings = MonthlyTiming.objects.all()

        data = {
            'doctors': [{'id': doctor.id, 'name': doctor.name, 'fee': doctor.fee} for doctor in doctors],
            'departments': [{'id': department.id, 'title': department.title} for department in departments],
            'available_times': [{'uuid': time.uuid, 'start_time': time.start_time, 'end_time': time.end_time} for time in available_times],
            'monthly_timings': [{'uuid': timing.uuid, 'start_time': timing.start_time, 'end_time': timing.end_time} for timing in monthly_timings],
        }
        return Response(data, status=status.HTTP_200_OK)



class CreateAppointmentAPIView(APIView):
    def post(self, request, *args, **kwargs):
        name = request.data.get('name')
        email = request.data.get('email')
        phone_number = request.data.get('phone_number')
        disease = request.data.get('disease') or ''
        date = request.data.get('date')
        message = request.data.get('message') or ''
        department_id = request.data.get('department')
        doctor_id = request.data.get('selected_doctor')
        payment_method = request.data.get('payment_method', 'online')  # Default to 'online' if not provided
        schedule_id = request.data.get('schedule_id')
        gender = request.data.get('gender')
        registration_fee_include = request.data.get('registration_fee')
        discount_percentage = float(request.data.get('discount', 0))  # Get discount percentage

        registration_fee = 'paid'

        if registration_fee_include == 'on':
            registration_fee = 'unpaid'

        # Debug statements
        print(f"Name: {name}, Email: {email}, Phone: {phone_number}, Disease: {disease}, Gender: {gender}")
        print(f"Date: {date}, Message: {message}, Department: {department_id}")
        print(f"Doctor: {doctor_id}, Payment Method: {payment_method}, Schedule ID: {schedule_id}")
        print(f"Discount: {discount_percentage}%")

        # Check if all required fields are present
        if not all([name, email, phone_number, date, department_id, doctor_id, schedule_id, gender]):
            return Response({"error": "Missing one or more required fields."}, status=status.HTTP_400_BAD_REQUEST)

        doctor = get_object_or_404(Doctor, id=doctor_id)
        leave_exists = Leave.objects.filter(doctor=doctor, date=date).exists()
        if leave_exists:
            return Response({"error": "The selected doctor is on leave on the specified date."}, status=status.HTTP_400_BAD_REQUEST)

        # Create or get patient
        patient, created = Patient.objects.get_or_create(
            email=email,
            defaults={'name': name, 'phone_number': phone_number, 'disease': disease, 'gender': gender}
        )

        # Get department and doctor
        department = get_object_or_404(Department, id=department_id)
        doctor = get_object_or_404(Doctor, id=doctor_id)

        # Determine if the schedule is monthly or weekly
        try:
            monthly_timing = MonthlyTiming.objects.get(uuid=schedule_id)
            content_type = ContentType.objects.get_for_model(MonthlyTiming)
            object_id = monthly_timing.id
            start_time = monthly_timing.start_time
        except MonthlyTiming.DoesNotExist:
            available_time = get_object_or_404(AvailableTime, uuid=schedule_id)
            content_type = ContentType.objects.get_for_model(AvailableTime)
            object_id = available_time.id
            start_time = available_time.start_time

        # Combine date and start_time to form a datetime
        appointment_date = timezone.datetime.strptime(date, '%Y-%m-%d').date()
        appointment_datetime = timezone.datetime.combine(appointment_date, start_time)
        appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())

        if appointment_datetime <= timezone.now():
            return Response({"error": "The appointment datetime must be in the future."}, status=status.HTTP_400_BAD_REQUEST)

        # Create appointment
        appointment = Appointment.objects.create(
            date=date,
            message=message,
            payment_id='',  # This will be filled after Razorpay payment if online
            payment_method=payment_method,
            patient=patient,
            department=department,
            selected_doctor=doctor,
            content_type=content_type,
            object_id=object_id,
            status='PENDING' if payment_method == 'online' else 'COMPLETED',
            discount=discount_percentage  # Save discount percentage
        )

        amount = int(doctor.fee) * 100  # amount in paise
        if registration_fee != 'paid':
            amount += 27000  # add registration fee in paise

        # Apply discount
        if discount_percentage > 0:
            discount_amount = (amount * discount_percentage) / 100
            amount -= int(discount_amount)

        if payment_method == 'cash':
            if not request.user.is_superuser:
                Notification.objects.create(
                    message=f"{appointment.patient.name} booked an appointment with {appointment.selected_doctor.name} for ₹ {amount / 100}",
                    read_status=False,
                    redirection_url=reverse('view_appointment', args=[appointment.id]),
                    object_id=appointment.id,
                    type='appointment'
                )


                msg.success(request, 'Appointment created successfully with cash payment.')


        if payment_method == 'online':
            print("Coming Here -------------------------------------- Yes")
            merchant_transaction_id = str(uuid.uuid4())  # Generates a unique UUID string
            request.session['merchantTransactionId'] = merchant_transaction_id  # Store in session for later use
            request.session['appointmentId'] = appointment.id  # Store in session for later use
            print("Appointment ID", appointment.id)
            
            payload = {
                "merchantId": merchant_id_phonephe,  # Ensure this is the correct sandbox merchant ID
                "merchantTransactionId": merchant_transaction_id,
                "merchantUserId": "MUID123",
                "amount": amount,
                "redirectUrl": "https://ngrhealthcare.com/handle-payment/",
                "redirectMode": "REDIRECT",
                "callbackUrl": "https://ngrhealthcare.com/handle-payment/",
                "mobileNumber": phone_number,
                "paymentInstrument": {"type": "PAY_PAGE"}
            }

            # Encode payload to Base64
            payload_str = json.dumps(payload)
            base64_payload = base64.b64encode(payload_str.encode()).decode()

            # Compute the checksum
            salt_key = salt_key_phonephe  # M ake sure this is the correct sandbox salt key
            salt_index = "1"  # Ensure this matches PhonePe's sandbox configuration
            checksum_str = f"{base64_payload}/pg/v1/pay{salt_key}"
            checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + "###" + salt_index

            # Headers
            headers = {
                "accept": "application/json",
                "Content-Type": "application/json",
                "X-VERIFY": checksum
            }

            # Send the request
            response = requests.post(payment_url_phonephe, json={"request": base64_payload}, headers=headers)
            
            try:
                response_data = response.json()
                print(response_data)
                if response_data.get("success"):
                    print("Coming Here inside response")
                    # Update appointment with Razorpay order ID
                    appointment.payment_id = merchant_transaction_id
                    appointment.save()
                    payment_url = response_data["data"]["instrumentResponse"]["redirectInfo"]["url"]
                    print("URL", payment_url)

                    # Save Razorpay payment details
                    RazorpayPaymentDetails.objects.create(
                        payment_id=merchant_transaction_id,
                        order_id=merchant_transaction_id,
                        signature='',  # This will be filled after payment verification
                        amount=amount,
                        currency='INR',
                        payment_method=payment_method,
                        status='PENDING',  # Initial status
                        appointment=appointment
                    )
                    return JsonResponse({'url':payment_url}) 
                else:
                    return JsonResponse({"error": "Failed to initiate payment", "details": response_data})
            except ValueError:
                return JsonResponse({"error": "Non-JSON response", "details": response.text})




        else:
            # Create RazorpayPaymentDetails with custom ID for cash payments
            RazorpayPaymentDetails.objects.create(
                payment_id=str(uuid.uuid4()),  # Generate a custom UUID
                order_id='',
                signature='',
                amount=amount,
                currency='INR',
                payment_method='cash',
                status='COMPLETED',  # Directly mark as completed for cash payments
                appointment=appointment
            )

        # Return response for non-online payment method
        return Response({
            'appointment_id': appointment.id,
            'name': name,
            'email': email,
            'phone_number': phone_number,
            'description': 'Appointment Booking'
        }, status=status.HTTP_201_CREATED)

    def get(self, request, *args, **kwargs):
        doctors = Doctor.objects.all()
        departments = Department.objects.all().order_by('priority')
        available_times = AvailableTime.objects.all()
        monthly_timings = MonthlyTiming.objects.all()

        data = {
            'doctors': [{'id': doctor.id, 'name': doctor.name} for doctor in doctors],
            'departments': [{'id': department.id, 'title': department.title} for department in departments],
            'available_times': [{'uuid': time.uuid, 'start_time': time.start_time, 'end_time': time.end_time} for time in available_times],
            'monthly_timings': [{'uuid': timing.uuid, 'start_time': timing.start_time, 'end_time': timing.end_time} for timing in monthly_timings],
        }
        return Response(data, status=status.HTTP_200_OK)





@csrf_exempt
def handle_payment(request):
    print("Hellog World")


    


class HandlePaymentAPIView(APIView):
    def post(self, request, *args, **kwargs):
        payment_id = request.data.get('payment_id')
        appointment_id = request.data.get('appointment_id')
        razorpay_signature = request.data.get('razorpay_signature')

        # Verify the payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            'razorpay_order_id': appointment_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
            appointment = get_object_or_404(Appointment, id=appointment_id)
            appointment.status = 'COMPLETED'
            appointment.save()
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except razorpay.errors.SignatureVerificationError:
            return redirect('payment_failure_account')


@method_decorator(login_required, name='dispatch')
class UnreadNotificationsView(APIView):
    def get(self, request):
        notifications = Notification.objects.filter(read_status=False).order_by('-created_at')
        notifications_data = [
            {
                'id': notification.id,
                'message': notification.message,
                'created_at': naturaltime(notification.created_at),
                'redirection_url': notification.redirection_url
            }
            for notification in notifications
        ]
        return Response(notifications_data, status=status.HTTP_200_OK)



@method_decorator(login_required, name='dispatch')
class MarkNotificationAsReadView(APIView):
    def post(self, request, notification_id):
        notification = get_object_or_404(Notification, id=notification_id)
        notification.read_status = True
        notification.first_read_by = request.user
        notification.save()
        return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)


@method_decorator(login_required, name='dispatch')
class MarkAllNotificationsAsReadView(APIView):
    def post(self, request):
        Notification.objects.filter(read_status=False).update(read_status=True, first_read_by=request.user)
        return Response({'message': 'All notifications marked as read.'}, status=status.HTTP_200_OK)




def view_appointment(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)

    # Get the related object (AvailableTime or MonthlyTiming)
    content_type = appointment.content_type
    related_object = content_type.get_object_for_this_type(id=appointment.object_id)

    # Determine if the appointment is past or upcoming
    if isinstance(related_object, AvailableTime):
        # Combine appointment date with the start time from AvailableTime
        appointment_datetime = timezone.datetime.combine(appointment.date, related_object.start_time)
        timing_details = f"{related_object.start_time.strftime('%I:%M %p')} to {related_object.end_time.strftime('%I:%M %p')}"
    else:
        # Combine the date and start time from MonthlyTiming
        appointment_datetime = timezone.datetime.combine(related_object.date, related_object.start_time)
        timing_details = f"{related_object.start_time.strftime('%I:%M %p')} to {related_object.end_time.strftime('%I:%M %p')}"

    # Make appointment_datetime timezone-aware
    appointment_datetime = timezone.make_aware(appointment_datetime, timezone.get_current_timezone())

    payment_details = RazorpayPaymentDetails.objects.filter(appointment=appointment).first()

    # Format the date in dd-mm-yyyy format
    formatted_date = DateFormat(appointment.date).format('d-m-Y')

    detailed_appointment = {
        'appointment': appointment,
        'related_object': related_object,
        'payment_details': payment_details,
        'appointment_datetime': appointment_datetime,
        'timing_details': timing_details,
        'formatted_date': formatted_date,
    }

    return render(request, 'backend/appointment-view.html', {'detailed_appointment': detailed_appointment})




def payment_success_account(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    payment_details = RazorpayPaymentDetails.objects.get(appointment=appointment)
    # Get the related object (AvailableTime or MonthlyTiming)
    content_type = appointment.content_type
    related_object = content_type.get_object_for_this_type(id=appointment.object_id)

    # Determine the timing
    if isinstance(related_object, AvailableTime):
        start_time = related_object.start_time
        end_time = related_object.end_time
    else:
        start_time = related_object.start_time
        end_time = related_object.end_time


    # Check if the user is a super admin
    if request.user.is_superuser:
        # Render the page for super admins
        return render(request, 'backend/payment-success.html', {
            'appointment': appointment,
            'start_time': start_time,
            'end_time': end_time,
            'payment_details':payment_details
        })
    else:
        # Redirect non-super admin users to another page
        return render(request, 'frontend/payment-success.html', {
            'appointment': appointment,
            'start_time': start_time,
            'end_time': end_time,
            'payment_details':payment_details
            
        })


def payment_failure_account(request):
    if request.user.is_superuser:
        return render(request, 'backend/payment-failure.html')
    else: 
        return render(request, 'frontend/payment-failure.html')
        





class CreateHealthCheckupBookingAPIView(APIView):
    def post(self, request, *args, **kwargs):
        # Extract data from request
        plan_id = request.data.get('plan_id')
        name = request.data.get('name')
        email = request.data.get('email')
        number = request.data.get('number')
        message = request.data.get('message')
        address = request.data.get('address')
        payment_method = request.data.get('payment')  # 'online' or 'pay_at_hospital'
        is_home_collection = request.data.get('home_collection', False) == 'on'  # Checkbox value

        # Validate required fields
        if not all([plan_id, name, email, number]):
            return Response(
                {"error": "Missing required fields"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Validate plan
        plan = get_object_or_404(HealthCheckupPlan, id=plan_id)

        # Create or get patient
        patient, created = Patient.objects.get_or_create(
            email=email,
            defaults={'name': name, 'phone_number': number}
        )

        # Create booking with conditional home collection
        booking_data = {
            'plan': plan,
            'patient': patient,
            'message': message,
            'is_home_sample_collection': is_home_collection,
        }
        
        if payment_method != 'online':
            booking_data['is_without_payment'] = True
            booking_data['status'] = 'COMPLETED'
        else: 
            booking_data['is_without_payment'] = False
            

        if is_home_collection and address:
            booking_data['home_sample_collection'] = address
        elif is_home_collection and not address:
            return Response(
                {"error": "Address is required for home sample collection"},
                status=status.HTTP_400_BAD_REQUEST
            )

        booking = HealthCheckupBooking.objects.create(**booking_data)

        # Handle payment
        amount = int(plan.price * 100)  # Convert to paise

        # Generate random IDs for Razorpay (you'll replace these with actual Razorpay IDs later)
        payment_id = str(uuid.uuid4())
        order_id = str(uuid.uuid4())

        # Create Razorpay payment details based on payment method
        payment_status = 'PENDING'
        
        if payment_method == 'online':
            # For "Pay Now" - prepare for payment gateway integration
            pass
        else:  # pay_at_hospital
            payment_details = RazorpayPaymentDetails.objects.create(
                payment_id=payment_id,
                order_id=order_id,
                signature='',
                amount=amount,
                currency='INR',
                payment_method='pay_at_hospital',
                status='PENDING',
                payment_for='CHECKUP',
                booking=booking,
            )

            Notification.objects.create(
                message=f"{name} booked a health checkup {plan.title} ",
                read_status=False,
                redirection_url=reverse('view_checkup_appointment', args=[booking.id]),
                object_id=plan.id,
                type='checkup'
            )
            
            response_data = {
                'booking_id': booking.id,
                'payment_id': payment_id,
                'order_id': order_id,
                'amount': amount,
                'status': 'PENDING'
            }

        return Response(
            response_data,
            status=status.HTTP_201_CREATED
        )


class CreateHealthCheckupBookingDoneAPIView(APIView):
    def post(self, request, *args, **kwargs):
        try:
            # Extract and validate data
            plan_id = request.data.get('plan_id')
            name = request.data.get('name')
            email = request.data.get('email')
            number = request.data.get('number')
            message = request.data.get('message', '')
            address = request.data.get('address', '')

            if not (plan_id and name and email and number):
                return Response(
                    {'status': 'error', 'message': 'Missing required fields'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate plan
            plan = get_object_or_404(HealthCheckupPlan, id=plan_id)

            # Create or get the patient
            patient, _ = Patient.objects.get_or_create(
                email=email,
                defaults={'name': name, 'phone_number': number}
            )

            # Create booking
            booking_data = {
                'plan': plan,
                'patient': patient,
                'status': "COMPLETED",
                'is_without_payment': True,
                'message': message,
                'is_home_sample_collection': True,
                'home_sample_collection': address if address else None
            }
            appointment = HealthCheckupBooking.objects.create(**booking_data)

            Notification.objects.create(
                message=f"{appointment.patient.name} booked a health checkup {appointment.plan.title} ",
                read_status=False,
                redirection_url=reverse('view_checkup_appointment', args=[appointment.id]),
                object_id=appointment.id,
                type='checkup'
            )

            return Response(
                {'status': 'success', 'message': 'Your Checkup Booked Successfully', 'is_done': True},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {'status': 'error', 'message': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class HandleHealthCheckupPaymentAPIView(APIView):
    def post(self, request, *args, **kwargs):
        payment_id = request.data.get('payment_id')
        booking_id = request.data.get('booking_id')
        razorpay_signature = request.data.get('razorpay_signature')

        # Retrieve booking and payment details
        booking = get_object_or_404(HealthCheckupBooking, id=booking_id)
        payment_details = get_object_or_404(RazorpayPaymentDetails, booking=booking, order_id=request.data.get('razorpay_order_id'))

        # Verify payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            'razorpay_order_id': payment_details.order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
            payment_details.payment_id = payment_id
            payment_details.signature = razorpay_signature
            payment_details.status = 'COMPLETED'
            payment_details.save()

            booking.status = 'COMPLETED'
            booking.save()

            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except razorpay.errors.SignatureVerificationError:
            return Response({'status': 'error', 'message': 'Payment verification failed.'}, status=status.HTTP_400_BAD_REQUEST)








@csrf_exempt
def handle_health_checkup_payment(request):
   
    print("hello World")





def health_checkup_payment_success(request, booking_id):
    booking = get_object_or_404(HealthCheckupBooking, id=booking_id)
    
    # Since health checkup bookings do not have time slots, we will just confirm the plan details.
    plan = booking.plan

    # Check if the user is a super admin
    if request.user.is_superuser:
        # Render the page for super admins
        return render(request, 'backend/healthcheckup-payment-success.html', {
            'booking': booking,
            'plan': plan
        })
    else:
        # Render for non-super admin users
        return render(request, 'frontend/healthcheckup-frontend-success.html', {
            'booking': booking,
            'plan': plan
        })



# views.py

def health_checkup_payment_failure(request):
    if request.user.is_superuser:
        return render(request, 'frontend/healthcheckup-payment-failure.html')
    else: 
        return render(request, 'frontend/healthcheckup-frontend-failure.html')






def homepage(request):
    departments = Department.objects.filter(status='active', show_on_homepage = True).order_by('priority')[:8]
    doctors = Doctor.objects.filter(show_on_homepage = True, status='active').order_by('priority')[:8]
    blogs = Blog.objects.filter(status='active', show_on_homepage = True)[:3]
    banners = Banner.objects.filter(status='active')
    ad_banners = AdBanner.objects.filter(status='active')
    checkups =  HealthCheckupPlan.objects.filter(status='active')[:8]

    context = {
        'departments': departments,
        'doctors': doctors,
        'blogs': blogs,
        'ad_banners': ad_banners,
        'banners': banners,
        'checkups':checkups
    }
    return render(request, 'frontend/index.html', context)


def about(request):
    doctors = Doctor.objects.filter(show_on_homepage = True, status='active').order_by('priority')[:8]
    blogs = Blog.objects.filter(status='active', show_on_homepage = True)[:3]
    context = {
        'doctors': doctors,
        'blogs': blogs,
    }
    return render(request, 'frontend/about.html', context)


def services(request):
    departments = Department.objects.filter(status='active').order_by('priority')
    context = {
        'departments': departments,
    }
    return render(request, 'frontend/services.html', context)


def service(request, slug):
    department = Department.objects.get(slug=slug)
    departments = Department.objects.filter(status='active', show_on_homepage = True).order_by('priority')[:5]
    context = {
        'department': department,
        'departments': departments,
    }
    
    return render(request, 'frontend/service.html', context)

def frontend_blogs(request):
    
    blogs = Blog.objects.filter(status='active')
    context = {
        'blogs': blogs,
    }
    return render(request, 'frontend/blogs.html', context)





def blog(request, slug):
    # Fetch the blog
    blog = get_object_or_404(Blog, slug=slug)
    tags_list = blog.tags.split(',')  # Assuming tags are comma-separated in the Blog model


    # Render context for GET request
    context = {
        'blog': blog,
        'tags_list': tags_list
    }
    return render(request, 'frontend/blog.html', context)






def contact(request):
    if request.method == 'POST':
        try:
            # Log the raw request for debugging
            logger.debug("Request body: %s", request.body)
            
            # Parse JSON data safely
            if not request.body:
                return JsonResponse(
                    {'success': False, 'error': 'Empty request body'}, 
                    status=400
                )
                
            data = json.loads(request.body.decode('utf-8'))
            logger.debug("Parsed JSON data: %s", data)
            
            # Initialize and validate form
            form = MessageForm(data)
            if form.is_valid():
                # Save the form instance
                message_instance = form.save()
                
                # Create notification
                Notification.objects.create(
                    message=f"{form.cleaned_data['name']} Messaged You",
                    read_status=False,
                    redirection_url=reverse('message', args=[message_instance.slug]),
                    object_id=message_instance.id,
                    type='contact'
                )
                
                return JsonResponse({
                    'success': True,
                    'message': 'Message sent successfully'
                }, status=201)
                
            else:
                logger.debug("Form errors: %s", form.errors)
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.as_json()
                }, status=400)
                
        except json.JSONDecodeError as e:
            logger.error("JSON decoding error: %s", str(e))
            return JsonResponse(
                {'success': False, 'error': 'Invalid JSON format'}, 
                status=400
            )
        except Exception as e:
            logger.error("Unexpected error: %s", str(e))
            return JsonResponse(
                {'success': False, 'error': 'Internal server error'}, 
                status=500
            )
            
    # Handle GET requests
    return render(request, 'frontend/contact.html', {
        'form': MessageForm()  # Pass an empty form for GET requests
    })


    


def checkups(request):
    checkups = HealthCheckupPlan.objects.filter(status='active')
    categories = HealthCheckupPlan.CATEGORY  # Fetching all categories

    context = {
        'checkups': checkups,
        'categories': categories,
    }
    return render(request, 'frontend/services.html', context)



def single_checkup(request, slug):
    checkup = HealthCheckupPlan.objects.get(slug=slug)
    checkups = HealthCheckupPlan.objects.filter(status='active', category=checkup.category)
    context = {
        'checkup': checkup,
        'checkups': checkups,
    }
    
    return render(request, 'frontend/service.html', context)



def gallery(request):
    gallery = Gallery.objects.all()

    context = {
        'gallery': gallery
    }
    
    return render(request, 'frontend/gallery.html', context)

def frontend_doctors(request):
    departments = Department.objects.filter(status='active').order_by('priority')
    
    selected_department = request.GET.get('department', None)  # Fetch selected department, default to None
    search_query = request.GET.get('search', '')  # Fetch search query, default to an empty string

    doctors = Doctor.objects.filter(status='active').order_by('priority')

    if selected_department:
        doctors = doctors.filter(department_id=selected_department)
        
    if search_query:
        doctors = doctors.filter(name__icontains=search_query)
    
    context = {
        'doctors': doctors,
        'departments': departments,
        'selected_department': selected_department,
        'search_query': search_query,
    }
    
    return render(request, 'frontend/doctors.html', context)
    


def frontend_doctor(request, slug):
    doctor = Doctor.objects.get(slug=slug)

    context = {
        'doctor': doctor,
    }
    
    return render(request, 'frontend/doctor.html', context)



def frontend_careers(request):    
    careers = Career.objects.filter(status='active')

    context = {
        'careers': careers,
    }
    return render(request, 'frontend/careers.html', context)



@csrf_exempt
def single_career(request, slug):
    career = get_object_or_404(Career, slug=slug)

    if request.method == 'POST':
        # Extract data from request
        name = request.POST.get('name')
        email = request.POST.get('email')
        number = request.POST.get('number')
        cover_letter = request.POST.get('cover-letter')
        cv = request.FILES.get('resume')

        # Create new career application
        application = CareerApplication(
            name=name,
            email=email,
            number=number,
            cover_letter=cover_letter,
            cv=cv,
            job=career
        )
        application.save()
        
        NotificationHR.objects.create(
            message=f"{application.name} Applied for {career.job_title} position",
            read_status=False,
            redirection_url=reverse('hr_view_career_application', args=[career.slug, application.slug]),
            object_id=application.id,
            type='career'
        )

        return JsonResponse({'success': True, 'message': 'Application submitted successfully'})

    context = {
        'career': career,
    }
    return render(request, 'frontend/career.html', context)



def privacy_policy(request):
    return render(request, 'frontend/privacy-policy.html')

def terms_condition(request):
    return render(request, 'frontend/terms-condition.html')











def create_home_sample_collection_view(request):
    if request.method == "POST":
        # Retrieve form data
        name = request.POST.get("name")
        email = request.POST.get("email")
        phone_number = request.POST.get("phone_number")
        message = request.POST.get("message", "")
        plan_id = request.POST.get("plan_id")
        prescription = request.FILES.get("prescription")  # Handling file upload


        # Validate and get related objects
        plan = get_object_or_404(HealthCheckupPlan, id=plan_id)

        # Create or get the patient
        patient, created = Patient.objects.get_or_create(
            email=email,
            defaults={
                'name': name,
                'phone_number': phone_number
            }
        )

        # Create HomeSampleCollection instance
        appointment = HomeSampleCollection.objects.create(
            patient=patient,
            plan=plan,
            message=message,
            prescription=prescription  # Save the uploaded file
        )

        Notification.objects.create(
            message=f"{name} booked a health checkup {plan.title} for home sample collection",
            read_status=False,
            redirection_url=reverse('view_home_sample_appointment', args=[appointment.id]),
            object_id=appointment.id,
            type='checkup'
        )


        msg.success(request, "Your Booking Confirmed")


    # Pass available plans to the template
    plans = HealthCheckupPlan.objects.filter(is_home_sample_available=True)
    return render(request, "frontend/home-sample.html", {"plans": plans})









from django.views import View
import requests
import random


API_KEY = "adcf6991-063b-11f0-8b17-0200cd936042"  # Replace with your 2Factor.in API key

# OTP Send View
class OTPSendView(View):
    def get(self, request):
        return render(request, 'frontend/login.html')

    def post(self, request):
        phone_number = request.POST.get('phone_number')
        
        if not phone_number or not phone_number.isdigit() or len(phone_number) != 10:
            msg.error(request, "Please enter a valid 10-digit phone number.")
            return redirect('otp_send')

        # Send OTP request to 2Factor.in
        url = f"https://2factor.in/API/V1/{API_KEY}/SMS/{phone_number}/AUTOGEN"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("Status") == "Success":
                # Store phone number and SessionId in session
                request.session['phone_number'] = phone_number
                request.session['otp_session_id'] = data.get("Details")  # SessionId from 2Factor.in
                request.session.set_expiry(300)  # 5-minute expiry
                msg.success(request, "OTP has been sent to your phone number.")
                return redirect('otp_verify')
            else:
                msg.error(request, "Failed to send OTP. Please try again.")
                return redirect('otp_send')
        else:
            msg.error(request, "Error connecting to SMS service. Please try again.")
            return redirect('otp_send')

# OTP Verify View
class OTPVerifyView(View):
    def get(self, request):
        if 'phone_number' not in request.session or 'otp_session_id' not in request.session:
            return redirect('otp_send')
        return render(request, 'frontend/otp_verify.html')

    def post(self, request):
        entered_otp = request.POST.get('otp').strip()  # Remove any whitespace
        session_id = request.session.get('otp_session_id')
        phone_number = request.session.get('phone_number')

        if not phone_number or not session_id:
            msg.error(request, "Session expired. Please start again.")
            return redirect('otp_send')

        # Verify OTP with 2Factor.in
        url = f"https://2factor.in/API/V1/{API_KEY}/SMS/VERIFY/{session_id}/{entered_otp}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("Status") == "Success" and data.get("Details") == "OTP Matched":
                try:
                    patient = Patient.objects.filter(phone_number=phone_number).first()
                    bookings = HealthCheckupBooking.objects.filter(patient=patient)
                    request.session['verified_phone_number'] = phone_number
                    del request.session['otp_session_id']  # Clear session ID after verification
                    return redirect('view_bookings')
                except Patient.DoesNotExist:
                    msg.info(request, "No bookings found for this phone number.")
                    return redirect('view_bookings')
                    
            else:
                msg.error(request, "Invalid OTP. Please try again.")
                return redirect('otp_verify')
        else:
            msg.error(request, "Error verifying OTP. Please try again.")
            return redirect('otp_verify')



def view_bookings(request):
    phone_number = request.session.get('verified_phone_number')
    if not phone_number:
        return redirect('otp_send')
    
    try:
        patient = Patient.objects.filter(phone_number=phone_number).first()
        if patient:
            bookings = HealthCheckupBooking.objects.filter(patient=patient).prefetch_related('payment_details')  # Use correct related_name
        else:
            bookings = []
        
        return render(request, 'frontend/booking_list.html', {
            'bookings': bookings,
            'phone_number': phone_number
        })
    except Patient.DoesNotExist:
        return render(request, 'frontend/booking_list.html', {
            'bookings': [],
            'phone_number': phone_number
        })


def logout(request):
    request.session.flush()  # Clear all session data
    msg.success(request, "You have been logged out successfully.")
    return redirect('otp_send')  # Redirect to the login/OTP send page



def specialities(request):
    specialities = Department.objects.filter(status = 'active')
    context = {
        'specialities': specialities
    }
    return render(request, 'frontend/specialities.html', context)

def speciality_detail(request, slug):
    speciality = Department.objects.get(slug=slug)
    specialities = Department.objects.filter(status = 'active')

    context = {
        'speciality': speciality,
        'specialities': specialities
        
    }
    return render(request, 'frontend/speciality.html', context)