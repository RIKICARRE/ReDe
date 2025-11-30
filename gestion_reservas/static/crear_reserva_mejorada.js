document.addEventListener('DOMContentLoaded', () => {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const form = document.getElementById('reserva-form');
    const reservaIdInput = document.getElementById('reserva-id');
    const cancelarBtn = document.getElementById('cancelar-flujo');

    // Pasos
    const pasos = {1: document.getElementById('paso-1'),2: document.getElementById('paso-2'),3: document.getElementById('paso-3')};
    const stepIndicators = {1: document.getElementById('step-1'),2: document.getElementById('step-2'),3: document.getElementById('step-3')};

    let pasoActual = 1;
    let deporte = '';
    let fecha = '';
    let hora = '';

    const horas = Array.from({length: 14}, (_,i)=> (i+8).toString().padStart(2,'0')+':00');

    function mostrarPaso(n){
        Object.values(pasos).forEach(p=>p.classList.add('hidden'));
        pasos[n].classList.remove('hidden');
        actualizarIndicadores(n);
        pasoActual = n;
    }
    function actualizarIndicadores(activo){
        Object.entries(stepIndicators).forEach(([n,el])=>{
            const circle = el.querySelector('div');
            const text = el.querySelector('span');
            if(parseInt(n) <= activo){
                circle.classList.remove('bg-gray-300','text-gray-600');
                circle.classList.add('bg-blue-500','text-white');
                text.classList.add('text-blue-500','font-medium');
                text.classList.remove('text-gray-600');
            } else {
                circle.classList.add('bg-gray-300','text-gray-600');
                circle.classList.remove('bg-blue-500','text-white');
                text.classList.remove('text-blue-500','font-medium');
                text.classList.add('text-gray-600');
            }
        });
    }
    function formatearFecha(f){
        const d = new Date(f+'T00:00:00');
        return d.toLocaleDateString('es-ES',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
    }
    function error(msg){ alert(msg);} // TODO: reemplazar por toast
    function exito(msg){ alert(msg); window.location.href='/mis-reservas/?ok=1'; }
    function showLoading(){ const m=document.getElementById('loading-modal'); m.classList.remove('hidden'); m.classList.add('flex'); }
    function hideLoading(){ const m=document.getElementById('loading-modal'); m.classList.add('hidden'); m.classList.remove('flex'); }

    // Ya es un enlace directo. Refuerzo: si se quisiera interceptar para confirmar:
    if(cancelarBtn){
        cancelarBtn.addEventListener('click', (e)=>{
            // Opcional: confirmación suave (descomentar si se quiere preguntar)
            // if(!confirm('¿Cancelar el proceso de reserva?')) { e.preventDefault(); }
        });
    }

    // Selección deporte
    document.querySelectorAll('.deporte-option').forEach(opt=>{
        opt.addEventListener('click',()=>{
            document.querySelectorAll('.deporte-option').forEach(o=>o.classList.remove('selected','border-blue-500'));
            opt.classList.add('selected','border-blue-500');
            deporte = opt.dataset.deporte;
            document.getElementById('siguiente-paso-1').disabled = false;
        });
    });
    document.getElementById('siguiente-paso-1').addEventListener('click',()=>{
        if(!deporte) return;
        mostrarPaso(2);
        const hoy = new Date().toISOString().split('T')[0];
        const inputFecha = document.getElementById('fecha-reserva');
        inputFecha.min = hoy;
        if(!inputFecha.value) inputFecha.value = hoy;
        if(inputFecha.value){ fecha = inputFecha.value; cargarHorariosDisponibles(getUrlParam('hora')); }
    });

    document.getElementById('fecha-reserva').addEventListener('change',e=>{ fecha = e.target.value; if(fecha) cargarHorariosDisponibles(); });

    async function cargarHorariosDisponibles(preselectHora=null){
        if(!deporte || !fecha) return;
        const grid = document.getElementById('horarios-grid');
        grid.innerHTML = '<div class="col-span-full text-sm text-gray-500">Cargando...</div>';
        try{
            const resp = await fetch('/reservas/horarios-disponibles/',{
                method:'POST',
                headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken},
                body: JSON.stringify({espacio:deporte,fecha:fecha,reserva_id: reservaIdInput.value || null})
            });
            const data = await resp.json();
            renderHoras(data.horarios_ocupados||[], preselectHora || getUrlParam('hora'));
        }catch(e){ console.error(e); renderHoras([], preselectHora); }
    }
    function renderHoras(ocupados, preselect){
        const grid = document.getElementById('horarios-grid');
        grid.innerHTML='';
        horas.forEach(h=>{
            const b=document.createElement('button');
            b.type='button';
            b.textContent=h;
            b.dataset.hora=h;
            b.className='px-4 py-2 text-sm font-medium rounded-lg border transition-colors';
            if(ocupados.includes(h)){
                b.disabled=true; b.className+=' bg-red-100 text-red-600 border-red-200 cursor-not-allowed'; b.title='No disponible';
            } else {
                b.className+=' bg-white text-gray-700 border-gray-300 hover:bg-blue-50 hover:border-blue-500';
                b.addEventListener('click',()=> seleccionarHora(h,b));
            }
            grid.appendChild(b);
        });
        if(preselect){
            const norm = preselect.length===5? preselect : preselect.padStart(5,'0');
            const target = Array.from(grid.querySelectorAll('button')).find(btn=> btn.dataset.hora===norm);
            if(target && !target.disabled){ seleccionarHora(norm,target); }
        }
    }
    function seleccionarHora(h, btn){
        document.querySelectorAll('#horarios-grid button').forEach(b=>{ if(!b.disabled){ b.classList.remove('bg-blue-500','text-white','border-blue-500'); b.classList.add('bg-white','text-gray-700','border-gray-300'); }});
        btn.classList.remove('bg-white','text-gray-700','border-gray-300');
        btn.classList.add('bg-blue-500','text-white','border-blue-500');
        hora = h;
        document.getElementById('siguiente-paso-2').disabled = false;
    }

    document.getElementById('atras-paso-2').addEventListener('click',()=> mostrarPaso(1));
    document.getElementById('siguiente-paso-2').addEventListener('click',()=>{ if(fecha && hora){ actualizarResumen(); mostrarPaso(3);} });
    document.getElementById('atras-paso-3').addEventListener('click',()=> mostrarPaso(2));

    function actualizarResumen(){
        document.getElementById('resumen-deporte').textContent = deporte;
        document.getElementById('resumen-fecha').textContent = formatearFecha(fecha);
        const horaFin = (parseInt(hora.split(':')[0])+1).toString().padStart(2,'0')+':00';
        document.getElementById('resumen-horario').textContent = `${hora} - ${horaFin}`;
    }

    form.addEventListener('submit', async e=>{
        e.preventDefault();
        if(!deporte || !fecha || !hora){ return error('Faltan datos para completar la reserva'); }
        showLoading();
        try{
            const inicio = `${fecha}T${hora}:00`;
            const horaFin = (parseInt(hora.split(':')[0])+1).toString().padStart(2,'0');
            const fin = `${fecha}T${horaFin}:00:00`;
            const esEdicion = !!reservaIdInput.value;
            const url = esEdicion? `/reservas/modificar/${reservaIdInput.value}/` : '/reservas/crear/';
            const method = esEdicion? 'PUT':'POST';
            const resp = await fetch(url,{method,headers:{'Content-Type':'application/json','X-CSRFToken':csrfToken},body: JSON.stringify({espacio:deporte,momento_inicio:inicio,momento_fin:fin})});
            const data = await resp.json();
            if(data.error) return error(data.error);
            exito(esEdicion? 'Reserva modificada con éxito' : 'Reserva creada con éxito');
        }catch(err){ console.error(err); error('Error procesando la solicitud'); } finally { hideLoading(); }
    });

    function getUrlParam(key){ return new URLSearchParams(window.location.search).get(key); }
    // Modo edición
    if(getUrlParam('id')){
        reservaIdInput.value = getUrlParam('id');
        const esp = getUrlParam('espacio');
        const fec = getUrlParam('fecha');
        const hor = getUrlParam('hora');
        if(esp){ const o=document.querySelector(`[data-deporte="${esp}"]`); if(o){ o.click(); } }
        if(fec){ fecha = fec; document.getElementById('fecha-reserva').value = fec; mostrarPaso(2); cargarHorariosDisponibles(hor); }
    }
});