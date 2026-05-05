document.addEventListener("DOMContentLoaded", () => {

    // ==============================
    // CAMPO DO LMI DA COBERTURA BÁSICA
    // ==============================
    const campoBasico = document.getElementById("lmi_basico");
    if (!campoBasico) return;

    const checkboxes = document.querySelectorAll("input[name='adicional']");

    // ==============================
    // FUNÇÃO DE MÁSCARA MONETÁRIA
    // ==============================
    function aplicarMascaraLmiBasico(input) {
        let valor = input.value.replace(/\D/g, "");

        if (!valor) {
            input.value = "";
            return;
        }

        if (valor.length > 9) {
            valor = valor.substring(0, 9);
        }

        if (parseInt(valor, 10) > 1000000) {
            alert("O LMI máximo permitido é R$ 1.000.000");
            valor = "1000000";
        }

        input.value = valor.replace(/\B(?=(\d{3})+(?!\d))/g, ".");
    }

    // ==============================
    // ATUALIZA ADICIONAIS
    // ==============================
    function atualizarAdicionais() {
        const valor = campoBasico.value;

        document.querySelectorAll(".lmi-adicional").forEach(input => {
            const checkbox = input.closest(".item-adicional")
                                  .querySelector("input[name='adicional']");

            if (checkbox.checked) {
                input.value = valor;
            }
        });
    }

    // ==============================
    // BLOQUEIA DIGITAÇÃO NÃO NUMÉRICA
    // ==============================
    campoBasico.addEventListener("keydown", (e) => {
        const teclasPermitidas = ["Backspace", "Delete", "ArrowLeft", "ArrowRight", "Tab"];
        const ehNumero = e.key >= "0" && e.key <= "9";

        if (!(ehNumero || teclasPermitidas.includes(e.key))) {
            e.preventDefault();
        }
    });

    // ==============================
    // AO DIGITAR NO LMI BÁSICO
    // ==============================
    campoBasico.addEventListener("input", function () {
        aplicarMascaraLmiBasico(this);
        atualizarAdicionais();
    });

    // ==============================
    // AO MARCAR/DESMARCAR ADICIONAIS
    // ==============================
    checkboxes.forEach(cb => {
        cb.addEventListener("change", function () {

            const item = cb.closest(".item-adicional");
            const input = item.querySelector(".lmi-adicional");

            if (cb.checked) {
                input.style.display = "block";
                input.value = campoBasico.value;
            } else {
                input.style.display = "none";
                input.value = "";
            }
        });
    });

});


// ==============================
// FUNÇÃO PARA USAR NO BACKEND
// ==============================
function getLmiBasico() {
    const campo = document.getElementById("lmi_basico");
    if (!campo || campo.value.trim() === "") return null;

    return parseInt(campo.value.replace(/\./g, ""), 10);
}