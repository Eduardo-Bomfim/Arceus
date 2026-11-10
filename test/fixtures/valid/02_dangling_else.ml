programa dangling_else {
    var a, b booleano;
    a = verdadeiro;
    b = falso;

    # O 'senão' deve ligar-se ao 'se' interno (b)
    se (a)
        se (b)
            escreva 1;
        senão
            escreva 2;

    # Chaves explícitas ligam o 'senão' ao 'se' externo (a)
    se (a) {
        se (b)
            escreva 3;
    } senão {
        escreva 4;
    }
}
fim.
