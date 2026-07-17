// Dynamic rain particle spawner
(function() {
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;

    function spawnParticle() {
        const p = document.createElement('span');
        const left = Math.random() * 100;
        const startY = -(Math.random() * 200 + 50);
        const duration = 3 + Math.random() * 8;
        const height = 80 + Math.random() * 120;
        const opacity = 0.3 + Math.random() * 0.5;

        p.style.left = left + '%';
        p.style.height = height + 'px';
        p.style.setProperty('--start', startY + 'px');
        p.style.animationDuration = duration + 's';
        p.style.opacity = opacity;

        particlesContainer.appendChild(p);

        p.addEventListener('animationend', function() {
            p.remove();
        });
    }

    for (let i = 0; i < 15; i++) {
        setTimeout(spawnParticle, i * 150);
    }

    function scheduleNext() {
        const delay = 150 + Math.random() * 600;
        setTimeout(() => {
            spawnParticle();
            scheduleNext();
        }, delay);
    }
    scheduleNext();
})();

// Protected links
document.addEventListener('DOMContentLoaded', function() {
    const isAuthenticated = document.body.dataset.authenticated === 'true';

    function handleProtectedClick(e) {
        if (!isAuthenticated) {
            e.preventDefault();
            e.stopPropagation();
            alert('ACCESS DENIED\nAuthentication Required\nPlease log in to access challenge archives.');
            window.location.href = '/auth/login';
            return false;
        }
        return true;
    }

    document.querySelectorAll('[data-protected="true"]').forEach(el => {
        el.addEventListener('click', handleProtectedClick);
    });
    document.querySelectorAll('.protected-link').forEach(el => {
        el.addEventListener('click', handleProtectedClick);
    });
});

// Loading Overlay
(function() {
    const overlay = document.getElementById('loading-overlay');

    function showLoader() {
        if (overlay) {
            overlay.classList.add('show');
            overlay.style.display = 'flex';
        }
    }

    function hideLoader() {
        if (overlay) {
            overlay.classList.remove('show');
            overlay.style.display = 'none';
        }
    }

    window.addEventListener('load', function() {
        hideLoader();
    });

    window.addEventListener('beforeunload', function() {
        showLoader();
    });

    setTimeout(hideLoader, 10000);
})();

// Inline username editing
document.addEventListener('DOMContentLoaded', function() {
    const editBtn = document.getElementById('editUsernameBtn');
    const displaySpan = document.getElementById('usernameDisplay');
    const editForm = document.getElementById('editUsernameForm');
    const cancelBtn = document.getElementById('cancelEditUsername');

    if (editBtn && displaySpan && editForm) {
        editBtn.addEventListener('click', function() {
            displaySpan.style.display = 'none';
            editBtn.style.display = 'none';
            editForm.style.display = 'block';
            const input = editForm.querySelector('input[name="new_username"]');
            if (input) input.focus();
        });

        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                displaySpan.style.display = 'inline';
                editBtn.style.display = 'inline';
                editForm.style.display = 'none';
                const input = editForm.querySelector('input[name="new_username"]');
                if (input) input.value = displaySpan.textContent.trim();
            });
        }
    }
});
