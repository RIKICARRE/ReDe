document.addEventListener('DOMContentLoaded', () => {
    // Elementos del DOM
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const reservaForm = document.getElementById('reserva-form');
    const reservaIdInput = document.getElementById('reserva-id');
    const formTitle = document.getElementById('form-title');
    
    // Elementos de los pasos
    const pasos = {
        1: document.getElementById('paso-1'),
        2: document.getElementById('paso-2'),
        3: document.getElementById('paso-3')
    };
    
    // Elementos de navegación entre pasos
    const steps = {
        1: document.getElementById('step-1'),
        2: document.getElementById('step-2'),
        3: document.getElementById('step-3')
    };
    
    // Estado actual
    let pasoActual = 1;
    let deporteSeleccionado = '';
    let fechaSeleccionada = '';
    let horaSeleccionada = '';
    let reservaEnEdicion = null;
    
    // Horarios disponibles (de 8:00 a 22:00)
    const horariosDisponibles = [];
    for (let i = 8; i <= 21; i++) {
        horariosDisponibles.push(i.toString().padStart(2, '0') + ':00');
    }
    
    // Funciones de utilidad
    function mostrarPaso(numeroPaso) {
        // Ocultar todos los pasos
        Object.values(pasos).forEach(paso => paso.classList.add('hidden'));
        
        // Mostrar el paso actual
        pasos[numeroPaso].classList.remove('hidden');
        
        // Actualizar indicadores visuales
        actualizarIndicadoresPaso(numeroPaso);
        
        pasoActual = numeroPaso;
    }
    
    function actualizarIndicadoresPaso(pasoActivo) {
        Object.keys(steps).forEach(numeroStr => {
            const numero = parseInt(numeroStr);
            const step = steps[numero];
            const circulo = step.querySelector('div');
            const texto = step.querySelector('span');
            
            if (numero <= pasoActivo) {
                // Paso completado o actual
                circulo.classList.remove('bg-gray-300', 'text-gray-600');
                circulo.classList.add('bg-blue-500', 'text-white');
                texto.classList.remove('text-gray-600');
                texto.classList.add('text-blue-500', 'font-medium');
            } else {
                // Paso futuro
                circulo.classList.remove('bg-blue-500', 'text-white');
                circulo.classList.add('bg-gray-300', 'text-gray-600');
                texto.classList.remove('text-blue-500', 'font-medium');
                texto.classList.add('text-gray-600');
            }
        });
    }
    
    function formatearFecha(fechaStr) {
        const fecha = new Date(fechaStr + 'T00:00:00');
        return fecha.toLocaleDateString('es-ES', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
    }
    
    function mostrarError(mensaje) {
        alert(mensaje); // Se puede mejorar con un modal más elegante
    }
    
    function mostrarExito(mensaje) {
        alert(mensaje);
        resetearFormulario();
        window.location.reload();
    }
    
    function mostrarCargando() {
        document.getElementById('loading-modal').classList.remove('hidden');
        document.getElementById('loading-modal').classList.add('flex');
    }
    
    function ocultarCargando() {
        document.getElementById('loading-modal').classList.add('hidden');
        document.getElementById('loading-modal').classList.remove('flex');
    }
    
    function resetearFormulario() {
        pasoActual = 1;
        deporteSeleccionado = '';
        fechaSeleccionada = '';
        horaSeleccionada = '';
        reservaEnEdicion = null;
        reservaIdInput.value = '';
        formTitle.textContent = 'Hacer Nueva Reserva';
        document.getElementById('texto-boton-confirmar').textContent = 'Confirmar Reserva';
        
        // Resetear selecciones visuales
        document.querySelectorAll('.deporte-option').forEach(option => {
            option.classList.remove('border-blue-500', 'bg-blue-50');
            option.classList.add('border-gray-200');
        });
        
        document.getElementById('fecha-reserva').value = '';
        document.getElementById('horarios-grid').innerHTML = '';
        
        mostrarPaso(1);
        document.getElementById('siguiente-paso-1').disabled = true;
    }
    
    // Paso 1: Selección de deporte
    document.querySelectorAll('.deporte-option').forEach(option => {
        option.addEventListener('click', () => {
            // Remover selección anterior
            document.querySelectorAll('.deporte-option').forEach(opt => {
                opt.classList.remove('border-blue-500', 'bg-blue-50');
                opt.classList.add('border-gray-200');
            });
            
            // Seleccionar opción actual
            option.classList.remove('border-gray-200');
            option.classList.add('border-blue-500', 'bg-blue-50');
            
            deporteSeleccionado = option.dataset.deporte;
            document.getElementById('siguiente-paso-1').disabled = false;
        });
    });
    
    document.getElementById('siguiente-paso-1').addEventListener('click', () => {
        if (deporteSeleccionado) {
            mostrarPaso(2);
            // Establecer fecha mínima como hoy
            const hoy = new Date().toISOString().split('T')[0];
            document.getElementById('fecha-reserva').min = hoy;
        }
    });
    
    // Paso 2: Selección de fecha y horario
    document.getElementById('fecha-reserva').addEventListener('change', async (e) => {
        fechaSeleccionada = e.target.value;
        if (fechaSeleccionada) {
            await cargarHorariosDisponibles();
        }
    });
    
    async function cargarHorariosDisponibles() {
        if (!deporteSeleccionado || !fechaSeleccionada) return;
        
        try {
            const response = await fetch('/reservas/horarios-disponibles/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    espacio: deporteSeleccionado,
                    fecha: fechaSeleccionada,
                    reserva_id: reservaEnEdicion // Para excluir la reserva actual en ediciones
                })
            });
            
            const data = await response.json();
            mostrarHorarios(data.horarios_ocupados || []);
            
        } catch (error) {
            console.error('Error al cargar horarios:', error);
            mostrarHorarios([]);
        }
    }
    
    function mostrarHorarios(horariosOcupados) {
        const horariosGrid = document.getElementById('horarios-grid');
        horariosGrid.innerHTML = '';
        
        horariosDisponibles.forEach(horario => {
            const horaBtn = document.createElement('button');
            horaBtn.type = 'button';
            horaBtn.textContent = horario;
            horaBtn.className = 'px-4 py-2 text-sm font-medium rounded-lg border transition-colors';
            
            const ocupado = horariosOcupados.includes(horario);
            
            if (ocupado) {
                horaBtn.className += ' bg-red-100 text-red-600 border-red-200 cursor-not-allowed';
                horaBtn.disabled = true;
                horaBtn.title = 'No disponible';
            } else {
                horaBtn.className += ' bg-white text-gray-700 border-gray-300 hover:bg-blue-50 hover:border-blue-500';
                horaBtn.addEventListener('click', () => seleccionarHora(horario, horaBtn));
            }
            
            horariosGrid.appendChild(horaBtn);
        });
    }
    
    function seleccionarHora(hora, botonElement) {
        // Remover selección anterior
        document.querySelectorAll('#horarios-grid button').forEach(btn => {
            btn.classList.remove('bg-blue-500', 'text-white', 'border-blue-500');
            btn.classList.add('bg-white', 'text-gray-700', 'border-gray-300');
        });
        
        // Seleccionar hora actual
        botonElement.classList.remove('bg-white', 'text-gray-700', 'border-gray-300');
        botonElement.classList.add('bg-blue-500', 'text-white', 'border-blue-500');
        
        horaSeleccionada = hora;
        document.getElementById('siguiente-paso-2').disabled = false;
    }
    
    document.getElementById('atras-paso-2').addEventListener('click', () => {
        mostrarPaso(1);
    });
    
    document.getElementById('siguiente-paso-2').addEventListener('click', () => {
        if (fechaSeleccionada && horaSeleccionada) {
            actualizarResumen();
            mostrarPaso(3);
        }
    });
    
    // Paso 3: Confirmación
    function actualizarResumen() {
        document.getElementById('resumen-deporte').textContent = deporteSeleccionado;
        document.getElementById('resumen-fecha').textContent = formatearFecha(fechaSeleccionada);
        
        const horaFin = (parseInt(horaSeleccionada.split(':')[0]) + 1).toString().padStart(2, '0') + ':00';
        document.getElementById('resumen-horario').textContent = `${horaSeleccionada} - ${horaFin}`;
    }
    
    document.getElementById('atras-paso-3').addEventListener('click', () => {
        mostrarPaso(2);
    });
    
    // Envío del formulario
    reservaForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!deporteSeleccionado || !fechaSeleccionada || !horaSeleccionada) {
            mostrarError('Faltan datos para completar la reserva');
            return;
        }
        
        mostrarCargando();
        
        try {
            const momentoInicio = `${fechaSeleccionada}T${horaSeleccionada}:00`;
            const horaFin = (parseInt(horaSeleccionada.split(':')[0]) + 1).toString().padStart(2, '0');
            const momentoFin = `${fechaSeleccionada}T${horaFin}:00:00`;
            
            const url = reservaEnEdicion ? `/reservas/modificar/${reservaEnEdicion}/` : '/reservas/crear/';
            const method = reservaEnEdicion ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    espacio: deporteSeleccionado,
                    momento_inicio: momentoInicio,
                    momento_fin: momentoFin,
                }),
            });
            
            const data = await response.json();
            
            if (data.error) {
                mostrarError(data.error);
                return;
            }
            
            const mensaje = reservaEnEdicion ? 
                '¡Reserva modificada con éxito!' : 
                '¡Reserva creada con éxito!';
            
            mostrarExito(mensaje);
            
        } catch (error) {
            console.error('Error:', error);
            mostrarError('Ocurrió un error al procesar la solicitud.');
        } finally {
            ocultarCargando();
        }
    });
    
    // Manejo de botones de editar reserva
    document.querySelectorAll('.editar-reserva-btn').forEach(button => {
        button.addEventListener('click', () => {
            const id = button.getAttribute('data-id');
            const espacio = button.getAttribute('data-espacio');
            const fecha = button.getAttribute('data-fecha');
            const hora = button.getAttribute('data-hora');
            
            iniciarEdicion(id, espacio, fecha, hora);
        });
    });
    
    function iniciarEdicion(id, espacio, fecha, hora) {
        reservaEnEdicion = id;
        reservaIdInput.value = id;
        formTitle.textContent = 'Modificar Reserva';
        document.getElementById('texto-boton-confirmar').textContent = 'Guardar Cambios';
        
        // Pre-seleccionar deporte
        deporteSeleccionado = espacio;
        const deporteOption = document.querySelector(`[data-deporte="${espacio}"]`);
        if (deporteOption) {
            document.querySelectorAll('.deporte-option').forEach(opt => {
                opt.classList.remove('border-blue-500', 'bg-blue-50');
                opt.classList.add('border-gray-200');
            });
            deporteOption.classList.remove('border-gray-200');
            deporteOption.classList.add('border-blue-500', 'bg-blue-50');
        }
        
        // Ir al paso 2 y pre-seleccionar fecha
        mostrarPaso(2);
        const fechaInput = document.getElementById('fecha-reserva');
        fechaSeleccionada = fecha;
        fechaInput.value = fecha;
        
        // Cargar horarios y pre-seleccionar hora
        cargarHorariosDisponibles().then(() => {
            setTimeout(() => {
                const horaStr = hora.padStart(2, '0') + ':00';
                const horaBtn = Array.from(document.querySelectorAll('#horarios-grid button'))
                    .find(btn => btn.textContent === horaStr);
                if (horaBtn && !horaBtn.disabled) {
                    seleccionarHora(horaStr, horaBtn);
                }
            }, 100);
        });
    }
    
    // Manejo de botones de eliminar reserva
    document.querySelectorAll('.eliminar-reserva-btn').forEach(button => {
        button.addEventListener('click', async () => {
            const reservaId = button.getAttribute('data-id');
            
            if (confirm('¿Estás seguro de que deseas eliminar esta reserva?')) {
                try {
                    const response = await fetch(`/reservas/eliminar/${reservaId}/`, {
                        method: 'DELETE',
                        headers: {
                            'Content-Type': 'application/json',
                            'X-CSRFToken': csrfToken,
                        },
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        mostrarExito('Reserva eliminada con éxito!');
                    } else {
                        mostrarError('Error al eliminar la reserva.');
                    }
                } catch (error) {
                    console.error('Error al eliminar reserva:', error);
                    mostrarError('Ocurrió un error al eliminar la reserva.');
                }
            }
        });
    });
    
    // Funcionalidad de desplazamiento horizontal para las reservas
    const reservasContainer = document.getElementById('reservas-container');
    const scrollLeftBtn = document.getElementById('scroll-left');
    const scrollRightBtn = document.getElementById('scroll-right');
    
    if (scrollLeftBtn && scrollRightBtn) {
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
        
        // Actualizar visibilidad de botones de scroll
        const toggleScrollButtons = () => {
            if (reservasContainer.scrollLeft > 0) {
                scrollLeftBtn.classList.remove('hidden');
            } else {
                scrollLeftBtn.classList.add('hidden');
            }
            
            if (reservasContainer.scrollLeft + reservasContainer.clientWidth < reservasContainer.scrollWidth) {
                scrollRightBtn.classList.remove('hidden');
            } else {
                scrollRightBtn.classList.add('hidden');
            }
        };
        
        // Inicializar visibilidad
        toggleScrollButtons();
        
        // Escuchar eventos de scroll
        reservasContainer.addEventListener('scroll', toggleScrollButtons);
        window.addEventListener('resize', toggleScrollButtons);
    }
});