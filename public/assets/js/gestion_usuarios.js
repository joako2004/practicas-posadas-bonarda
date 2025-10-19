document.addEventListener('DOMContentLoaded', function() {
    loadUsers();
});

async function loadUsers() {
    const loadingMessage = document.getElementById('loading-message');
    const errorMessage = document.getElementById('error-message');
    const tableBody = document.getElementById('users-table-body');

    // Show loading message
    loadingMessage.style.display = 'block';
    errorMessage.style.display = 'none';
    tableBody.innerHTML = '';

    try {
        const response = await fetch('/api/usuarios', {
            method: 'GET'
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al cargar usuarios');
        }

        const users = await response.json();

        // Hide loading message
        loadingMessage.style.display = 'none';

        // Populate table
        if (users.length === 0) {
            tableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 20px;">No hay usuarios registrados</td></tr>';
            return;
        }

        users.forEach(user => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${user.id}</td>
                <td>${user.nombre} ${user.apellido}</td>
                <td>${user.email}</td>
                <td>
                    <button class="edit-btn" onclick="editUser(${user.id}, '${user.nombre}', '${user.apellido}', '${user.email}')">Editar</button>
                    <button class="delete-btn" onclick="deleteUser(${user.id}, '${user.nombre} ${user.apellido}')">Eliminar</button>
                </td>
            `;
            tableBody.appendChild(row);
        });

    } catch (error) {
        loadingMessage.style.display = 'none';
        showError('Error de conexión: ' + error.message);
    }
}

async function deleteUser(userId, userName) {
    console.log('deleteUser called with userId:', userId, 'userName:', userName);
    if (!confirm(`¿Estás seguro de que quieres eliminar al usuario "${userName}"?`)) {
        console.log('User cancelled delete operation');
        return;
    }

    console.log('Sending DELETE request to:', `/api/usuarios/${userId}`);
    try {
        const response = await fetch(`/api/usuarios/${userId}`, {
            method: 'DELETE'
        });

        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);

        if (!response.ok) {
            const errorData = await response.json();
            console.log('Error data:', errorData);
            throw new Error(errorData.detail || 'Error al eliminar usuario');
        }

        const result = await response.json();
        console.log('Success result:', result);
        alert(result.message || 'Usuario eliminado exitosamente');

        // Reload the users list
        loadUsers();

    } catch (error) {
        console.log('Error in deleteUser:', error);
        alert('Error al eliminar usuario: ' + error.message);
    }
}

function editUser(userId, userName, userApellido, userEmail) {
    document.getElementById('edit-user-id').value = userId;
    document.getElementById('edit-nombre').value = userName;
    document.getElementById('edit-apellido').value = userApellido;
    document.getElementById('edit-email').value = userEmail;
    document.getElementById('edit-modal').style.display = 'flex';
}

async function saveUser(event) {
    event.preventDefault();
    const userId = document.getElementById('edit-user-id').value;
    const nombre = document.getElementById('edit-nombre').value.trim();
    const apellido = document.getElementById('edit-apellido').value.trim();
    const email = document.getElementById('edit-email').value.trim();

    // Validation
    if (!nombre || !apellido || !email) {
        alert('Todos los campos son obligatorios.');
        return;
    }
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
        alert('Por favor, ingresa un email válido.');
        return;
    }

    try {
        const response = await fetch(`/api/usuarios/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ nombre, apellido, email })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Error al actualizar usuario');
        }

        const result = await response.json();
        alert(result.message || 'Usuario actualizado exitosamente');
        closeEditModal();
        loadUsers();

    } catch (error) {
        alert('Error al actualizar usuario: ' + error.message);
    }
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

function cancelEdit() {
    document.getElementById('edit-modal').style.display = 'none';
}

document.getElementById('edit-form').addEventListener('submit', saveUser);

function showError(message) {
    const loadingMessage = document.getElementById('loading-message');
    const errorMessage = document.getElementById('error-message');

    loadingMessage.style.display = 'none';
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}