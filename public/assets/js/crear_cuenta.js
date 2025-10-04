document.querySelector('.registration-form').addEventListener('submit', async function(e) {
    e.preventDefault(); // Evita submit tradicional

    // Verifica contraseñas coinciden
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
        // Crear usuario
        const response = await fetch('/usuarios/crear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const errorData = await response.json();
            let errorMsg = errorData.detail || 'Error desconocido';
            if (errorData.errors) {
                errorMsg += '\n' + errorData.errors.join('\n');
            }
            alert(errorMsg);
            return;
        }

        // Iniciar sesión automáticamente
        console.log('DEBUG: Attempting login with URL /autenticar_creacion_usuario/login');
        const loginResponse = await fetch('/autenticar_creacion_usuario/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `username=${encodeURIComponent(data.email)}&password=${encodeURIComponent(data.password)}`
        });
        console.log('DEBUG: Login response status:', loginResponse.status);

        if (!loginResponse.ok) {
            const errorData = await loginResponse.json();
            console.log('DEBUG: Login error response:', errorData);
            alert('Error al iniciar sesión: ' + (errorData.detail || 'Intenta de nuevo'));
            return;
        }

        const loginData = await loginResponse.json();
        console.log('DEBUG: Login successful, received data:', loginData);
        localStorage.setItem('token', loginData.access_token);
        console.log('DEBUG: Token stored:', loginData.access_token.substring(0, 10) + '...');
        alert('Usuario creado exitosamente!');
        window.location.href = '/crear_reserva';
    } catch (error) {
        console.error('DEBUG: Error de conexión:', error);
        alert('Error de conexión: ' + error.message);
    }
});