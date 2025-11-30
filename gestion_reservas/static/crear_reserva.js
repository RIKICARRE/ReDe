document.addEventListener('DOMContentLoaded', () => {
  const momentoInicioInput = document.getElementById('momento_inicio');
  const momentoFinInput = document.getElementById('momento_fin');
  const reservaForm = document.getElementById('crear-reserva-form');
  const reservaIdInput = document.getElementById('reserva-id');
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
  
  // Función para actualizar el campo de fin a una hora después del inicio
  const actualizarMomentoFin = () => {
      const inicioValue = momentoInicioInput.value;
      if (inicioValue) {
          const inicioDate = new Date(inicioValue);
          if (isNaN(inicioDate.getTime())) {
              // Fecha inválida
              momentoFinInput.value = '';
              return;
          }
          const finDate = new Date(inicioDate.getTime() + 60 * 60 * 1000); // Añade 1 hora

          // Formatea la fecha al formato 'YYYY-MM-DDTHH:MM' para datetime-local
          const year = finDate.getFullYear();
          const month = String(finDate.getMonth() + 1).padStart(2, '0');
          const day = String(finDate.getDate()).padStart(2, '0');
          const hours = String(finDate.getHours()).padStart(2, '0');
          const minutes = String(finDate.getMinutes()).padStart(2, '0');

          const finFormatted = `${year}-${month}-${day}T${hours}:${minutes}`;
          momentoFinInput.value = finFormatted;
      } else {
          momentoFinInput.value = '';
      }
  };

  // Escuchar cambios en el campo de inicio
  momentoInicioInput.addEventListener('change', actualizarMomentoFin);

  // Verificar si hay parámetros en la URL para editar una reserva
  const urlParams = new URLSearchParams(window.location.search);
  const reservaId = urlParams.get('id');
  const inicio = urlParams.get('inicio');
  const fin = urlParams.get('fin');
  const espacio = urlParams.get('espacio');

  // Si hay parámetros, llenar el formulario con ellos
  if (reservaId && inicio && fin && espacio) {
      reservaIdInput.value = reservaId;
      momentoInicioInput.value = inicio;
      momentoFinInput.value = fin;
      document.getElementById('espacio').value = espacio;
  }

  // Manejar el envío del formulario
  reservaForm.addEventListener('submit', (e) => {
      e.preventDefault();

      const reservaId = reservaIdInput.value;
      const url = reservaId ? `/reservas/modificar/${reservaId}/` : '/reservas/crear/';
      const method = reservaId ? 'PUT' : 'POST';

      const espacio = document.getElementById('espacio').value;
      const momento_inicio = momentoInicioInput.value;
      const momento_fin = momentoFinInput.value;

      fetch(url, {
          method: method,
          headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': csrfToken,
          },
          body: JSON.stringify({
              espacio: espacio,
              momento_inicio: momento_inicio,
              momento_fin: momento_fin,
          }),
      })
      .then(response => response.json())
      .then(data => {
          if (data.error) {
              alert(data.error);
              return;
          }
          if (reservaId) {
              alert("Reserva actualizada con éxito!");
          } else {
              alert("Reserva creada con éxito!");
          }
          // Redirigir a la página de mis reservas
          window.location.href = '/reservas/';
      })
      .catch(error => {
          console.error('Error:', error);
          alert("Ocurrió un error al procesar la solicitud.");
      });
  });
});