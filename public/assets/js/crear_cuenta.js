// verificar que la contraseña y verificar contraseña sean iguales
document.querySelector('.registration-form').addEventListener('submit', function(e) {
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    
    if (password !== confirmPassword) {
        e.preventDefault();
        alert('Las contraseñas no coinciden');
        return false;
    }
});

document.querySelector('.registration-form').addEventListener('submit', async function(e) {
    e.preventDefault();  // Evita submit tradicional

    // Verifica contraseñas coinciden (ya lo tienes)
    const password = document.getElementById('password').value;
    const confirmPassword = document.getElementById('confirm-password').value;
    if (password !== confirmPassword) {
        alert('Las contraseñas no coinciden');
        return;
    }

    // Recopila datos del form
    const formData = new FormData(this);
    const data = Object.fromEntries(formData.entries());  // Convierte a JSON

    try {
        const response = await fetch('/usuarios/crear', {  // Endpoint de tu backend
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'  // Envía como JSON (ajusta si usas Form)
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json();
            let errorMsg = errorData.detail || 'Error desconocido';
            if (errorData.errors) {
                errorMsg += '\n' + errorData.errors.join('\n');  // Muestra lista de errores
            }
            alert(errorMsg);  // Ventana sencilla con el error
            return;
        }

        // Si ok, redirige o muestra éxito
        const result = await response.json();
        alert('Usuario creado exitosamente!');
        window.location.href = '/';  // Redirige a home

    } catch (error) {
        alert('Error de conexión: ' + error.message);
    }
});