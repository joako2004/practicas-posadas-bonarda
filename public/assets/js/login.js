document.querySelector('.login-form').addEventListener('submit', async function(e) {
    e.preventDefault();  

    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    const formData = new URLSearchParams();
    formData.append('username', email);  
    formData.append('password', password);

    try {
        const response = await fetch('/autenticar_creacion_usuario/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: formData.toString()
        });

        if (!response.ok) {
            const errorData = await response.json();
            alert(errorData.detail || 'Error de autenticación');
            return;
        }

        const result = await response.json();
        alert('Inicio de sesión exitoso!');
        localStorage.setItem('token', result.access_token);
        window.location.href = '/crear_reserva';  // Redirige a crear reserva

    } catch (error) {
        alert('Error de conexión: ' + error.message);
    }
});