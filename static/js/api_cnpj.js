function consultarCNPJ() {
    const cnpj = document.querySelector('input[name="cnpj"]').value.replace(/\D/g, '');

    if (cnpj.length !== 14) {
        alert("CNPJ inválido. Certifique-se de digitar 14 números.");
        return Promise.reject("CNPJ inválido");
    }

    return fetch(`/api/cnpj/${cnpj}`)
        .then(response => {
            if (!response.ok) {
                throw new Error("Erro na consulta da API");
            }
            return response.json();
        })
        .then(data => {
            if (data.status === "ERRO") {
                alert(data.mensagem);
                throw new Error(data.mensagem);
            }

            document.querySelector('input[name="nome"]').value = data.nome || '';
            document.querySelector('input[name="situacao"]').value = data.situacao || '';
            document.querySelector('input[name="porte"]').value = data.porte || '';
            document.querySelector('input[name="logradouro"]').value = data.logradouro || '';
            document.querySelector('input[name="numero"]').value = data.numero || '';
            document.querySelector('input[name="municipio"]').value = data.municipio || '';
            document.querySelector('input[name="bairro"]').value = data.bairro || '';
            document.querySelector('input[name="uf"]').value = data.uf || '';
            document.querySelector('input[name="cep"]').value = data.cep || '';
            document.querySelector('input[name="email"]').value = data.email || '';
            document.querySelector('input[name="telefone"]').value = data.telefone || '';
            document.querySelector('input[name="status"]').value = data.status || '';
        });
}

document.getElementById("btnConsultarCNPJ").addEventListener("click", consultarCNPJ);