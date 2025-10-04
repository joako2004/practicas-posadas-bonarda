document.querySelector('.login-form').addEventListener('submit', async function(e) {
    e.preventDefault();  // Evita submit tradicional

    // Recopila datos del form
    const data = {
        email: document.getElementById('email').value,
        password: document.getElementById('password').value
    };

    try {
        const response = await fetch('/autenticar_creacion_usuario/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json();
            alert(errorData.detail || 'Error de autenticación');
            return;
        }

        // Si ok, guarda token y redirige
        const result = await response.json();
        alert('Inicio de sesión exitoso!');
        // Guardar token en localStorage
        localStorage.setItem('token', result.access_token);
        window.location.href = '/';  // Redirige a home

    } catch (error) {
        alert('Error de conexión: ' + error.message);
    }
});