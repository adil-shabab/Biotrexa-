from django.db import models
from ckeditor.fields import RichTextField
from django.utils.text import slugify
import uuid
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.urls import reverse
from tinymce.models import HTMLField
from django.contrib.auth.models import User


STATUS_CHOICES = [
    ('active', 'Active'),
    ('inactive', 'Inactive'),
]


# Create your models here.
class Department(models.Model):
    description = HTMLField(null=True, blank=True)
    small_description = models.TextField(null=True, blank=True)
    show_on_homepage = models.BooleanField(default=False)  # New field to control homepage display
    title = models.CharField(max_length=200)
    banner = models.FileField(upload_to='departments', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')    
    slug = models.SlugField(unique=True)
    priority = models.DecimalField(max_digits=4, decimal_places=0, null=True, blank=True)

    def __str__(self):
        return self.title
# Create your models here.


class Facility(models.Model):
    description = HTMLField(null=True, blank=True)
    small_description = models.TextField(null=True, blank=True)
    show_on_homepage = models.BooleanField(default=False)  # New field to control homepage display
    title = models.CharField(max_length=200)
    image = models.FileField(upload_to='facilities', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')    
    slug = models.SlugField(unique=True)
    priority = models.DecimalField(max_digits=4, decimal_places=0, null=True, blank=True)

    def __str__(self):
        return self.title



class Consultation(models.Model):
    description = models.TextField(null=True, blank=True)
    title = models.CharField(max_length=200)
    image = models.FileField(upload_to='consultation', null=True, blank=True)
    icon = models.FileField(upload_to='consultation-icon', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')    
    slug = models.SlugField(unique=True)
    priority = models.DecimalField(max_digits=4, decimal_places=0, null=True, blank=True)

    def __str__(self):
        return self.title





class AdBanner(models.Model):
    slug = models.SlugField(unique=True, blank=True, null=True)
    image = models.ImageField(upload_to='ad_banners/')
    created_at = models.DateTimeField(auto_now_add=True)
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='ad_banners', null=True, blank=True)
    department = models.ForeignKey('Department', on_delete=models.CASCADE, related_name='ad_banners', null=True, blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')    


    def save(self, *args, **kwargs):
        if not self.slug:
            if self.department:
                # If department exists, create slug based on department title
                self.slug = slugify(f'{self.department.title}-ad')
            else:
                # If no department, use UUID for the slug
                self.slug = str(uuid.uuid4())

            original_slug = self.slug
            counter = 1
            while AdBanner.objects.filter(slug=self.slug).exists():
                if self.department:
                    self.slug = f'{original_slug}-{counter}'
                else:
                    self.slug = f'{uuid.uuid4()}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.doctor.name if self.doctor else 'No Doctor'} - {self.department.title if self.department else 'No Department'} - {self.status}"





    @property
    def redirect_url(self):
        if self.doctor:
            return reverse('frontend_doctor', args=[self.doctor.slug])
        elif self.department:
            return f"{reverse('frontend_doctors')}?department={self.department.title}"
        else:
            return reverse('frontend_doctors')
     

class Banner(models.Model):
    heading = models.CharField(max_length=255)
    description = models.TextField()
    button_text = models.CharField(max_length=100)
    button_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    image_for_desktop = models.ImageField(upload_to='banners/desktop/')
    image_for_mobile = models.ImageField(upload_to='banners/mobile/')
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')    


    def __str__(self):
        return self.heading



        

class Gallery(models.Model):
    image = models.ImageField(upload_to='gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Gallery Image - {self.id}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Gallery'
        verbose_name_plural = 'Galleries'
        
        

    
class Doctor(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    experience_years = models.PositiveIntegerField()
    fee = models.DecimalField(max_digits=10, decimal_places=2)
    email = models.EmailField()
    number = models.CharField(max_length=15)
    gender = models.CharField(max_length=6, choices=GENDER_CHOICES)
    education = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    photo = models.ImageField(upload_to='doctors')
    slug = models.SlugField(unique=True, blank=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')    
    priority = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    description = HTMLField()
    show_on_homepage = models.BooleanField(default=False)  # New field to control homepage display



    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Doctor.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



    def get_absolute_url(self):
        return reverse('frontend_doctor', args=[self.slug])



class AvailableTime(models.Model):
    DAY_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='available_times')
    day = models.CharField(max_length=9, choices=DAY_CHOICES)
    start_time = models.TimeField()
    slot = models.PositiveIntegerField()
    end_time = models.TimeField()
    status = models.CharField(max_length=10, default='active')
    remaining_slots = models.PositiveIntegerField(default=5)


    def __str__(self):
        return f'{self.doctor.name} - {self.day} {self.start_time} to {self.end_time}'

class MonthlyTiming(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    date = models.DateField(default=timezone.now)
    start_time = models.TimeField()    
    status = models.CharField(max_length=10, default='active')
    end_time = models.TimeField()
    slot = models.PositiveIntegerField()
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='available_monthly_times')
    remaining_slots = models.PositiveIntegerField(default=5)


    def __str__(self):
        return f"{self.doctor.name} - {self.date} ({self.slot})"




class Blog(models.Model):
    heading = models.TextField()
    image = models.ImageField(upload_to='blog_images/')
    category = models.CharField(max_length=100)
    createdAt = models.DateTimeField(auto_now_add=True)
    author = models.CharField(max_length=255)
    author_designation = models.CharField(max_length=255)
    content = HTMLField()
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')    

    tags = models.TextField(null=True, blank=True)  # Field to store tags
    slug = models.SlugField(unique=True, blank=True)
    show_on_homepage = models.BooleanField(default=False)  # New field to control homepage display


    def get_absolute_url(self):
        return reverse('blog', args=[self.slug])


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.heading)
            original_slug = self.slug
            counter = 1
            while Blog.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)


    def __str__(self):
        return self.heading


    def get_tags(self):
        """Return the list of tags."""
        return self.tags.split(',') if self.tags else []




class Message(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=15)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Message.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)



    def __str__(self):
        return self.name
    
    



class Career(models.Model):

    job_title = models.CharField(max_length=200)
    department = models.CharField(max_length=200,null=True, blank=True)
    experience = models.PositiveIntegerField(help_text="Years of experience required")
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    responsibilities = HTMLField()
    skills = HTMLField()
    job_summary = HTMLField()
    qualifications = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=8, choices=STATUS_CHOICES, default='active')    



    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.job_title)
            original_slug = self.slug
            counter = 1
            while Career.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)



    def __str__(self):
        return self.job_title


    def get_absolute_url(self):
        return reverse('single_career', args=[self.slug])



class CareerApplication(models.Model):
    name = models.CharField(max_length=100)
    number = models.CharField(max_length=15)
    email = models.EmailField()
    cover_letter = models.TextField(blank=True, null=True)
    cv = models.FileField(upload_to='cvs/')
    created_at = models.DateTimeField(auto_now_add=True)
    job = models.ForeignKey(Career, on_delete=models.CASCADE, related_name='career_application')
    slug = models.SlugField(unique=True, blank=True)


    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while CareerApplication.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)






class BlogComment(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while BlogComment.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Comment by {self.name} on {self.blog.heading}"




class Leave(models.Model):
    date = models.DateField(default=timezone.now)
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='leave_date')
    created_at = models.DateTimeField(auto_now_add=True)
    reason = models.TextField()

    def __str__(self):
        return f"{self.doctor} - {self.date}"






class Patient(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ]

    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(default=timezone.now)
    disease = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(unique=True, blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='male')  # Add gender field

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            original_slug = self.slug
            counter = 1
            while Patient.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name



class Appointment(models.Model):
    PAYMENT_STATUS = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
    )

    date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    message = models.TextField(null=True, blank=True, default='')
    payment_id = models.CharField(max_length=255, null=True, blank=True)
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='PENDING')
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    selected_doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    slug = models.SlugField(unique=True, blank=True, null=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # New field

    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    schedule = GenericForeignKey('content_type', 'object_id')

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.patient.name}-{self.date}')
            original_slug = self.slug
            counter = 1
            while Appointment.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super(Appointment, self).save(*args, **kwargs)

    def __str__(self):
        return f'Appointment with {self.selected_doctor} on {self.date} at {self.schedule}'



    
    
class Notification(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    read_status = models.BooleanField(default=False)
    redirection_url = models.CharField(max_length=200, blank=True, null=True)
    type = models.CharField(max_length=200, default='appointment')
    object_id = models.PositiveIntegerField(default=1)
    is_alarmed = models.BooleanField(default=False)  # New field
    first_read_by = models.ForeignKey(User, related_name='first_read_notifications', null=True, blank=True, on_delete=models.SET_NULL)  # New field


    def __str__(self):
        return self.message




class Summary(models.Model):
    ROLE_CHOICES = [
        ('frontdesk', 'Front Desk'),
        ('hr', 'HR'),
        ('media', 'Media'),
        ('admin', 'Admin')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.user.username} Profile'
    




class HealthCheckupPlan(models.Model):


    CATEGORY = [
        ('Clinical Services ', 'Clinical Services '),
        ('Laboratory Services', 'Laboratory Services'),
        ('Radiology Services', 'Radiology Services'),
        ('Minor OT', 'Minor OT'),
        ('Dietetics', 'Dietetics'),
        ('Pharmacy', 'Pharmacy'),
        ('Research & Innovation in Diagnostics', 'Research & Innovation in Diagnostics'),
    ]

    category = models.CharField(max_length=105, choices=CATEGORY, default='health_checkup')

    title = models.CharField(max_length=255)
    description = HTMLField()
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default='active')    
    is_home_sample_available = models.BooleanField(default=False)
    is_online_payment_available = models.BooleanField(default=True)

    total_test_include = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='health_checkup_plans/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f'{self.title}')
            original_slug = self.slug
            counter = 1
            while HealthCheckupPlan.objects.filter(slug=self.slug).exists():
                self.slug = f'{original_slug}-{counter}'
                counter += 1
        super(HealthCheckupPlan, self).save(*args, **kwargs)

    def __str__(self):
        return self.title



    def get_absolute_url(self):
        return reverse('single_checkup', args=[self.slug])
    


class HealthCheckupBooking(models.Model):
    plan = models.ForeignKey(HealthCheckupPlan, on_delete=models.CASCADE, related_name='bookings')
    message = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('PENDING', 'Pending'), ('COMPLETED', 'Completed')], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='health_checkup_bookings')
    payment_id = models.CharField(max_length=255, null=True, blank=True)
    is_home_sample_collection = models.BooleanField(default=False)
    home_sample_collection = models.TextField(null=True, blank=True)
    is_without_payment = models.BooleanField(default=False, null=True, blank=True)
    report = models.FileField(upload_to='reports/', null=True, blank=True)  # New field for PDF report

    def __str__(self):
        return f"{self.patient.name} - {self.plan.title}"






class HomeSampleCollection(models.Model):
    plan = models.ForeignKey(HealthCheckupPlan, on_delete=models.CASCADE, related_name='bookings_home_sample')
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='health_checkup_bookings_home_sample')
    prescription = models.FileField(
        upload_to='prescriptions/',
        blank=True,
        null=True,
        help_text="Upload the patient's prescription (optional)"
    )

    def __str__(self):
        return f"{self.patient.name} - {self.plan.title}"





class RazorpayPaymentDetails(models.Model):

    PAYMENT_FOR = (
        ('APPOINTMENT', 'APPOINTMENT'),
        ('CHECKUP', 'CHECKUP'),
    )

    payment_id = models.CharField(max_length=255)
    order_id = models.CharField(max_length=255)
    signature = models.CharField(max_length=255)
    amount = models.PositiveIntegerField()  # Amount in paise
    currency = models.CharField(max_length=10, default='INR')
    payment_method = models.CharField(max_length=50)
    status = models.CharField(max_length=10)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name='razorpay_payment_details', null=True, blank=True)
    payment_for = models.CharField(max_length=12, choices=PAYMENT_FOR, default='APPOINTMENT')
    booking = models.OneToOneField(HealthCheckupBooking, on_delete=models.CASCADE, related_name='payment_details', null=True, blank=True)

    

    def __str__(self):
        return f'Payment {self.payment_id} for Appointment {self.payment_for}'
    
    
    
    