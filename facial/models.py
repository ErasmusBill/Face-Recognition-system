from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    Custom user model that extends the default Django user model.
    """
    verification_code = models.CharField(max_length=255, blank=True, null=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        
    def __str__(self) -> str:
        return self.username  
    
    
class FacialRecognition(models.Model):
    """
    Model to store facial recognition data.
    """
    COMPARISON_CHOICES = [
        ('same', 'Same Person'),
        ('different', 'Different Person'),
        ('no_face', 'No Face Detected'),
        ('error', 'Error Occurred'),
        ('pending', 'Pending'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='facial_recognition')
    image_1 = models.ImageField(upload_to='facial_recognition_images/')
    image_2 = models.ImageField(upload_to='facial_recognition_images/')
    comparison_result = models.CharField(
        max_length=20, 
        choices=COMPARISON_CHOICES, 
        default='pending',
        help_text="Result of the facial recognition comparison"
    )
    result_details = models.TextField(
        blank=True, 
        null=True,
        help_text="Additional details about the comparison result"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facial Recognition"
        verbose_name_plural = "Facial Recognitions"
        ordering = ['-created_at']
        
    def __str__(self) -> str:
        return f"Facial Recognition for {self.user.username} - {self.get_result_display()}"
    
    def get_result_display(self):
        """Return a user-friendly display of the comparison result"""
        result_map = {
            'same': '✓ Same Person',
            'different': '✗ Different Person', 
            'no_face': '⚠ No Face Detected',
            'error': '❌ Error Occurred',
            'pending': '⏳ Pending'
        }
        return result_map.get(self.comparison_result, 'Unknown')