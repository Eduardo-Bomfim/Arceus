programa lacos_blocos {
    var contador, soma : inteiro;
    contador = 5;
    soma = 0;

    enquanto (contador > 0) {
        var passo_local inteiro;
        passo_local = 1;
        soma = soma + contador;
        contador = contador - passo_local;
    }

    escreva soma;
}
fim.
