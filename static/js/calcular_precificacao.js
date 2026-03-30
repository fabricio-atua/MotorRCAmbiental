// -------- CONSULTA CNPJ --------
async function consultarCNPJ() {
    const cnpj = document.querySelector('input[name="cnpj"]').value.replace(/\D/g, '');

    if (cnpj.length !== 14) {
        alert("CNPJ inválido. Certifique-se de digitar 14 números.");
        throw new Error("CNPJ inválido");
    }

    const response = await fetch(`/api/cnpj/${cnpj}`);
    if (!response.ok) throw new Error("Erro na consulta da API");

    const data = await response.json();
    if (data.status === "ERRO") {
        alert(data.mensagem);
        throw new Error("Erro retornado da API: " + data.mensagem);
    }

    const campos = ["nome", "situacao", "porte", "logradouro", "numero", "municipio", "bairro", "uf", "cep", "email", "telefone", "status"];
    campos.forEach(campo => {
        document.querySelector(`input[name="${campo}"]`).value = data[campo] || '';
    });
}

function isCNPJPreenchido() {
    return document.querySelector('input[name="nome"]').value.trim() !== "";
}

// -------- VALIDAÇÃO SE OS CAMPOS FORAM PREENCHIDOS --------
function validarFormularioCompleto() {

    // ==============================
    // # VALIDAÇÃO DESABILITADA
    // ==============================
    /*
    let isValid = true;

    // Campos obrigatórios
    const campos = [
        { name: 'cnpj' },
        { id: 'corretor_codigo' },
        { id: 'corretor_nome' },
        { id: 'corretor_comissao' },
        { id: 'corretor_contato' },
        { id: 'corretor_telefone' },
        { id: 'cobertura_select' },
        { id: 'canal_select' },
        { name: 'ft_prodperig', type: 'radio' },
        { id: 'embarques_qtd' },
        { id: 'embarque_lmi' },
        { id: 'acondicionamento_faixa_granel' },
        { id: 'acondicionamento_faixa_fracionado' }
    ];

    campos.forEach((campo) => {
        let input, valor;
        let span;

        if (campo.type === 'radio') {
            const radios = document.querySelectorAll(`input[name="${campo.name}"]`);
            const checked = Array.from(radios).some(r => r.checked);
            span = radios[0]?.closest('.pergunta')?.querySelector('.span-required');

            if (!checked) {
                radios.forEach(r => r.style.outline = '2px solid #e63636');
                if (span) span.style.display = 'block';
                isValid = false;
            } else {
                radios.forEach(r => r.style.outline = '');
                if (span) span.style.display = 'none';
            }

        } else {
            input = campo.id ? document.getElementById(campo.id) : document.querySelector(`input[name="${campo.name}"]`);
            valor = input?.value.trim();
            span = input?.closest('.pergunta')?.querySelector('.span-required') || input?.closest('div')?.querySelector('.span-required');

            if (!input || valor === '' || valor === '0') {
                input?.style.setProperty('border', '2px solid #e63636', 'important');
                if (span) span.style.display = 'block';
                isValid = false;
            } else {
                input?.style.setProperty('border', '', 'important');
                if (span) span.style.display = 'none';
            }
        }
    });

    // Validar grupo produto_top5[]
    const produtos = document.querySelectorAll('input[name="produto_top5[]"]');
    let peloMenosUmPreenchido = false;
    produtos.forEach(input => {
        if (input.value.trim() !== '') {
            peloMenosUmPreenchido = true;
        }
    });

    const spanProduto = document.querySelector('#QAR .span-required');
    if (!peloMenosUmPreenchido) {
        produtos.forEach(input => input.style.setProperty('border', '2px solid #e63636', 'important'));
        if (spanProduto) spanProduto.style.display = 'block';
        isValid = false;
    } else {
        produtos.forEach(input => input.style.setProperty('border', '', 'important'));
        if (spanProduto) spanProduto.style.display = 'none';
    }

    // Outras validações como perfil do motorista, QAR-5 a QAR-10, modais, tipos de seguro, etc...
    // Todas permanecem comentadas para desabilitar mensagens de erro
    */

    // ==============================
    // # FIM VALIDAÇÃO DESABILITADA
    // ==============================

    return true; // sempre retorna true, permitindo envio
}

// -------- MENSAGEM FLUTUANTE --------
function mostrarMensagemFlutuante(mensagem, tipo) {
    const mensagemElement = document.getElementById("mensagemFlutuante");

    mensagemElement.style.backgroundColor = tipo === 'sucesso' ? '#4CAF50' : '#df6259';
    mensagemElement.style.color = 'white';
    mensagemElement.textContent = mensagem;
    mensagemElement.style.display = 'block';

    setTimeout(() => {
        mensagemElement.style.display = 'none';
    }, 5000);
}

document.getElementById('btnCalcular').addEventListener('click', function(event) {
    if (!validarFormularioCompleto()) {
        event.preventDefault(); // Impede envio
    }
});

// -------- EVENTO CLICK --------
document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("btnCalcular").addEventListener("click", async function (e) {
        e.preventDefault();

        if (!validarFormularioCompleto()) return;

        const processandoElement = document.getElementById("processando");
        const mensagemDiv = document.getElementById("mensagemCotacao");

        if (processandoElement) processandoElement.style.display = "inline-flex";
        if (mensagemDiv) {
            mensagemDiv.style.display = "none";
            mensagemDiv.textContent = "";
        }

        try {
            if (!isCNPJPreenchido()) await consultarCNPJ();

            const formData = new FormData();

            // Topo
            const canalSelect = document.getElementById("canal_select").value;
            const coberturaSelect = document.getElementById("cobertura_select").value;
            const produtoInputs = document.querySelectorAll("input[name='produto_top5[]']");
            produtoInputs.forEach(input => {
                const valor = input.value.trim();
                if (valor !== "") formData.append("produto_top5[]", valor);
            });
            formData.append("ft_canal", canalSelect);
            formData.append("ft_cobertura", coberturaSelect);
            formData.append("ft_prodperig", document.querySelector("input[name='ft_prodperig']:checked")?.value || "");
            
            const qtdeEmbarque = document.getElementById("ft_qtde_embarque").value.replace(/\./g, "");
            formData.append("ft_qtde_embarque", qtdeEmbarque);
            
            const lmiBasico = getLmiBasico(); // chama a função que limpa e converte
            formData.append("ft_isagrupcobertura", lmiBasico ?? "");

            formData.append("ft_acondicionamento_granel", document.querySelector("#acondicionamento_faixa_granel")?.value || "");
            formData.append("ft_acondicionamento_fracionado", document.querySelector("#acondicionamento_faixa_fracionado")?.value || "");

            // Segurado
            const camposSegurado = ["cnpj", "nome", "situacao", "porte", "logradouro", "numero", "municipio", "bairro", "uf", "cep", "email", "telefone", "status"];
            camposSegurado.forEach(campo => {
                const input = document.querySelector(`input[name='${campo}']`);
                if (input) formData.append(campo, input.value.trim());
            });

            // Grupo empresarial
            document.querySelectorAll(".linha-grupoempresa").forEach(linha => {
                formData.append("grupo_emp_cnpj[]", linha.querySelector(".cnpjGrupo")?.value.trim() || "");
                formData.append("grupo_emp_nome[]", linha.querySelector(".nomeGrupo")?.value.trim() || "");
                formData.append("grupo_emp_participacao[]", linha.querySelector(".participacaoGrupo")?.value.trim() || "");
            });

            // Frota
            formData.append("qtd_frota_transportadora", document.getElementById("qtd_frota_transportadora").value || "");
            formData.append("qtd_frota_agregado", document.getElementById("qtd_frota_agregado").value || "");
            formData.append("qtd_frota_propria", document.getElementById("qtd_frota_propria").value || "");
            formData.append("qtd_frota_autonomo", document.getElementById("qtd_frota_autonomo").value || "");

            // Perfis, certificações, tipo seguro, modais
            document.querySelectorAll("input[name='perfil_motorista[]']:checked").forEach(input => {
                formData.append("perfil_motorista[]", input.value);
            });
            for (let i = 1; i <= 5; i++) {
                formData.append(`cd_certificao_${i}`, document.querySelector(`input[name="cd_certificao_${i}"]:checked`)?.value || "");
            }
            document.querySelectorAll('input[name^="cd_tipo_seguro_"]:checked').forEach(el => {
                formData.append("tipo_seguro[]", el.value);
            });
            document.querySelectorAll('input[name="modais_utilizado[]"]:checked').forEach(el => {
                formData.append("modais_utilizado[]", el.value);
            });

            // Atividades
            document.querySelectorAll('input[name="atividade[]"]:checked').forEach(el => {
                formData.append("atividade[]", el.value);
            });

            // Classes e porcentagens
            const classes = {};
            const porcentagens = {};
            document.querySelectorAll("input[name^='classe_']:checked").forEach((checkbox) => {
                const classKey = checkbox.name.split('_')[1];
                const porcentagemInput = document.querySelector(`input[name='cd_classeproduto_${classKey}']`);
                classes[classKey] = true;
                porcentagens[classKey] = porcentagemInput ? porcentagemInput.value : "";
            });
            formData.append("classes", JSON.stringify(classes));
            formData.append("porcentagens", JSON.stringify(porcentagens));

            // UFs
            const ufsSelecionadas = [];
            document.querySelectorAll("input[name='uf_transp[]']:checked").forEach(checkbox => {
                ufsSelecionadas.push(checkbox.value);
            });
            formData.append("ufs", JSON.stringify(ufsSelecionadas));

            // Dados do corretor
            const dadosCorretor = {};
            ["corretor_codigo", "corretor_nome", "corretor_comissao", "corretor_contato", "corretor_telefone"].forEach(campo => {
                const input = document.querySelector(`input[name='${campo}']`);
                if (input) dadosCorretor[campo] = input.value.trim();
            });
            formData.append("corretor", JSON.stringify(dadosCorretor));


            // ============================================================
            // COBERTURAS ADICIONAIS
            // ============================================================
            document.querySelectorAll('input[name="adicional"]:checked').forEach(cb => {

                const lmi = cb.closest(".item-adicional")
                            ?.querySelector(".lmi-input")?.value || "";

                formData.append("coberturas_adicionais[]", JSON.stringify({
                    codigo: cb.value,
                    lmi: lmi
                }));
            });

            // Enviar
            const response = await fetch("/calcular_precificacao", {
                method: "POST",
                body: formData
            });

            if (!response.ok) throw new Error(`Erro HTTP: ${response.status}`);
            const data = await response.json();

            console.log("dados_cotacao:", data.dados_cotacao);

            // === CHAMADA DO ITEM TABELA DE PREÇO FINAL NA TELA HTML ===
            if (typeof montarTabelaCoberturas === "function") {
                montarTabelaCoberturas(data); // monta a tabela no HTML
            }

            // Mostrar mensagem de sucesso
            const numeroCotacao = data.dados_cotacao?.cotacao?.numero_cotacao || "???";

            if (mensagemDiv) {
                mensagemDiv.textContent = `Cotação ${numeroCotacao} salva com sucesso!`;
                alert(`Cotação ${numeroCotacao} salva com sucesso!`);

                mensagemDiv.style.color = "green";
                mensagemDiv.style.display = "block";
                setTimeout(() => {
                    mensagemDiv.style.display = "none";
                }, 10000);
            }

            // Atualizar resposta JSON se necessário
            const respostaJson = document.getElementById("resposta-json");
            if (respostaJson) respostaJson.innerText = JSON.stringify(data, null, 2);

        } catch (error) {
            console.error("Erro ao processar cotação:", error);
            // Mostrar mensagem de erro
            if (mensagemDiv) {
                mensagemDiv.textContent = "Erro ao processar a cotação: " + error.message;
                mensagemDiv.style.color = "red";
                mensagemDiv.style.display = "block";
            }

            const respostaJson = document.getElementById("resposta-json");
            if (respostaJson) {
                respostaJson.innerText = "Erro ao enviar formulário: " + error.message;
            }

        } finally {
            if (processandoElement) processandoElement.style.display = "none";
        }
    });
});
