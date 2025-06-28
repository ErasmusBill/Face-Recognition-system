// Image preview functionality
document.getElementById('image_1')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('img1').src = e.target.result;
            document.getElementById('preview1').classList.remove('hidden');
        }
        reader.readAsDataURL(file);
    }
});

document.getElementById('image_2')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('img2').src = e.target.result;
            document.getElementById('preview2').classList.remove('hidden');
        }
        reader.readAsDataURL(file);
    }
});

// Add fade-in animation to elements
document.addEventListener('DOMContentLoaded', function() {
    const elements = document.querySelectorAll('.fade-in');
    elements.forEach((el, index) => {
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 100);
    });
});