let bloqueado = false;
const TEMPO_BLOQUEIO = 5000; // 5 segundos
const TEMPO_FEEDBACK = 4000; // 4 segundos para mostrar feedback

async function votar(grau) {
    // Impedir múltiplos cliques
    if (bloqueado) {
        showMensagem("Aguarde...", "carregando");
        return;
    }
    
    bloqueado = true;
    
    // Desabilitar todos os botões
    disableBotoes(true);
    
    // Mostrar mensagem de carregamento
    showMensagem("Enviando sua resposta...", "carregando");

    try {
        const response = await fetch("/votar", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ grau })
        });

        const data = await response.json();

        if (response.ok) {
            showMensagem("✅ Voto registado com sucesso! Obrigado.", "sucesso");
        } else {
            showMensagem("❌ Erro ao registar a resposta. Tente novamente.", "erro");
        }
    } catch (error) {
        console.error("Erro:", error);
        showMensagem("❌ Erro de conexão. Tente novamente.", "erro");
    }

    // Voltar a habilitar após o tempo de bloqueio
    setTimeout(() => {
        bloqueado = false;
        disableBotoes(false);
        showMensagem("", "vazio");
    }, TEMPO_BLOQUEIO);
}

function showMensagem(texto, classe) {
    const msg = document.getElementById("mensagem");
    if (!msg) return;
    
    msg.innerText = texto;
    msg.className = "mensagem-feedback " + classe;
    msg.style.display = texto ? "flex" : "none";
}

function disableBotoes(disable) {
    const botoes = document.querySelectorAll(".btn-fullscreen");
    botoes.forEach(btn => {
        btn.disabled = disable;
        btn.style.opacity = disable ? "0.5" : "1";
        btn.style.cursor = disable ? "not-allowed" : "pointer";
    });
}

// Atualizar data e dia da semana ao carregar a página
document.addEventListener("DOMContentLoaded", function() {
    atualizarDataHora();
    
    // Atualizar a cada minuto
    setInterval(atualizarDataHora, 60000);
});

function atualizarDataHora() {
    const hoje = new Date();
    
    // Formatar data (DD/MM/YYYY)
    const dia = String(hoje.getDate()).padStart(2, '0');
    const mes = String(hoje.getMonth() + 1).padStart(2, '0');
    const ano = hoje.getFullYear();
    const dataFormatada = `${dia}/${mes}/${ano}`;
    
    // Obter dia da semana
    const diasSemana = [
        "Domingo", "Segunda", "Terça", "Quarta", 
        "Quinta", "Sexta", "Sábado"
    ];
    const diaAtual = diasSemana[hoje.getDay()];
    
    // Atualizar elementos
    const elemData = document.getElementById("data-atual");
    const elemDia = document.getElementById("dia-atual");
    
    if (elemData) elemData.innerText = dataFormatada;
    if (elemDia) elemDia.innerText = diaAtual;
}


