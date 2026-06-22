// Dynamic rain particle spawner
(function() {
    const particlesContainer = document.getElementById('particles');
    if (!particlesContainer) return;

    // Spawn a single particle
    function spawnParticle() {
        const p = document.createElement('span');
        const left = Math.random() * 100;
        const startY = -(Math.random() * 200 + 50);  // -50 to -250px
        const duration = 3 + Math.random() * 8;      // 3–11 seconds
        const height = 80 + Math.random() * 120;     // 80–200px
        const opacity = 0.3 + Math.random() * 0.5;   // 0.3–0.8

        p.style.left = left + '%';
        p.style.height = height + 'px';
        p.style.setProperty('--start', startY + 'px');
        p.style.animationDuration = duration + 's';
        p.style.opacity = opacity;

        particlesContainer.appendChild(p);

        // Remove particle after animation ends
        p.addEventListener('animationend', function() {
            p.remove();
        });
    }

    // Spawn a few immediately so the effect isn't empty at start
    for (let i = 0; i < 15; i++) {
        setTimeout(spawnParticle, i * 150);
    }

    // Then spawn new particles at random intervals
    function scheduleNext() {
        const delay = 150 + Math.random() * 600; // 150–750ms
        setTimeout(() => {
            spawnParticle();
            scheduleNext();
        }, delay);
    }
    scheduleNext();
})();

// Protected links – unchanged
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

// ---------- Loading Overlay (improved) ----------
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

    // ... (isSamePageAnchor, click handler, submit handler remain unchanged) ...

    // Hide loader when page finishes loading
    window.addEventListener('load', function() {
        hideLoader();
    });

    // Show loader on page unload (navigation, refresh, back/forward)
    window.addEventListener('beforeunload', function() {
        showLoader();   // <-- this is the fix
    });

    // Fallback: hide loader after 10 seconds (in case something goes wrong)
    setTimeout(hideLoader, 10000);
})();
// ---------- Inline username editing ----------
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
            // Focus the input
            const input = editForm.querySelector('input[name="new_username"]');
            if (input) input.focus();
        });

        if (cancelBtn) {
            cancelBtn.addEventListener('click', function() {
                displaySpan.style.display = 'inline';
                editBtn.style.display = 'inline';
                editForm.style.display = 'none';
                // Reset input to current username (in case of change)
                const input = editForm.querySelector('input[name="new_username"]');
                if (input) input.value = displaySpan.textContent.trim();
            });
        }
    }
});