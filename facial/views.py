from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from .models import FacialRecognition, User
from django.contrib import messages
from .forms import SignUpForm, ImageUploadForm
from django.dispatch import receiver
from django.db.models.signals import post_save
import random
from django.core.mail import send_mail  
from PIL import Image
import face_recognition
import numpy as np
import logging
from django.conf import settings
import io
import os

logger = logging.getLogger(__name__)

def signup_view(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            email = form.cleaned_data.get('email')
            if username and password and email:
                verification_code = random.randint(100000, 999999)
                logger.info(f"Verification pin generated for {email}")
                User.objects.create_user(username=username, password=password, email=email,verification_code=verification_code,is_verified=False)
                messages.success(request, 'Account created successfully.Please check your email for verification code.')
                return redirect('verify-email')  
            else:
                messages.error(request, 'All fields are required.')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = SignUpForm()
    return render(request, 'facial/signup.html', {'form': form})

@receiver(post_save, sender=User)
def send_verification_email(sender, instance, created, **kwargs):
    if created:
        try:
            verification_code = int(instance.verification_code)
            subject = "Welcome! Verify Your Email"
            message = f"Hello {instance.username},\n\nYour verification code is: {verification_code}"
            email_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@yourdomain.com')
            recipient_list = [instance.email]

            send_mail(subject, message, email_from, recipient_list,fail_silently=False)
            logger.info(f"Verification email sent to {instance.email}")
        
        except Exception as e:
            logger.error(f"Failed to send verification email to {instance.email}")

def resend_verification_view(request, email=None):
    if request.method == 'POST':
        if email:
            try:
                user = User.objects.get(email=email, is_verified=False)
                # Generate new verification code
                user.verification_code = str(random.randint(100000, 999999))
                user.save()

                # Send new verification email
                send_verification_email(user, created=False)

                messages.success(request, 'New verification code sent to your email.')
            except User.DoesNotExist:
                messages.error(request, 'No unverified account found with this email.')
        else:
            messages.error(request, 'Email is required.')

        return redirect('verify_email_page') 

    return render(request, 'facial/resend_verification.html') 
       
def verify_email_view(request):
    if request.method == "POST":
        verification_code = request.POST.get("verification_code")
        
        if not verification_code:
            messages.error(request, 'Verification code is required.')
            return render(request, 'facial/verify_email.html')
        
        try:
            user = User.objects.get(verification_code=verification_code)
            user.is_verified = True
            user.save()
            messages.success(request, 'Email verified successfully.')
            return redirect('login')
        except User.DoesNotExist:
            messages.error(request, 'Invalid verification code.')
            return render(request, 'facial/verify_email.html')
    
    return render(request, 'facial/verify_email.html')
                
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
       
        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'facial/login.html')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'is_verified') and not user.is_verified: # type: ignore
                messages.error(request, "please verify your email before logging")
                return redirect('verify_email_page')
            
            login(request, user)
            messages.success(request, f'Welcome {user.username}!')
            return redirect('home')  
        else:
            messages.error(request, 'Invalid username or password.')
            logger.warning(f"Failed login attempt for user: {username}")
      
    return render(request, 'facial/login.html')

def logout_view(request):
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.success(request, f'Goodbye {username}! You have been logged out successfully.')
    return redirect('login')  

def current_user(request):
    if request.user.is_authenticated:
        return HttpResponse(f"Current user: {request.user.username}")
    else:
        return HttpResponse("No user is currently logged in.")

@login_required   
def upload_images(request):
    """
    View to handle facial recognition image uploads and comparison
    """
    if request.method == "POST":
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            image1 = form.cleaned_data.get('image1')
            image2 = form.cleaned_data.get('image2')
            
            if not image1 or not image2:
                messages.error(request, 'Both images are required.')
                return render(request, 'facial/upload_images.html', {'form': form})
            
            try:
                # Create FacialRecognition instance
                facial_recognition = FacialRecognition.objects.create(
                    user=request.user,
                    image_1=image1,
                    image_2=image2,
                    comparison_result='pending'
                )
                
                # Perform facial comparison
                comparison_result = compare_faces_from_db(facial_recognition)
                
                # Update the result
                facial_recognition.comparison_result = comparison_result['status']
                facial_recognition.result_details = comparison_result['details']
                facial_recognition.save()
                
                # Add appropriate message
                if comparison_result['status'] == 'same':
                    messages.success(request, '✓ Images contain the same person!')
                elif comparison_result['status'] == 'different':
                    messages.info(request, '✗ Images contain different people.')
                elif comparison_result['status'] == 'no_face':
                    messages.warning(request, '⚠ No face detected in one or both images.')
                else:
                    messages.error(request, f'❌ Error occurred: {comparison_result["details"]}')
                
                return redirect('facial_recognition_detail', pk=facial_recognition.pk)
                
            except Exception as e:
                logger.error(f"Error processing facial recognition for user {request.user.username}: {str(e)}")
                messages.error(request, 'An error occurred while processing your images. Please try again.')
                return render(request, 'facial/upload_images.html', {'form': form})
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ImageUploadForm()
    
    return render(request, 'facial/upload_images.html', {'form': form})

@login_required
def facial_recognition_history(request):
    """
    View to display user's facial recognition history
    """
    recognitions = FacialRecognition.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'facial/recognition_history.html', {'recognitions': recognitions})

@login_required
def facial_recognition_detail(request, pk):
    """
    View to display details of a specific facial recognition
    """
    try:
        recognition = FacialRecognition.objects.get(pk=pk, user=request.user)
        return render(request, 'facial/recognition_detail.html', {'recognition': recognition})
    except FacialRecognition.DoesNotExist:
        messages.error(request, 'Facial recognition record not found.')
        return redirect('facial_recognition_history')

def compare_faces_from_db(facial_recognition_instance):
    """
    Compare faces from database stored images
    
    Args:
        facial_recognition_instance: FacialRecognition model instance
        
    Returns:
        dict: Contains status and details of comparison
    """
    try:
        # Get file paths from the model instance
        image1_path = facial_recognition_instance.image_1.path
        image2_path = facial_recognition_instance.image_2.path
        
        # Load images using face_recognition
        img1 = face_recognition.load_image_file(image1_path)   
        img2 = face_recognition.load_image_file(image2_path)

        # Get face encodings
        enc1 = face_recognition.face_encodings(img1)
        enc2 = face_recognition.face_encodings(img2)
        
        # Check if faces were detected
        if not enc1 and not enc2:
            return {
                'status': 'no_face',
                'details': 'No faces detected in either image'
            }
        elif not enc1:
            return {
                'status': 'no_face',
                'details': 'No face detected in the first image'
            }
        elif not enc2:
            return {
                'status': 'no_face',
                'details': 'No face detected in the second image'
            }
        
        # Compare faces
        result = face_recognition.compare_faces([enc1[0]], enc2[0], tolerance=0.6)
        
        # Calculate face distance for additional details
        face_distance = face_recognition.face_distance([enc1[0]], enc2[0])[0]
        confidence_percentage = max(0, (1 - face_distance) * 100)
        
        if result[0]:
            return {
                'status': 'same',
                'details': f'Faces match with {confidence_percentage:.1f}% confidence (distance: {face_distance:.3f})'
            }
        else:
            return {
                'status': 'different',
                'details': f'Faces do not match. Confidence: {confidence_percentage:.1f}% (distance: {face_distance:.3f})'
            }
            
    except FileNotFoundError as e:
        logger.error(f"Image file not found: {str(e)}")
        return {
            'status': 'error',
            'details': 'One or both image files could not be found'
        }
    except Exception as e:
        logger.error(f"Error in facial comparison: {str(e)}")
        return {
            'status': 'error',
            'details': f'Error processing images: {str(e)}'
        }

def compare_faces(image1_path, image2_path):
    """
    Legacy function for backward compatibility
    """
    try:
        img1 = face_recognition.load_image_file(image1_path)   
        img2 = face_recognition.load_image_file(image2_path) 

        # Face encoding
        enc1 = face_recognition.face_encodings(img1)
        enc2 = face_recognition.face_encodings(img2)
        
        if not enc1 or not enc2:
            return "No face detected"
        
        result = face_recognition.compare_faces([enc1[0]], enc2[0])
        
        return "Same person" if result[0] else "Different person"
    except Exception as e:
        return f"Error: {str(e)}"

@login_required
def home(request):
    """
    Home view showing user dashboard
    """
    recent_recognitions = FacialRecognition.objects.filter(user=request.user).order_by('-created_at')[:5]
    context = {
        'recent_recognitions': recent_recognitions,
        'total_recognitions': FacialRecognition.objects.filter(user=request.user).count()
    }
    return render(request, 'facial/home.html', context)