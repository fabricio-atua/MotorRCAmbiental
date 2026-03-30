document.addEventListener("DOMContentLoaded", () => {

    const campo = document.getElementById("ft_qtde_embarque");
    if (!campo) return;

    campo.addEventListener("input", function () {

        let valor = this.value.replace(/\D/g, "");

        if (!valor) {
            this.value = "";
            return;
        }

        valor = parseInt(valor, 10);

        if (valor > 2500) {
            alert("O máximo permitido é 2.500 embarques.");
            valor = 2500;
        }

        this.value = valor
            .toString()
            .replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    });

});

// ==============================
// FUNÇÃO PARA USAR NO BACKEND
// ==============================
function getQtdEmbarques() {
    const campo = document.getElementById("ft_qtde_embarque");
    return parseInt(
        (campo.value || "").replace(/\./g, ""),
        10
    ) || 0;
}
