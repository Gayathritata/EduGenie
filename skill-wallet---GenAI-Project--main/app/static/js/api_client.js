/* File: app/static/js/api_client.js */
/* Core Asynchronous Network Client for EduGenie */

class APIClient {
    static async request(endpoint, method = 'GET', body = null) {
        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        };

        const config = {
            method,
            headers,
            credentials: 'include',
            cache: 'no-store'
        };

        if (body && (method === 'POST' || method === 'PUT')) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(endpoint, config);
            const data = await response.json();

            if (!response.ok) {
                if (response.status === 401) {
                    APIClient.clearAuthCookie();
                    throw new Error('Please sign in to use this feature.');
                }
                
                const errorMsg = data.detail || 'An unexpected error occurred.';
                throw new Error(errorMsg);
            }

            return data;
        } catch (error) {
            console.error(`API Error on ${method} ${endpoint}:`, error);
            throw error;
        }
    }

    static get(endpoint) {
        return APIClient.request(endpoint, 'GET');
    }

    static post(endpoint, body) {
        return APIClient.request(endpoint, 'POST', body);
    }

    static delete(endpoint) {
        return APIClient.request(endpoint, 'DELETE');
    }

    static clearAuthCookie() {
        document.cookie = "access_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    }

    static logoutUserLocal() {
        APIClient.clearAuthCookie();
    }
}

/* Global Premium Notification Handler */
function showNotification(message, type = 'success') {
    let container = document.getElementById('toast-notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-notification-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = '';
    if (type === 'success') {
        icon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
    } else if (type === 'error') {
        icon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
    } else {
        icon = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>`;
    }

    toast.innerHTML = `${icon}<span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 10);

    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}

