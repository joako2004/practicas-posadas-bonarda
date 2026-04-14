// Espera a que el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM Content Loaded');
    
    // Referencias a elementos
    var loginToggleBtn = document.getElementById('login-toggle-btn');
    var registerToggleBtn = document.getElementById('register-toggle-btn');
    var registrationForm = document.getElementById('registration-form');
    var loginForm = document.getElementById('login-form');
    var togglePasswordBtns = document.querySelectorAll('.toggle-password');
    
    console.log('loginToggleBtn:', loginToggleBtn);
    console.log('registerToggleBtn:', registerToggleBtn);
    console.log('togglePasswordBtns:', togglePasswordBtns.length);
    
    // Toggle: Mostrar formulario de login
    if (loginToggleBtn) {
        loginToggleBtn.onclick = function() {
            console.log('Click en YA TENGO CUENTA');
            registrationForm.classList.add('hidden');
            loginForm.classList.remove('hidden');
        };
    }
    
    // Toggle: Mostrar formulario de registro
    if (registerToggleBtn) {
        registerToggleBtn.onclick = function() {
            console.log('Click en CREAR CUENTA');
            loginForm.classList.add('hidden');
            registrationForm.classList.remove('hidden');
        };
    }
    
    // Toggle password visibility
    for (var i = 0; i < togglePasswordBtns.length; i++) {
        togglePasswordBtns[i].onclick = function(e) {
            e.preventDefault();
            console.log('Click en toggle password');
            
            var targetId = this.getAttribute('data-target');
            var input = document.getElementById(targetId);
            var img = this.querySelector('img');
            
            if (input && img) {
                if (input.type === 'password') {
                    input.type = 'text';
                    img.src = '/static/assets/images/ojo-dos.png';
                } else {
                    input.type = 'password';
                    img.src = '/static/assets/images/ojo-uno.png';
                }
            }
        };
    }
    
    // Formulario de registro
    if (registrationForm) {
        registrationForm.onsubmit = function(e) {
            e.preventDefault();
            console.log('Submit registro');
            
            var password = document.getElementById('password').value;
            var confirmPassword = document.getElementById('confirm-password').value;
            
            if (password !== confirmPassword) {
                alert('Las contraseñas no coinciden');
                return;
            }
            
            var data = {
                nombre: document.getElementById('nombre').value,
                apellido: document.getElementById('apellido').value,
                dni: document.getElementById('dni').value,
                cuil_cuit: document.getElementById('cuil_cuit').value,
                email: document.getElementById('email').value,
                telefono: document.getElementById('telefono').value,
                password: document.getElementById('password').value
            };
            
            fetch('/usuarios/crear', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(function(response) {
                if (!response.ok) {
                    return response.json().then(function(err) { throw new Error(err.detail); });
                }
                return response.json();
            })
            .then(function(data) {
                localStorage.setItem('token', data.token);
                alert('Usuario creado exitosamente!');
                window.location.href = '/crear_reserva';
            })
            .catch(function(error) {
                alert('Error: ' + error.message);
            });
        };
    }
    
    // Formulario de login
    if (loginForm) {
        loginForm.onsubmit = function(e) {
            e.preventDefault();
            console.log('Submit login');
            
            var dni = document.getElementById('login-dni').value;
            var password = document.getElementById('login-password').value;
            
            fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dni: dni, password: password })
            })
            .then(function(response) {
                if (!response.ok) {
                    return response.json().then(function(err) { throw new Error(err.detail); });
                }
                return response.json();
            })
            .then(function(loginData) {
                return fetch('/autenticar_creacion_usuario/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'username=' + loginData.user.email + '&password=' + password
                });
            })
            .then(function(tokenResponse) {
                if (!tokenResponse.ok) {
                    throw new Error('Error al generar token');
                }
                return tokenResponse.json();
            })
            .then(function(tokenData) {
                localStorage.setItem('token', tokenData.access_token);
                alert('Inicio de sesión exitoso!');
                window.location.href = '/crear_reserva';
            })
            .catch(function(error) {
                alert('Error: ' + error.message);
            });
        };
    }
    
    console.log('Scripts inicializados');
});