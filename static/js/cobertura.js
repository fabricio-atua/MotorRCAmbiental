document.addEventListener("DOMContentLoaded", () => {

    // ==============================
    // ELEMENTOS DA TELA
    // ==============================
    const selectCobertura = document.getElementById("cobertura_select");
    const divCoberturas = document.getElementById("descCoberturas");
    const lista = document.getElementById("listaSubcoberturas");

    const btnAdicionais = document.getElementById("btnAdicionais");
    const adicionaisContainer = document.getElementById("adicionaisContainer");

    // ==============================
    // COBERTURA BÁSICA
    // ==============================
    selectCobertura.addEventListener("change", function () {
        const valor = this.value;

        if (!valor) {
            divCoberturas.style.display = "none";
            lista.innerHTML = "";
            return;
        }

        fetch(`/api/cobertura_exibir/${valor}`)
            .then(res => res.json())
            .then(data => {
                lista.innerHTML = "";

                const coberturas = Array.isArray(data) ? data : [data];

                coberturas.forEach(cob => {
                    const li = document.createElement("li");
                    li.textContent = cob.DS_COBERTURA || "Cobertura sem descrição";
                    lista.appendChild(li);
                });

                divCoberturas.style.display = coberturas.length > 0 ? "block" : "none";
            })
            .catch(err => {
                console.error("Erro ao buscar coberturas:", err);
                divCoberturas.style.display = "none";
                lista.innerHTML = "";
            });
    });

    if (selectCobertura.value) {
        selectCobertura.dispatchEvent(new Event("change"));
    }

    // ==============================
    // BOTÃO COBERTURAS ADICIONAIS
    // ==============================
    btnAdicionais.addEventListener("click", function () {
        const visible = adicionaisContainer.style.display === "block";
        adicionaisContainer.style.display = visible ? "none" : "block";
    });

    // ==============================
    // MÁSCARA MONETÁRIA
    // ==============================
    function aplicarMascaraMoeda(input) {
        let valor = input.value.replace(/\D/g, "");

        if (!valor) {
            input.value = "";
            return;
        }

        if (valor.length > 9) valor = "100000000";

        if (valor.length <= 2) {
            input.value = valor;
            return;
        }

        let parteInteira = valor.slice(0, -2);
        let centavos = valor.slice(-2);

        parteInteira = parteInteira.replace(/\B(?=(\d{3})+(?!\d))/g, ".");

        input.value = `${parteInteira},${centavos}`;
    }

    // ==============================
    // EVENTOS DOS CHECKBOXES
    // ==============================
    document.querySelectorAll('#adicionaisContainer input[type="checkbox"]').forEach(chk => {
        chk.addEventListener("change", function () {
            const li = this.closest("li");
            const inputLmi = li.querySelector(".lmi-input");

            if (this.checked) {
                inputLmi.style.display = "block";

                if (!inputLmi._maskAttached) {
                    inputLmi._maskAttached = true;

                    inputLmi.addEventListener("input", function () {
                        aplicarMascaraMoeda(this);
                        let numero = parseInt(this.value.replace(/\D/g, ""));
                        if (numero > 100000000) {
                            alert("O LMI máximo permitido é R$ 1.000.000,00");
                            this.value = "1.000.000,00";
                        }
                    });

                    inputLmi.addEventListener("blur", function () {
                        if (this.value === "") return;
                        if (!this.value.includes(",")) this.value = this.value + ",00";
                    });
                }

            } else {
                inputLmi.value = "";
                inputLmi.style.display = "none";
            }
        });
    });

    // ==============================
    // PREPARA DADOS PARA ENVIAR AO BACKEND
    // ==============================
    function getCoberturasComLmi() {
        return [...document.querySelectorAll('#adicionaisContainer input[type="checkbox"]:checked')].map(chk => {
            const li = chk.closest("li");
            const val = li.querySelector(".lmi-input").value || null;
            const numero = val ? parseFloat(val.replace(/\./g, "").replace(",", ".")) : null;

            return {
                codigo: chk.value,
                nome: chk.dataset.nome,
                lmi: numero
            };
        });
    }

    // ==============================
    // VALIDAÇÕES ANTES DE ENVIAR
    // ==============================
    function validarCoberturasAntesDeEnviar() {
        const selecionados = document.querySelectorAll('#adicionaisContainer input[type="checkbox"]:checked');

        for (const chk of selecionados) {
            const inputLmi = chk.closest("li").querySelector(".lmi-input");

            if (!inputLmi.value || inputLmi.value.trim() === "") {
                alert(`Você marcou a cobertura "${chk.dataset.nome}" mas não informou o LMI.`);
                inputLmi.focus();
                return false;
            }

            const numero = parseFloat(inputLmi.value.replace(/\./g, "").replace(",", "."));

            if (numero > 1000000) {
                alert(`O LMI da cobertura "${chk.dataset.nome}" não pode ser maior que R$ 1.000.000,00`);
                inputLmi.focus();
                return false;
            }
        }

        return true;
    }

});