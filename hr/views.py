from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from core.forms import *
from core.models import *
from django.contrib import messages as mp
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
import datetime
from django.utils.timezone import now
from django.core.paginator import Paginator
from django.utils.dateformat import DateFormat
from django.core.exceptions import ObjectDoesNotExist



@login_required(login_url='login')
def hr_dashboard(request):

    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        mp.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if not profile.role == 'hr':
        if profile.role == 'admin':
            return redirect('dashboard')
        else:
            return redirect('homepage')



    job_openings_count = Career.objects.filter(status = 'active').count()
    application_count = CareerApplication.objects.all().count()

    context= {
        'job_openings_count': job_openings_count,
        'application_count' : application_count
    }
    return render(request, 'hr/dashboard.html', context)





# career view 
@login_required(login_url='login')
def hr_careers(request):
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        mp.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if not profile.role == 'hr':
        if profile.role == 'admin':
            return redirect('dashboard')
        else:
            return redirect('homepage')



            
    careers = Career.objects.all()
    context ={'careers': careers}
    return render(request, 'hr/career.html', context)


@login_required(login_url='login')
def hr_create_career(request):
 
 
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        mp.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if not profile.role == 'hr':
        if profile.role == 'admin':
            return redirect('dashboard')
        else:
            return redirect('homepage')



            
    if request.method == 'POST':
        form = CareerForm(request.POST)
        if form.is_valid():
            form.save()
            mp.success(request, 'Career created successfully!')
            return redirect('hr_careers')  # Redirect to a list of careers or any other appropriate view
    else:
        form = CareerForm()
    
    return render(request, 'hr/create-career.html', {'form': form})


@login_required(login_url='login')
def hr_update_career(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        mp.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if not profile.role == 'hr':
        if profile.role == 'admin':
            return redirect('dashboard')
        else:
            return redirect('homepage')


    career = Career.objects.get(slug=slug)
    if request.method == 'POST':
        form = CareerForm(request.POST, instance=career)
        if form.is_valid():
            form.save()
            mp.success(request, 'Career Updated successfully!')
            return redirect('hr_careers')  # Redirect to a list of careers or any other appropriate view
    else:
        form = CareerForm(instance=career)
    
    return render(request, 'hr/update-career.html', {'form': form})


@login_required(login_url='login')
def hr_delete_career(request, pk):
    
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        mp.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if not profile.role == 'hr':
        if profile.role == 'admin':
            return redirect('dashboard')
        else:
            return redirect('homepage')


 

    try:
        career = Career.objects.get(id=pk)
        career.delete()
        mp.success(request, 'Career deleted successfully.')
        return redirect('hr_careers')
    except Career.DoesNotExist:
        mp.error(request, 'Career not found.')
        return redirect('hr_careers')
    
    

@login_required(login_url='login')
def hr_view_career_applications(request, slug):
    
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        mp.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if not profile.role == 'hr':
        if profile.role == 'admin':
            return redirect('dashboard')
        else:
            return redirect('homepage')


   
    career = Career.objects.get(slug=slug)
    applications = CareerApplication.objects.filter(job=career)
    application_count = CareerApplication.objects.all().count()
    now = datetime.datetime.now().strftime('%I:%M %p')
    context = {'career': career, 'applications': applications, 'application_count':application_count,'now':now}
    return render(request, 'hr/career-application-view.html', context)


@login_required(login_url='login')
def hr_view_career_application(request, careerslug, applicationslug):
    try:
        profile = Summary.objects.get(user=request.user)
    except ObjectDoesNotExist:
        mp.error(request,'Profile does not exist. You cannot access here.')
        return redirect('login')

    if not profile.role == 'hr':
        if profile.role == 'admin':
            return redirect('dashboard')
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
    return render(request, 'hr/career-application-view-inner.html', context)