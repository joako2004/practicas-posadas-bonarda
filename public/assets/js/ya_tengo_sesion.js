document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    
    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const dni = document.getElementById('dni').value;
        const password = document.getElementById('password').value;
        
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    dni: dni,
                    password: password
                })
            });
            
            if (response.ok) {
                const loginData = await response.json();
                // Generate JWT token for the user
                const tokenResponse = await fetch('/autenticar_creacion_usuario/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded'
                    },
                    body: new URLSearchParams({
                        username: loginData.user.email, // Use email as username
                        password: password
                    }).toString()
                });

                if (tokenResponse.ok) {
                    const tokenData = await tokenResponse.json();
                    localStorage.setItem('token', tokenData.access_token);
                    window.location.href = '/crear_reserva';
                } else {
                    alert('Error al generar token de sesión');
                }
            } else {
                const errorData = await response.json();
                // Check if it's a credential error vs server error
                if (response.status === 401) {
                    alert('Los datos no corresponden a un usuario registrado');
                } else {
                    alert(errorData.detail || 'Error al iniciar sesión');
                }
            }
        } catch (error) {
            alert('Error de conexión: ' + error.message);
        }
    });
});