# forms.py

from django import forms
from .models import *


STATUS_CHOICES = [
    (True, 'Active'),
    (False, 'Inactive')
]




class BlogCommentForm(forms.Form):
    name = forms.CharField(max_length=100, required=True, widget=forms.TextInput(attrs={'placeholder': 'Your Name'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Your Email'}))
    comment = forms.CharField(widget=forms.Textarea(attrs={'placeholder': 'Write Your Comment'}), required=True)
    rating = forms.IntegerField(min_value=1, max_value=5, required=True, widget=forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]))

class BannerForm(forms.ModelForm):

    class Meta:
        model = Banner
        fields = [
            'heading',
            'description',
            'button_text',
            'button_url',
            'image_for_desktop',
            'image_for_mobile',
            'status'
        ]
        widgets = {
            
            'image_for_desktop': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL(this)",
                "accept": "image/*"
            }),
            'image_for_mobile': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL2(this)",
                "accept": "image/*"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['heading'].widget.attrs['class'] = 'form-control'
        self.fields['description'].widget.attrs['class'] = 'form-control description_class'
        self.fields['button_text'].widget.attrs['class'] = 'form-control'
        self.fields['button_url'].widget.attrs['class'] = 'form-control'





class GalleryForm(forms.ModelForm):
    class Meta:
        model = Gallery
        fields = ['image']

        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL(this)",
                "accept": "image/*"
            }),
   
        }
        





class AdBannerForm(forms.ModelForm):
    
    class Meta:
        model = AdBanner
        fields = ['department', 'doctor', 'image', 'status']

        widgets = {

            'image': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL(this)",
                "accept": "image/*"
            }),

            
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['department'].widget.attrs['class'] = 'form-control'
        self.fields['doctor'].widget.attrs['class'] = 'form-control'




class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['title', 'priority', 'banner', 'status', 'small_description', 'description', 'show_on_homepage']

        widgets = {

            'banner': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL(this)",
                "accept": "image/*"
            }),
            
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['priority'].widget.attrs['class'] = 'form-control'
        self.fields['small_description'].widget.attrs['class'] = 'form-control'
        self.fields['priority'].widget.attrs['class'] = 'form-control'
        self.fields['small_description'].widget.attrs['required'] = True  # Make description required




class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['title', 'priority', 'image', 'status', 'small_description', 'description', 'show_on_homepage']

        widgets = {

            'image': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL(this)",
                "accept": "image/*"
            }),

            
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['priority'].widget.attrs['class'] = 'form-control'
        self.fields['small_description'].widget.attrs['class'] = 'form-control'
        self.fields['priority'].widget.attrs['class'] = 'form-control'
        self.fields['small_description'].required = True  # Make description required










class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['title', 'priority', 'image', 'status', 'icon', 'description']

        widgets = {

            'image': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL(this)",
                "accept": "image/*"
            }),
            'icon': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL2(this)",
                "accept": "image/*"
            }),
            
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['priority'].widget.attrs['class'] = 'form-control'
        self.fields['description'].widget.attrs['class'] = 'form-control'
        self.fields['priority'].widget.attrs['class'] = 'form-control'
        self.fields['description'].required = True  # Make description required












class CheckupForm(forms.ModelForm):
    
    class Meta:
        model = HealthCheckupPlan
        fields = ['title', 'is_home_sample_available', 'is_online_payment_available', 'price', 'image', 'category', 'total_test_include', 'description', 'status']

        widgets = {

            'image': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL(this)",
                "accept": "image/*"
            }),
            'price': forms.TextInput(attrs={
                'placeholder': '₹'
            })
            
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].widget.attrs['class'] = 'form-control'
        self.fields['price'].widget.attrs['class'] = 'form-control'
        self.fields['total_test_include'].widget.attrs['class'] = 'form-control'
        self.fields['category'].widget.attrs['class'] = 'form-control'






class DoctorForm(forms.ModelForm):

    class Meta:
        model = Doctor
        fields = [
            'name','designation', 'experience_years', 'fee', 'email', 'number', 'gender',
            'education', 'city', 'priority', 'photo', 'status', 'show_on_homepage', 'description'
        ]
        widgets = {
            
            'photo': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL(this)",
                "accept": "image/*"
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['designation'].widget.attrs['class'] = 'form-control'
        self.fields['experience_years'].widget.attrs['class'] = 'form-control'
        self.fields['fee'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['number'].widget.attrs['class'] = 'form-control'
        self.fields['gender'].widget.attrs['class'] = 'form-control'
        self.fields['education'].widget.attrs['class'] = 'form-control'
        self.fields['priority'].widget.attrs['class'] = 'form-control'
        self.fields['city'].widget.attrs['class'] = 'form-control'
        self.fields['show_on_homepage'].widget.attrs['class'] = 'form-check-input'  # Added this line


class AvailableTimeForm(forms.ModelForm):
    class Meta:
        model = AvailableTime
        fields = ['day', 'start_time', 'end_time', 'slot']



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['day'].widget.attrs['class'] = 'form-control'
        self.fields['start_time'].widget.attrs['class'] = 'form-control'
        self.fields['end_time'].widget.attrs['class'] = 'form-control'
        self.fields['slot'].widget.attrs['class'] = 'form-control'



class MonthlyTimeForm(forms.ModelForm):
    class Meta:
        model = MonthlyTiming
        fields = ['date', 'start_time', 'end_time', 'slot']



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs['class'] = 'form-control'
        self.fields['start_time'].widget.attrs['class'] = 'form-control'
        self.fields['end_time'].widget.attrs['class'] = 'form-control'
        self.fields['slot'].widget.attrs['class'] = 'form-control'



class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['heading', 'show_on_homepage', 'image', 'category', 'author', 'content', 'status', 'tags', 'author_designation']
        widgets = {
            
            'image': forms.FileInput(attrs={
                'class': 'file__input',
                'required': 'required',
                'onchange' : "readURL(this)",
                "accept": "image/*"
            }),
            'tags': forms.TextInput(attrs={'class': 'form-control'}),
        }
        
        
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['heading'].widget.attrs['class'] = 'form-control'
        self.fields['category'].widget.attrs['class'] = 'form-control'
        self.fields['author_designation'].widget.attrs['class'] = 'form-control'
        self.fields['author'].widget.attrs['class'] = 'form-control'
        self.fields['content'].widget.attrs['class'] = 'form-control'
        self.fields['show_on_homepage'].widget.attrs['class'] = 'form-check-input'  # Added this line




        
    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        tags = tags.replace(' ', '')  # Remove any spaces around commas
        return tags



class CareerForm(forms.ModelForm):

    class Meta:
        model = Career
        fields = [
            'job_title', 'department', 'experience', 'salary',
            'responsibilities', 'skills', 'job_summary', 
            'qualifications', 'status'
        ]

        widgets = {
            
        }



    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['job_title'].widget.attrs['class'] = 'form-control'
        self.fields['department'].widget.attrs['class'] = 'form-control'
        self.fields['experience'].widget.attrs['class'] = 'form-control'
        self.fields['salary'].widget.attrs['class'] = 'form-control'
        self.fields['qualifications'].widget.attrs['class'] = 'form-control'




class LeaveForm(forms.ModelForm):
    class Meta:
        model = Leave
        fields = ['date', 'reason']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['date'].widget.attrs['class'] = 'form-control'
        self.fields['reason'].widget.attrs['class'] = 'form-control'



class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['name', 'email', 'phone_number', 'disease', 'gender']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].widget.attrs['class'] = 'form-control'
        self.fields['email'].widget.attrs['class'] = 'form-control'
        self.fields['phone_number'].widget.attrs['class'] = 'form-control'
        self.fields['disease'].widget.attrs['class'] = 'form-control'
        self.fields['gender'].widget.attrs['class'] = 'form-control'


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['name', 'email', 'phone_number', 'content']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Basic validation: Check if the phone number is a valid 10-digit number
        if not phone_number.isdigit() or len(phone_number) not in [10, 12]:
            raise forms.ValidationError("Please enter a valid phone number.")
        return phone_number

        