from django import forms
from django.contrib.auth.hashers import make_password
from .models import User,FacialRecognition

class SignUpForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(), label="Password")
    password_confirm = forms.CharField(widget=forms.PasswordInput(), label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("This email is already registered.")

        # if not email or not email.endswith('@example.com'):
        #     raise forms.ValidationError("Email must be from the domain 'example.com'.")

        return email
    
    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("This username is already taken")
        
        return username

    def clean_password_confirm(self):
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')

        if password != password_confirm:
            raise forms.ValidationError("Passwords do not match.")
        return password_confirm

    def save(self, commit=True):
        user = super().save(commit=False)
        user.password = make_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
    
    
class ImageUploadForm(forms.ModelForm):
    class Meta:
        model = FacialRecognition
        fields = ['image_1', 'image_2']
        widgets = {
            'image_1': forms.FileInput(attrs={
                'class': 'absolute inset-0 w-full h-full opacity-0 cursor-pointer',
                'accept': 'image/*',
                'required': True,
                'id': 'id_image_1'
            }),
            'image_2': forms.FileInput(attrs={
                'class': 'absolute inset-0 w-full h-full opacity-0 cursor-pointer', 
                'accept': 'image/*',
                'required': True,
                'id': 'id_image_2'
            })
        }
        labels = {
            'image_1': 'First Image',
            'image_2': 'Second Image'
        }
