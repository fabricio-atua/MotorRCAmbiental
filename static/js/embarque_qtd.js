document.addEventListener("DOMContentLoaded", () => {

    const perigoso = document.getElementById("ft_qtde_embarque_perigoso");
    const comum = document.getElementById("ft_qtde_embarque_prod_comum");

    if (!perigoso || !comum) return;

    function formatar(valor) {
        return valor
            .toString()
            .replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    function limparNumero(valor) {
        return parseInt((valor || "").replace(/\./g, ""), 10) || 0;
    }

    function validarCampo(campo) {

        let valor = limparNumero(campo.value);

        // trava individual
        if (valor > 2500) {
            valor = 2500;
        }

        // aplica formatação
        campo.value = valor ? formatar(valor) : "";
    }

    perigoso.addEventListener("input", () => validarCampo(perigoso));
    comum.addEventListener("input", () => validarCampo(comum));

});

// ==============================
// FUNÇÃO PARA USAR NO BACKEND
// ==============================
function getQtdEmbarquesPerigoso() {
    const campo = document.getElementById("ft_qtde_embarque_perigoso");
    return parseInt((campo.value || "").replace(/\./g, ""), 10) || 0;
}

function getQtdEmbarquesComum() {
    const campo = document.getElementById("ft_qtde_embarque_prod_comum");
    return parseInt((campo.value || "").replace(/\./g, ""), 10) || 0;
}
