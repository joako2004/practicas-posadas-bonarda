document.querySelector('.login-form').addEventListener('submit', async function(e) {
    e.preventDefault();  // Evita submit tradicional

    // Recopila datos del form
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;

    // Crear FormData con URLSearchParams
    const formData = new URLSearchParams();
    formData.append('username', email);  // Backend espera 'username', no 'email'
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