const area = document.getElementById('area');
let componentes = [];
let conexoes = [];
let pifs = [];
let idCount = 0;
let pifCount = 0;
let ligandoDe = null;
let selectedComponent = null;
let pifAtivo = null; // Para saber qual PIF está sendo editado

const deleteBtn = document.getElementById('delete-btn');
const clearBtn = document.getElementById('clear-btn');
const calculateBtn = document.getElementById('calculate-btn');
const modal = document.getElementById('properties-modal');
const propertiesForm = document.getElementById('properties-form');

function selecionarComponente(el) {
    if (selectedComponent) selectedComponent.classList.remove('selected');
    selectedComponent = el;
    if (selectedComponent) {
        selectedComponent.classList.add('selected');
        if (deleteBtn) deleteBtn.disabled = false;
    } else {
        if (deleteBtn) deleteBtn.disabled = true;
    }
}

function criarComp(tipo) {
    const div = document.createElement('div'); 
    // Usamos uma classe genérica para o design quadrado
    div.classList.add('draggable-component');

    const id = "C" + (idCount++);
    div.dataset.id = id;
    div.dataset.tipo = tipo;
    div.style.left = (60 + (componentes.length * 20)) + 'px';
    div.style.top = (60 + (componentes.length * 10)) + 'px';
    
    const icons = {
        "bomba": "💧", "caldeira": "🔥", "reaquecedor": "🔥",
        "turbina": "⚙️", "condensador": "🔄", "TrocadorDeCalor": "🔄",
        "compressor": "🌀"
    };

    // Novo design: Ícone acima e nome abaixo
    div.innerHTML = `
        <div class="comp-icon">${icons[tipo] || ""}</div>
        <div class="comp-name">${tipo}</div>
        <div class='ponto'></div>
    `;

    const p = div.querySelector('.ponto');
    p.addEventListener('click', (e) => {
        e.stopPropagation();
        if (!ligandoDe) {
            ligandoDe = div;
            p.style.background = 'orange';
        } else {
            if (ligandoDe !== div) adicionarConexao(ligandoDe, div);
            const prevP = ligandoDe.querySelector('.ponto');
            if (prevP) prevP.style.background = 'red';
            ligandoDe = null;
        }
    });

    div.addEventListener('mousedown', () => selecionarComponente(div));
    arrastar(div);
    area.appendChild(div);
    componentes.push(div);
    selecionarComponente(div);
}

function arrastar(el) {
    let offsetX, offsetY;
    el.onmousedown = function(e) {
        if (e.target.classList.contains('ponto')) return;
        selecionarComponente(el);
        offsetX = e.clientX - parseInt(el.style.left || 0);
        offsetY = e.clientY - parseInt(el.style.top || 0);
        document.onmousemove = function(e2) {
            el.style.left = (e2.clientX - offsetX) + 'px';
            el.style.top = (e2.clientY - offsetY) + 'px';
            atualizarLinhas();
            atualizarPIFs();
        }
        document.onmouseup = () => document.onmousemove = null;
    }
}

function adicionarConexao(a, b) {
    const idA = a.dataset.id, idB = b.dataset.id;
    if (conexoes.some(c => c[0] === idA && c[1] === idB)) return;
    conexoes.push([idA, idB]);
    desenharLinha(a, b);
    criarPIF(a, b);
}

function desenharLinha(a, b) {
    const svg = document.getElementById('linhas');
    const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
    line.dataset.a = a.dataset.id;
    line.dataset.b = b.dataset.id;
    line.setAttribute("stroke", "black");
    line.setAttribute('stroke-width', '2');
    svg.appendChild(line);
    atualizarLinhas();
}

function criarPIF(a, b) {
    const pif = document.createElement('div');
    const id = "PIF" + (pifCount++);
    pif.className = 'pif';
    pif.dataset.id = id;
    pif.dataset.pa = a.dataset.id;
    pif.dataset.pb = b.dataset.id;
    pif.dataset.pressao = ""; pif.dataset.temp = ""; pif.dataset.titulo = "";
    pif.innerHTML = "P";

    pif.addEventListener('click', (e) => {
        e.stopPropagation();
        abrirModal(pif);
    });

    area.appendChild(pif);
    pifs.push(pif);
    atualizarPIFs();
}

function abrirModal(pif) {
    pifAtivo = pif;
    document.getElementById('modal-p').value = pif.dataset.pressao;
    document.getElementById('modal-t').value = pif.dataset.temp;
    document.getElementById('modal-q').value = pif.dataset.titulo;
    modal.classList.add('active');
}

function fecharModal() {
    modal.classList.remove('active');
    pifAtivo = null;
}

propertiesForm.onsubmit = (e) => {
    e.preventDefault();
    if (pifAtivo) {
        pifAtivo.dataset.pressao = document.getElementById('modal-p').value;
        pifAtivo.dataset.temp = document.getElementById('modal-t').value;
        pifAtivo.dataset.titulo = document.getElementById('modal-q').value;
    }
    fecharModal();
};

document.querySelector('.close-button').onclick = fecharModal;
document.querySelector('.cancel-btn').onclick = fecharModal;

function atualizarLinhas() {
    const svg = document.getElementById('linhas');
    svg.querySelectorAll('line').forEach(line => {
        const a = componentes.find(c => c.dataset.id === line.dataset.a);
        const b = componentes.find(c => c.dataset.id === line.dataset.b);
        if (!a || !b) return;
        line.setAttribute('x1', a.offsetLeft + a.offsetWidth / 2);
        line.setAttribute('y1', a.offsetTop + a.offsetHeight / 2);
        line.setAttribute('x2', b.offsetLeft + b.offsetWidth / 2);
        line.setAttribute('y2', b.offsetTop + b.offsetHeight / 2);
    });
}

function atualizarPIFs() {
    pifs.forEach(pif => {
        const a = componentes.find(c => c.dataset.id === pif.dataset.pa);
        const b = componentes.find(c => c.dataset.id === pif.dataset.pb);
        if (!a || !b) return;
        const ax = a.offsetLeft + a.offsetWidth / 2, ay = a.offsetTop + a.offsetHeight / 2;
        const bx = b.offsetLeft + b.offsetWidth / 2, by = b.offsetTop + b.offsetHeight / 2;
        pif.style.left = ((ax + bx) / 2 - (pif.offsetWidth / 2)) + 'px';
        pif.style.top = ((ay + by) / 2 - (pif.offsetHeight / 2)) + 'px';
    });
}

function buildJSON() {
    const comps = componentes.map(c => ({ id: c.dataset.id, type: c.dataset.tipo, x: parseInt(c.style.left || 0), y: parseInt(c.style.top || 0) }));
    const pifJson = pifs.map(p => ({ id: p.dataset.id, from: p.dataset.pa, to: p.dataset.pb, pressao: p.dataset.pressao, temperatura: p.dataset.temp, titulo: p.dataset.titulo }));
    const selectFluido = document.getElementById('workingFluid');
    const temCompressor = componentes.some(c => c.dataset.tipo === 'compressor');

    return { 
        components: comps, connections: conexoes, pifs: pifJson,
        fluido: selectFluido.value,
        densidade: parseFloat(selectFluido.options[selectFluido.selectedIndex].dataset.density),
        tipoCiclo: temCompressor ? "Brayton" : "Rankine"
    };
}

async function processarNoBackend() {
    const data = buildJSON();
    try {
        const resposta = await fetch("/processar-circuito", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data) });
        if (!resposta.ok) { alert("Erro ao processar o circuito."); return; }
        const blob = await resposta.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `relatorio_ciclo_${data.tipoCiclo.toLowerCase()}.pdf`;
        document.body.appendChild(a); a.click(); document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        alert("Relatório gerado com sucesso!");
    } catch (err) { alert("Erro na comunicação com o servidor."); }
}

if (deleteBtn) {
    deleteBtn.addEventListener('click', () => {
        if (selectedComponent) {
            const id = selectedComponent.dataset.id;
            conexoes = conexoes.filter(c => c[0] !== id && c[1] !== id);
            const svg = document.getElementById('linhas');
            svg.querySelectorAll(`line[data-a="${id}"], line[data-b="${id}"]`).forEach(l => l.remove());
            pifs = pifs.filter(p => {
                if (p.dataset.pa === id || p.dataset.pb === id) { p.remove(); return false; }
                return true;
            });
            componentes = componentes.filter(c => c.dataset.id !== id);
            selectedComponent.remove();
            selecionarComponente(null);
        }
    });
}

if (clearBtn) {
    clearBtn.addEventListener('click', () => {
        if (confirm("Deseja limpar toda a área de montagem?")) {
            componentes.forEach(c => c.remove());
            pifs.forEach(p => p.remove());
            document.getElementById('linhas').innerHTML = '';
            componentes = []; conexoes = []; pifs = [];
            selecionarComponente(null);
        }
    });
}

area.addEventListener('click', (e) => {
    if (e.target === area || e.target.id === 'linhas') selecionarComponente(null);
});

document.getElementById('btnBomba').addEventListener('click', () => criarComp('bomba'));
document.getElementById('btnCaldeira').addEventListener('click', () => criarComp('caldeira'));
document.getElementById('btnTurbina').addEventListener('click', () => criarComp('turbina'));
document.getElementById('btnCondensador').addEventListener('click', () => criarComp('condensador'));
document.getElementById('btnReaquecedor').addEventListener('click', () => criarComp('reaquecedor'));
document.getElementById('btnTrocaCalor').addEventListener('click', () => criarComp('TrocadorDeCalor'));
document.getElementById('btnCompressor').addEventListener('click', () => criarComp('compressor'));

if (calculateBtn) calculateBtn.addEventListener('click', processarNoBackend);
