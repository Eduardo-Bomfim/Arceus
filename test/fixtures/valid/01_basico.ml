programa basico {
    var x inteiro;
    var y, z : inteiro;
    var ativo booleano;

    # Entrada e atribuições básicas
    leia x;
    leia (y);
    z = x + y * 2;
    ativo = (z >= 10) e não falso;

    se (ativo) {
        escreva z;
    } senão {
        escreva 0;
    }
}
fim.
