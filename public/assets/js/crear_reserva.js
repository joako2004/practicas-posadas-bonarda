document.addEventListener('DOMContentLoaded', async function() {
    const token = localStorage.getItem('token');
    const reservasList = document.getElementById('reservas');
    const noReservasMsg = document.getElementById('no-reservas');

    if (!token) {
        // No token, perhaps show message or redirect
        noReservasMsg.textContent = 'Debes iniciar sesión para ver tus reservas.';
        noReservasMsg.style.display = 'block';
        return;
    }

    try {
        const response = await fetch('/api/reservas', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Error al obtener reservas');
        }

        const reservas = await response.json();

        if (reservas.length === 0) {
            noReservasMsg.style.display = 'block';
            reservasList.style.display = 'none';
        } else {
            noReservasMsg.style.display = 'none';
            reservasList.style.display = 'block';
            reservasList.innerHTML = ''; // Clear any existing

            reservas.forEach(reserva => {
                const li = document.createElement('li');
                li.textContent = `ID: ${reserva.id}, Fechas: ${reserva.fecha_check_in} a ${reserva.fecha_check_out}, Habitaciones: ${reserva.cantidad_habitaciones}, Estado: ${reserva.estado}, Precio: $${reserva.precio_total}`;
                reservasList.appendChild(li);
            });
        }
    } catch (error) {
        console.error('Error fetching reservations:', error);
        noReservasMsg.textContent = 'Error al cargar reservas. Intenta de nuevo.';
        noReservasMsg.style.display = 'block';
        reservasList.style.display = 'none';
    }
});