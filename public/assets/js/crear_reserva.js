
// Verificar si el usuario está autenticado
const token = localStorage.getItem('token');
if (!token) {
    window.location.href = 'crear_usuario.html'; // Redirigir si no hay token
}

// Botón de cerrar sesión
const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        window.location.href = 'crear_usuario.html';
    });
}

// Formatear fechas para mostrar
const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('es-ES', {
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });
};

// Cargar reservas existentes
async function cargarReservas() {
    const lista = document.getElementById('reservas');
    const noReservas = document.getElementById('no-reservas');
    if (!lista || !noReservas) {
        console.error('Elementos del DOM no encontrados');
        return;
    }

    try {
        noReservas.textContent = 'Cargando reservas...';
        const res = await axios.get('/api/reservas', {
            headers: { Authorization: `Bearer ${token}` }
        });
        const reservas = res.data;

        if (reservas.length === 0) {
            noReservas.style.display = 'block';
            noReservas.textContent = 'No tienes reservas aún.';
            lista.innerHTML = '';
        } else {
            noReservas.style.display = 'none';
            let html = '';
            reservas.forEach(r => {
                html += `<li>Reserva del ${formatDate(r.fecha_entrada)} al ${formatDate(r.fecha_salida)} - ${r.huespedes} huéspedes</li>`;
            });
            lista.innerHTML = html;
        }
    } catch (err) {
        console.error('Error cargando reservas:', err);
        if (err.response && (err.response.status === 401 || err.response.status === 403)) {
            localStorage.removeItem('token');
            window.location.href = 'crear_usuario.html';
            return;
        }
        noReservas.style.display = 'block';
        noReservas.textContent = 'Error al cargar reservas.';
    }
}
cargarReservas();

// Manejar submit del formulario
const form = document.getElementById('reserva-form');
if (form) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(e.target);
        const data = Object.fromEntries(formData);

        // Validación de fechas
        const hoy = new Date();
        hoy.setHours(0, 0, 0, 0);
        if (new Date(data.fecha_entrada) < hoy) {
            alert('La fecha de entrada no puede ser anterior a hoy.');
            return;
        }
        if (new Date(data.fecha_salida) <= new Date(data.fecha_entrada)) {
            alert('La fecha de salida debe ser posterior a la fecha de entrada.');
            return;
        }

        try {
            await axios.post('/api/reservas', data, {
                headers: { Authorization: `Bearer ${token}` }
            });
            alert('Reserva enviada. La administración te contactará vía WhatsApp.');
            cargarReservas(); // Recargar lista
            e.target.reset(); // Limpiar formulario
        } catch (err) {
            console.error('Error enviando reserva:', err);
            let errorMsg = 'Error al enviar la reserva. Intenta de nuevo.';
            if (err.response && err.response.data.error) {
                errorMsg = err.response.data.error;
            }
            if (err.response && (err.response.status === 401 || err.response.status === 403)) {
                localStorage.removeItem('token');
                window.location.href = 'crear_usuario.html';
                return;
            }
            alert(errorMsg);
        }
    });
}
