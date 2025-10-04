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
                window.location.href = '../crear_reserva/crear_reserva.html';
            } else {
                const errorData = await response.json();
                alert(errorData.detail || 'Error al iniciar sesión');
            }
        } catch (error) {
            alert('Error de conexión: ' + error.message);
        }
    });
});