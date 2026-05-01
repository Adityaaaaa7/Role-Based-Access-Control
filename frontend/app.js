const API_URL = 'http://localhost:5000/api';

function setToken(token) {
    localStorage.setItem('token', token);
}

function getToken() {
    return localStorage.getItem('token');
}

function removeToken() {
    localStorage.removeItem('token');
}

function checkAuth(redirectIfNotAuth = true) {
    const token = getToken();
    if (!token && redirectIfNotAuth) {
        window.location.href = 'login.html';
        return false;
    }
    return !!token;
}

function logout() {
    removeToken();
    window.location.href = 'login.html';
}
