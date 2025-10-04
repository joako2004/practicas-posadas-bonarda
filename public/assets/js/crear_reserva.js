document.addEventListener('DOMContentLoaded', async function() {
    console.log('DEBUG: DOMContentLoaded fired');
    const token = localStorage.getItem('token');
    console.log('DEBUG: Token from localStorage:', token ? token.substring(0, 10) + '...' : 'null');
    const reservasList = document.getElementById('reservas');
    const noReservasMsg = document.getElementById('no-reservas');
    const reservaForm = document.getElementById('reserva-form');
    const crearReservaSection = document.querySelector('section:nth-of-type(2)');

    // Validate token
     async function validateToken() {
         try {
             const response = await fetch('/api/reservas', {
                 method: 'GET',
                 headers: {
                     'Authorization': `Bearer ${token}`,
                     'Content-Type': 'application/json'
                 }
             });
             console.log('DEBUG: Token validation response status:', response.status);
             return response.ok;
         } catch (err) {
             console.error('DEBUG: Token validation failed:', err);
             return false;
         }
     }

    if (!token || !(await validateToken())) {
        console.log('DEBUG: No token or invalid token, showing login message');
        noReservasMsg.textContent = 'Debes iniciar sesión para ver tus reservas y crear nuevas.';
        noReservasMsg.style.display = 'block';
        reservasList.style.display = 'none';
        if (crearReservaSection) crearReservaSection.style.display = 'none';
        alert('Sesión no iniciada o expirada. Redirigiendo al login.');
        window.location.href = '/crear_usuario';
        return;
    }

    // Show form since logged in
    if (crearReservaSection) crearReservaSection.style.display = 'block';

    try {
        const response = await fetch('/api/reservas', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            if (response.status === 401 || response.status === 403) {
                console.log('DEBUG: Unauthorized or Forbidden, redirecting to login');
                localStorage.removeItem('token');
                alert('Sesión expirada. Por favor, inicia sesión nuevamente.');
                window.location.href = '/crear_usuario';
                return;
            }
            throw new Error('Error al obtener reservas');
        }

        const reservas = await response.json();

        if (reservas.length === 0) {
            noReservasMsg.style.display = 'block';
            reservasList.style.display = 'none';
        } else {
            noReservasMsg.style.display = 'none';
            reservasList.style.display = 'block';
            reservasList.innerHTML = '';

            reservas.forEach(reserva => {
                const li = document.createElement('li');
                li.textContent = `ID: ${reserva.id}, Fechas: ${reserva.fecha_check_in} a ${reserva.fecha_check_out}, Habitaciones: ${reserva.cantidad_habitaciones}, Estado: ${reserva.estado}, Precio: $${reserva.precio_total}`;
                reservasList.appendChild(li);
            });
        }
    } catch (error) {
        console.error('DEBUG: Error fetching reservations:', error);
        noReservasMsg.textContent = 'Error al cargar reservas. Intenta de nuevo.';
        noReservasMsg.style.display = 'block';
        reservasList.style.display = 'none';
    }

    // Handle reservation form submission
    if (reservaForm) {
        reservaForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            console.log('DEBUG: Form submission triggered');

            const formData = new FormData(reservaForm);
            const reservaData = {
                fecha_check_in: formData.get('fecha_check_in') + 'T00:00:00',
                fecha_check_out: formData.get('fecha_check_out') + 'T00:00:00',
                cantidad_habitaciones: parseInt(formData.get('cantidad_habitaciones'))
            };

            console.log('DEBUG: Reservation data to send:', reservaData);

            try {
                const response = await fetch('/api/reservas', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(reservaData)
                });

                console.log('DEBUG: API response status:', response.status);

                if (!response.ok) {
                    const errorData = await response.json();
                    console.error('DEBUG: API error response:', errorData);
                    if (response.status === 401 || response.status === 403) {
                        localStorage.removeItem('token');
                        alert('Sesión expirada. Por favor, inicia sesión nuevamente.');
                        window.location.href = '/crear_usuario';
                        return;
                    }
                    throw new Error(`Error: ${response.status} - ${errorData.detail || 'Error desconocido'}`);
                }

                const nuevaReserva = await response.json();
                console.log('DEBUG: New reservation created:', nuevaReserva);
                alert('Reserva enviada. La administración te contactará vía WhatsApp.');
                location.reload();
            } catch (error) {
                console.error('DEBUG: Error creating reservation:', error);
                alert('Error al crear reserva: ' + error.message);
            }
        });
    } else {
        console.error('DEBUG: Reservation form not found');
    }
});