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

    // Validaciones adicionales
    const nombre = document.getElementById('nombre').value;
    const apellido = document.getElementById('apellido').value;
    const dni = document.getElementById('dni').value;
    const cuil_cuit = document.getElementById('cuil_cuit').value;
    const telefono = document.getElementById('telefono').value;

    if (nombre.length < 2) {
        alert('El nombre debe tener al menos 2 caracteres');
        return;
    }
    if (apellido.length < 2) {
        alert('El apellido debe tener al menos 2 caracteres');
        return;
    }
    if (dni.length < 7 || dni.length > 8 || !/^\d+$/.test(dni)) {
        alert('El DNI debe tener 7 u 8 dígitos');
        return;
    }
    const cuilLimpio = cuil_cuit.replace(/[-\s]/g, '');
    if (cuilLimpio.length < 10 || cuilLimpio.length > 13 || !/^\d+$/.test(cuilLimpio)) {
        alert('CUIL/CUIT debe tener entre 10 y 13 dígitos (puede incluir guiones)');
        return;
    }
    if (telefono.replace(/[\s\-\(\)]/g, '').length < 8 || !/^\d+$/.test(telefono.replace(/[\s\-\(\)]/g, ''))) {
        alert('El teléfono debe tener al menos 8 dígitos');
        return;
    }
    if (password.length < 8) {
        alert('La contraseña debe tener al menos 8 caracteres');
        return;
    }

    // Recopila datos del form
    const data = {
        nombre: document.getElementById('nombre').value,
        apellido: document.getElementById('apellido').value,
        dni: document.getElementById('dni').value,
        cuil_cuit: document.getElementById('cuil_cuit').value,
        email: document.getElementById('email').value,
        telefono: document.getElementById('telefono').value,
        password: document.getElementById('password').value
    };

    try {
        const response = await fetch('/usuarios/crear', {  // Endpoint de tu backend
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)  // Envía como JSON
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
        // Guardar token en localStorage
        if (result.token) {
            localStorage.setItem('token', result.token);
        }
        window.location.href = '/';  // Redirige a home

    } catch (error) {
        alert('Error de conexión: ' + error.message);
    }
});