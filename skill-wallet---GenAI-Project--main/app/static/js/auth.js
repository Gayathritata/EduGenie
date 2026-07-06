/* File: app/static/js/auth.js */
/* Authentication Submit Handlers and Token Routines */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Login Form Submission Handler
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById('username').value.trim();
            const passwordInput = document.getElementById('password').value;
            const errorBox = document.getElementById('auth-error');

            if (!usernameInput || !passwordInput) {
                showError(errorBox, 'Please fill in all fields.');
                return;
            }

            setLoadingState(loginForm, true);
            hideError(errorBox);

            try {
                const response = await fetch('/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: usernameInput, password: passwordInput })
                });
                
                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'Incorrect credentials.');
                }

                // Redirect to dashboard on successful login
                window.location.href = '/dashboard';
            } catch (err) {
                showError(errorBox, err.message);
            } finally {
                setLoadingState(loginForm, false);
            }
        });
    }

    // 2. Registration Form Submission Handler
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const usernameInput = document.getElementById('username').value.trim();
            const emailInput = document.getElementById('email').value.trim();
            const passwordInput = document.getElementById('password').value;
            const confirmInput = document.getElementById('confirm-password').value;
            const errorBox = document.getElementById('auth-error');

            if (!usernameInput || !emailInput || !passwordInput || !confirmInput) {
                showError(errorBox, 'Please fill in all fields.');
                return;
            }

            if (passwordInput !== confirmInput) {
                showError(errorBox, 'Passwords do not match.');
                return;
            }

            setLoadingState(registerForm, true);
            hideError(errorBox);

            try {
                const response = await fetch('/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username: usernameInput, email: emailInput, password: passwordInput })
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'Registration failed.');
                }

                // Redirect to login on successful register
                window.location.href = '/login?msg=registered';
            } catch (err) {
                showError(errorBox, err.message);
            } finally {
                setLoadingState(registerForm, false);
            }
        });
    }

    // 3. Logout Button Click Handler
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                await fetch('/auth/logout', { method: 'POST' });
            } catch (err) {
                console.error('Logout error:', err);
            }
            // Clear local states and redirect
            document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
            window.location.href = '/login?msg=logged_out';
        });
    }
});

/* Utilities */
function showError(element, text) {
    if (element) {
        element.textContent = text;
        element.style.display = 'block';
        element.classList.add('animated');
    }
}

function hideError(element) {
    if (element) {
        element.textContent = '';
        element.style.display = 'none';
    }
}

function setLoadingState(formElement, isLoading) {
    const submitBtn = formElement.querySelector('button[type="submit"]');
    if (submitBtn) {
        if (isLoading) {
            submitBtn.disabled = true;
            submitBtn.dataset.originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="spinner" style="width:16px;height:16px;border-width:2px;margin:0;"></span> Processing...';
        } else {
            submitBtn.disabled = false;
            submitBtn.innerHTML = submitBtn.dataset.originalText || 'Submit';
        }
    }
}
