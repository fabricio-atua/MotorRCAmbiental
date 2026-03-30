document.addEventListener("DOMContentLoaded", function () {
    document.addEventListener('keypress', function (event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            let input = event.target;
            if (input.classList.contains('cnpjGrupo') || input.classList.contains('nomeGrupo')) {
                let linha = input.closest('.linha-grupoempresa');
                let inputs = linha.querySelectorAll('input');
                for (let i = 0; i < inputs.length; i++) {
                    if (inputs[i] === input && inputs[i + 1]) {
                        inputs[i + 1].focus();
                        break;
                    }
                }
            }
        }
    });

    // Adicionar nova linha de empresa
    document.getElementById("adicionarEmpresa").addEventListener("click", function () {
        let linhaOriginal = document.querySelector(".linha-grupoempresa");
        let novaLinha = linhaOriginal.cloneNode(true);

        // Limpa os valores dos inputs da nova linha
        novaLinha.querySelectorAll("input").forEach(input => input.value = "");

        // Remove o botão de adicionar da nova linha (deixa apenas na primeira)
        let botaoAdicionar = novaLinha.querySelector("#adicionarEmpresa");
        if (botaoAdicionar) {
            botaoAdicionar.remove();
        }

        document.getElementById("empresasGrupo").appendChild(novaLinha);
    });
});

// Remover linha de empresa (exceto a primeira)
function removerEmpresa(button) {
    const todasLinhas = document.querySelectorAll(".linha-grupoempresa");
    const linhaASerRemovida = button.parentElement;

    if (linhaASerRemovida === todasLinhas[0]) {
        alert("A primeira linha não pode ser removida.");
        return;
    }

    if (todasLinhas.length > 1) {
        linhaASerRemovida.remove();
    } else {
        alert("É necessário pelo menos uma empresa.");
    }
}