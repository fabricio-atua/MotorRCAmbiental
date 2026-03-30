document.addEventListener("DOMContentLoaded", function () {
    const preResposta = document.getElementById("resposta-json");
    const form = document.getElementById("formPrecificacao"); // id do form

    if (!form) return;

    // Função para enviar dados do form e atualizar JSON
    function atualizarJson() {
        const formData = new FormData(form);

        fetch("/calcular_precificacao", {
            method: "POST",
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            preResposta.textContent = JSON.stringify(data, null, 4);
        })
        .catch(error => {
            console.error("Erro ao buscar JSON:", error);
        });
    }

    // Seleciona todos os inputs, selects e textareas dentro do form
    const campos = form.querySelectorAll("input, select, textarea");

    // Adiciona listener de mudança a cada campo
    campos.forEach(campo => {
        campo.addEventListener("change", atualizarJson);
        campo.addEventListener("input", atualizarJson);
    });

});
