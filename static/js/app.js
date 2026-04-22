/**
 * 🎬 VidCover Tools — Main App JS
 * Navigation, scroll effects, animations
 */

document.addEventListener('DOMContentLoaded', () => {

    // ========================================================================
    // NAVBAR
    // ========================================================================

    // Mobile nav toggle
    const navToggle = document.getElementById('nav-toggle');
    const navLinks = document.getElementById('nav-links');

    if (navToggle && navLinks) {
        navToggle.addEventListener('click', () => {
            navLinks.classList.toggle('open');
            navToggle.classList.toggle('active');
        });

        // Close on link click (mobile)
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', () => {
                navLinks.classList.remove('open');
                navToggle.classList.remove('active');
            });
        });
    }

    // Navbar scroll effect
    const navbar = document.getElementById('main-nav');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        });
    }

    // ========================================================================
    // SCROLL ANIMATIONS
    // ========================================================================

    const animElements = document.querySelectorAll('.animate-on-scroll');

    if (animElements.length > 0) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

        animElements.forEach(el => observer.observe(el));
    }

    // ========================================================================
    // TOAST NOTIFICATIONS
    // ========================================================================

    window.showToast = function(message, type = 'success') {
        // Remove existing toasts
        document.querySelectorAll('.toast').forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'}</span>
            <span class="toast-message">${message}</span>
        `;

        // Styles
        Object.assign(toast.style, {
            position: 'fixed',
            top: '90px',
            right: '24px',
            padding: '14px 20px',
            borderRadius: '10px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontSize: '0.9rem',
            fontWeight: '600',
            zIndex: '9999',
            animation: 'slideInRight 0.3s ease, fadeOut 0.3s ease 2.7s forwards',
            background: type === 'success' ? 'rgba(16, 185, 129, 0.15)' :
                        type === 'error' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(139, 92, 246, 0.15)',
            border: `1px solid ${type === 'success' ? 'rgba(16, 185, 129, 0.3)' :
                     type === 'error' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(139, 92, 246, 0.3)'}`,
            color: type === 'success' ? '#10b981' :
                   type === 'error' ? '#ef4444' : '#8b5cf6',
            backdropFilter: 'blur(10px)',
        });

        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 3200);
    };

    // Add toast animation styles
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { opacity: 0; transform: translateX(60px); }
            to { opacity: 1; transform: translateX(0); }
        }
        @keyframes fadeOut {
            from { opacity: 1; }
            to { opacity: 0; }
        }
    `;
    document.head.appendChild(style);

    // ========================================================================
    // UTILITY: API Request Helper
    // ========================================================================

    window.apiRequest = async function(url, method = 'GET', data = null) {
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' },
        };
        if (data) options.body = JSON.stringify(data);

        try {
            const res = await fetch(url, options);
            const json = await res.json();
            return json;
        } catch (err) {
            console.error('API Error:', err);
            return { success: false, error: 'Network error. Please try again.' };
        }
    };

    // ========================================================================
    // CONFIRM DIALOG
    // ========================================================================

    window.confirmAction = function(message) {
        return confirm(message);
    };

});
