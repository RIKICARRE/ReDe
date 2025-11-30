document.addEventListener('DOMContentLoaded', () => {
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

  // Manejar la edición de reservas
  const editarReservaButtons = document.querySelectorAll('.editar-reserva-btn');
  editarReservaButtons.forEach(button => {
      button.addEventListener('click', () => {
          const reservaId = button.getAttribute('data-id');
          const inicio = button.getAttribute('data-momento_inicio');
          const fin = button.getAttribute('data-momento_fin');
          const espacio = button.getAttribute('data-espacio');
          
          // Redirigir a la página de crear reserva con los parámetros
          window.location.href = `/reservas/hacer/?id=${reservaId}&inicio=${inicio}&fin=${fin}&espacio=${espacio}`;
      });
  });

  // Manejar la eliminación de reservas
  const eliminarReservaButtons = document.querySelectorAll('.eliminar-reserva-btn');
  eliminarReservaButtons.forEach(button => {
      button.addEventListener('click', () => {
          const reservaId = button.getAttribute('data-id');
          if (confirm('¿Estás seguro de que deseas eliminar esta reserva?')) {
              fetch(`/reservas/eliminar/${reservaId}/`, {
                  method: 'DELETE',
                  headers: {
                      'Content-Type': 'application/json',
                      'X-CSRFToken': csrfToken,
                  },
              })
              .then(response => response.json())
              .then(data => {
                  if (data.success) {
                      alert("Reserva eliminada con éxito!");
                      window.location.reload(); // Recargar la página para actualizar la lista
                  } else {
                      alert('Error al eliminar la reserva.');
                  }
              })
              .catch(error => {
                  console.error('Error al eliminar reserva:', error);
                  alert("Ocurrió un error al eliminar la reserva.");
              });
          }
      });
  });

  // Funcionalidad de desplazamiento horizontal
  const reservasContainer = document.getElementById('reservas-container');
  const scrollLeftBtn = document.getElementById('scroll-left');
  const scrollRightBtn = document.getElementById('scroll-right');

  // Definir la cantidad de desplazamiento (en píxeles)
  const scrollAmount = 300;

  scrollLeftBtn.addEventListener('click', () => {
      reservasContainer.scrollBy({
          top: 0,
          left: -scrollAmount,
          behavior: 'smooth'
      });
  });

  scrollRightBtn.addEventListener('click', () => {
      reservasContainer.scrollBy({
          top: 0,
          left: scrollAmount,
          behavior: 'smooth'
      });
  });

  // Opcional: Mostrar/ocultar botones según el scroll
  const toggleScrollButtons = () => {
      // Mostrar botón izquierdo si no está al inicio
      if (reservasContainer.scrollLeft > 0) {
          scrollLeftBtn.classList.remove('hidden');
      } else {
          scrollLeftBtn.classList.add('hidden');
      }

      // Mostrar botón derecho si no está al final
      if (reservasContainer.scrollLeft + reservasContainer.clientWidth < reservasContainer.scrollWidth) {
          scrollRightBtn.classList.remove('hidden');
      } else {
          scrollRightBtn.classList.add('hidden');
      }
  };

  // Inicializar la visibilidad de los botones
  toggleScrollButtons();

  // Escuchar eventos de scroll para actualizar la visibilidad de los botones
  reservasContainer.addEventListener('scroll', toggleScrollButtons);
  window.addEventListener('resize', toggleScrollButtons);
});