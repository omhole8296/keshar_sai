// ==================== GLOBAL FUNCTIONS ====================

// Toggle profile dropdown
function toggleDropdown() {
    const dropdown = document.getElementById('dropdown');
    if (dropdown) {
        dropdown.classList.toggle('active');
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const profileMenu = document.querySelector('.profile-menu');
    const dropdown = document.getElementById('dropdown');
    if (profileMenu && dropdown && !profileMenu.contains(event.target)) {
        dropdown.classList.remove('active');
    }
});

// ==================== DASHBOARD FUNCTIONS ====================

// View property details
function viewProperty(id) {
    window.location.href = `/property/${id}`;
}

// Search functionality
const searchInput = document.getElementById('searchInput');
if (searchInput) {
    searchInput.addEventListener('input', function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const cards = document.querySelectorAll('.property-card');
        
        cards.forEach(card => {
            const title = card.querySelector('.card-title');
            const location = card.querySelector('.card-location');
            
            if (title && location) {
                const titleText = title.textContent.toLowerCase();
                const locationText = location.textContent.toLowerCase();
                
                if (titleText.includes(searchTerm) || locationText.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            }
        });
    });
}

// Category filter
document.querySelectorAll('.category-tab').forEach(tab => {
    tab.addEventListener('click', function() {
        // Update active tab
        document.querySelectorAll('.category-tab').forEach(t => t.classList.remove('active'));
        this.classList.add('active');

        // Filter cards
        const category = this.dataset.category;
        const cards = document.querySelectorAll('.property-card');

        cards.forEach(card => {
            if (category === 'all' || card.dataset.category === category) {
                card.style.display = 'block';
            } else {
                card.style.display = 'none';
            }
        });
    });
});

// ==================== PROPERTY VIEW FUNCTIONS ====================

// Change main image
function changeImage(thumbnail) {
    const mainImage = document.getElementById('mainImage');
    if (mainImage && thumbnail) {
        mainImage.style.backgroundImage = thumbnail.style.backgroundImage;
        
        // Update active thumbnail
        document.querySelectorAll('.thumbnail').forEach(t => t.classList.remove('active'));
        thumbnail.classList.add('active');
    }
}

// Book property
function bookProperty() {
    if (confirm('Are you sure you want to book this property?')) {
        alert('Booking request submitted! Our team will contact you shortly.');
        // Flask will handle actual booking
        // Uncomment below for AJAX submission
        // const propertyId = window.location.pathname.split('/').pop();
        // fetch(`/book-property/${propertyId}`, { method: 'POST' })
        //     .then(response => response.json())
        //     .then(data => {
        //         if (data.success) {
        //             alert('Booking successful!');
        //         }
        //     });
    }
}

// Edit property (owner only)
function editProperty() {
    const propertyId = window.location.pathname.split('/').pop();
    window.location.href = `/edit-property/${propertyId}`;
}

// Delete property (owner only)
function deleteProperty() {
    if (confirm('Are you sure you want to delete this property? This action cannot be undone.')) {
        const propertyId = window.location.pathname.split('/').pop();
        
        fetch(`/delete-property/${propertyId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Property deleted successfully!');
                window.location.href = '/dashboard';
            } else {
                alert('Error deleting property: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error deleting property. Please try again.');
        });
    }
}

// Call now
function callNow() {
    window.location.href = 'tel:+919876543210';
}

// WhatsApp chat
function whatsappChat() {
    window.open('https://wa.me/919876543210?text=Hi, I am interested in the property', '_blank');
}

// Schedule visit
function scheduleVisit() {
    alert('Visit scheduling form will open');
    // Flask will handle this
}

// Share property
function shareProperty() {
    if (navigator.share) {
        navigator.share({
            title: document.querySelector('.property-title')?.textContent || 'Property',
            text: 'Check out this property',
            url: window.location.href
        }).catch(err => console.log('Error sharing:', err));
    } else {
        // Fallback - copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            alert('Link copied to clipboard!');
        }).catch(() => {
            alert('Could not copy link. Please copy manually: ' + window.location.href);
        });
    }
}

// Like property
function likeProperty(propertyId) {
    fetch(`/like-property/${propertyId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI without alert
            return true;
        } else {
            console.log(data.message);
            return false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        return false;
    });
}

// Unlike property
function unlikeProperty(propertyId) {
    fetch(`/unlike-property/${propertyId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI without alert
            return true;
        } else {
            console.log(data.message);
            return false;
        }
    })
    .catch(error => {
        console.error('Error:', error);
        return false;
    });
}

// Toggle like/unlike
function toggleLike(event, propertyId) {
    event.stopPropagation(); // Prevent card click
    event.preventDefault();
    
    const likeBtn = event.currentTarget;
    const icon = likeBtn.querySelector('i');
    const isLiked = likeBtn.classList.contains('liked');
    
    if (isLiked) {
        // Unlike
        fetch(`/unlike-property/${propertyId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                likeBtn.classList.remove('liked');
                icon.classList.remove('fa-solid');
                icon.classList.add('fa-regular');
                
                // If on liked properties page, reload to remove the card
                if (window.location.pathname.includes('liked-properties')) {
                    setTimeout(() => location.reload(), 300);
                }
            }
        })
        .catch(error => console.error('Error:', error));
    } else {
        // Like
        fetch(`/like-property/${propertyId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                likeBtn.classList.add('liked');
                icon.classList.remove('fa-regular');
                icon.classList.add('fa-solid');
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

// ==================== FORM FUNCTIONS ====================

// Preview uploaded images
function previewImage(input, index) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            const preview = document.getElementById('preview' + index);
            const box = document.getElementById('imageBox' + index);
            
            if (preview && box) {
                preview.src = e.target.result;
                box.classList.add('has-image');
            }
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

// Remove image
function removeImage(index) {
    if (event) {
        event.stopPropagation();
    }
    
    const box = document.getElementById('imageBox' + index);
    const preview = document.getElementById('preview' + index);
    const input = box?.querySelector('input[type="file"]');
    
    if (box && preview && input) {
        box.classList.remove('has-image');
        preview.src = '';
        input.value = '';
        
        // Add hidden input to track deletion (for edit page)
        const form = document.getElementById('propertyForm');
        if (form) {
            const deleteInput = document.createElement('input');
            deleteInput.type = 'hidden';
            deleteInput.name = 'delete_image' + index;
            deleteInput.value = 'true';
            form.appendChild(deleteInput);
        }
    }
}

// Form validation
const propertyForm = document.getElementById('propertyForm');
if (propertyForm) {
    propertyForm.addEventListener('submit', function(e) {
        // Don't prevent default - let Flask handle submission
        
        // Basic validation
        const requiredFields = this.querySelectorAll('[required]');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.style.borderColor = 'red';
            } else {
                field.style.borderColor = '';
            }
        });
        
        if (!isValid) {
            e.preventDefault();
            alert('Please fill all required fields');
            return false;
        }
        
        return true;
    });
}

// ==================== PAGE LOAD ====================
document.addEventListener('DOMContentLoaded', function() {
    console.log('Keshar Sai Developers - Page Loaded');
});
