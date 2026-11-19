programa extensao_d {
    var i, total, x : inteiro;
    total = 0;

    para i = 1 ate 5 {
        total = total + i;
    }

    para i = 10 ate 0 passo -2 {
        escreva i;
    }

    x = 3;
    repita {
        escreva x;
        x = x - 1;
    } ate (x == 0);
}
fim.
