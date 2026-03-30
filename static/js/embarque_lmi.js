document.addEventListener("DOMContentLoaded", () => {

    // ==============================
    // CAMPO DO LMI DA COBERTURA BÁSICA
    // ==============================
    const campoBasico = document.getElementById("lmi_basico");
    if (!campoBasico) return;

    // ==============================
    // FUNÇÃO DE MÁSCARA MONETÁRIA
    // Formata enquanto digita e controla limite (apenas inteiros)
    // ==============================
    function aplicarMascaraLmiBasico(input) {
        // remove tudo que não for número
        let valor = input.value.replace(/\D/g, "");

        if (!valor) {
            input.value = "";
            return;
        }

        // limita ao máximo de 9 dígitos (1.000.000)
        if (valor.length > 9) {
            valor = valor.substring(0, 9);
        }

        // valida limite máximo
        if (parseInt(valor, 10) > 1000000) {
            alert("O LMI máximo permitido é R$ 1.000.000");
            valor = "1000000";
        }

        // formata milhares 123456 → 123.456
        input.value = valor.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    // ==============================
    // BLOQUEIA DIGITAÇÃO DE QUALQUER COISA NÃO NUMÉRICA
    // ==============================
    campoBasico.addEventListener("keydown", (e) => {
        const teclasPermitidas = ["Backspace", "Delete", "ArrowLeft", "ArrowRight", "Tab"];
        const ehNumero = e.key >= "0" && e.key <= "9";
        if (!(ehNumero || teclasPermitidas.includes(e.key))) {
            e.preventDefault();
        }
    });

    // ==============================
    // APLICA MÁSCARA AO DIGITAR
    // ==============================
    campoBasico.addEventListener("input", function () {
        aplicarMascaraLmiBasico(this);
    });

});

// ==============================
// FUNÇÃO PARA USAR NO BACKEND
// Converte "1.234.567" → 1234567 (inteiro)
// ==============================
function getLmiBasico() {
    const campo = document.getElementById("lmi_basico");
    if (!campo || campo.value.trim() === "") return null;

    // Remove pontos e converte para número inteiro
    return parseInt(campo.value.replace(/\./g, ""), 10);
}
