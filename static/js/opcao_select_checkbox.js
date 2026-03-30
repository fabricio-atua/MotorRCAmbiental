document.addEventListener('DOMContentLoaded', function () {
    // Função para limitar seleção a uma checkbox por grupo
    function limitarEscolhaUnica(grupoSelector) {
        const checkboxes = document.querySelectorAll(grupoSelector);
        checkboxes.forEach(function (checkbox) {
            checkbox.addEventListener('change', function () {
                if (this.checked) {
                    checkboxes.forEach(cb => {
                        if (cb !== this) cb.checked = false;
                    });
                }
            });
        });
    }

    // Aplicar a função para cada grupo de perguntas
    limitarEscolhaUnica('.linha-QAR61 input[type="checkbox"]'); // QAR-6
    limitarEscolhaUnica('.linha-QAR7 input[type="checkbox"]');  // QAR-7
    limitarEscolhaUnica('.linha-QAR81 input[type="checkbox"]'); // QAR-8
});