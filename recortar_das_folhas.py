# -*- coding: utf-8 -*-
u"""
============================================================
 RECORTAR AS FIGURAS DAS FOLHAS DE PAPEL — Jornalista por um Dia (2º ano)

 ⭐ A REGRA QUE MANDA AQUI (Marcos, 14/set/2026): *"procure na internet, nada de
    imagem gerada por IA, utilize das atividades"*.

 ⚠️ E NESTE CADERNO A REGRA TEM UMA SEGUNDA METADE, que é do assunto: o degrau
    é a FOTOLEGENDA — foto + legenda. Então metade das figuras **não se recorta
    com fundo transparente**: elas são FOTOS, e foto tem moldura. Um cachorro
    recortado flutuando não é uma foto de jornal; o mesmo cachorro dentro do seu
    retângulo, com céu e grama, é. As duas famílias convivem de propósito:

      · FOTO (retângulo, fundo inteiro)  -> o que a criança vai LEGENDAR
      · FIGURA (recortada, transparente) -> o que ela vai arrastar, ligar, casar

 De onde cada uma vem, e por que a folha é livre:

   · d37 — *"AS FOTOLEGENDAS SÃO TEXTOS QUE ACOMPANHAM UMA FOTO…"* — a versão
     limpa da d13, com as duas cenas maiores: o cachorro no parque e a menina
     com o bolo de aniversário.
   · d39 — *"A FOTOLEGENDA É UM GÊNERO TEXTUAL QUE FAZ PARTE DO NOSSO
     COTIDIANO."* — as três crianças lendo no chão.
   · d13 — a mesma família, e é a única com os irmãos chorando e o parquinho.
   · d03 — *"JORNAL — Você sabe ler um jornal?"* — o jornaleiro gritando.
   · d18 — *"Observe as imagens e escreva sobre as notícias."* — o molde de
     página de jornal em branco, com o menino comendo e a menina servindo suco.
   · d12 — *"TRABALHANDO COM NOTÍCIA"* (o golfinho Tião) — o golfinho a traço.
   · d29 — *"Funcionário adota beija-flor"* — a foto do beija-flor na flor.

 ⛔ O QUE FICOU DE FORA, E POR QUÊ — as FOTOS DE PESSOAS REAIS das folhas d24,
    d34, d17, d22 e d11. São fotografias de gente identificável publicadas em
    material de terceiros. Desenho a traço e clip-art de folha de atividade
    entram; retrato de pessoa real, não. (O beija-flor da d29 é foto, mas de um
    passarinho.)

 ⚠️ E O NOME TEM DE BATER COM O DESENHO. Conferir OLHANDO a folha de contato.

 Uso:  python3 _not2/recortar_das_folhas.py
============================================================
"""
from __future__ import print_function

import io
import json
import os
import sys

try:
    from PIL import Image
except ImportError as e:                                   # pragma: no cover
    print(u"preciso de Pillow (%s)" % e)
    sys.exit(2)

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
sys.path.insert(0, os.path.join(RAIZ, u"_padrao"))
from recorte_folha import (limpa_fundo, tira_halo, aperta,          # noqa: E402
                           tira_linha_impressa)

FOLHAS = os.path.join(RAIZ, u"_sequencias", u"folhas_not2")
DEST = os.path.join(AQUI, u"img")
PREFIXO = u"nt_"
MAIOR = 320

D03 = u"d03_4e2c0e.jpg"
D12 = u"d12_e05937.jpg"
D13 = u"d13_1f3193.jpg"
D18 = u"d18_1fc4d7.jpg"
D29 = u"d29_024841.jpg"
D37 = u"d37_a1ab65.jpg"
D39 = u"d39_565722.jpg"

# nome, folha, x1, y1, x2, y2, modo
#   "foto"   = retângulo inteiro, fundo e tudo (é uma FOTO de jornal)
#   "figura" = recortada, fundo transparente (é peça de arrastar/ligar)
PECAS = [
    # --- as FOTOS que a criança vai legendar --------------------------------
    (u"cachorro",   D37,   92,  262,  278,  438, u"foto"),
    (u"parque",     D13,  374,  790,  531,  904, u"foto"),
    (u"jornaleiro", D03,  447,  647, 1163, 1213, u"foto"),
    (u"beijaflor",  D29,  784,  519, 1091,  740, u"foto"),

    # --- as FIGURAS recortadas ----------------------------------------------
    (u"bolo",       D37,   95,  516,  292,  692, u"figura"),
    (u"lendo",      D39,  300,  198,  502,  336, u"figura"),
    (u"choro",      D13,  352,  565,  484,  748, u"figura"),
    (u"peixe",      D18,  632,  464,  992,  686, u"figura"),
    (u"suco",       D18,  144,  702,  498,  940, u"figura"),
    (u"golfinho",   D12,   74,  652,  292,  932, u"figura"),
]

DE_ONDE = {
    D03: u"d03 — JORNAL: Você sabe ler um jornal?",
    D12: u"d12 — TRABALHANDO COM NOTÍCIA (o golfinho Tião)",
    D13: u"d13 — IMPORTANTE SABER SOBRE AS FOTOLEGENDAS",
    D18: u"d18 — Observe as imagens e escreva sobre as notícias",
    D29: u"d29 — Funcionário adota beija-flor",
    D37: u"d37 — AS FOTOLEGENDAS SÃO TEXTOS QUE ACOMPANHAM UMA FOTO",
    D39: u"d39 — A FOTOLEGENDA É UM GÊNERO TEXTUAL DO NOSSO COTIDIANO",
}


# ⚠️ AS TRÊS QUE PRECISARAM DE UMA SEGUNDA PASSADA (medido pelo portão 0o6,
#    `_qa/halo.py`, que reprovou com 3,07%, 2,32% e 1,70% de franja branca).
#    O `tira_halo` de fábrica come 2 voltas a 228; estas três vieram de folhas
#    escaneadas com o papel mais sujo, e a franja é mais larga. Come-se mais
#    fundo SÓ NELAS — uma volta a mais em todo o caderno arriscaria as figuras
#    de corpo quase branco, que é justamente o que o `tira_halo` existe para não
#    machucar (ver o comentário dele em `_padrao/recorte_folha.py`).
FRANJA_LARGA = {u"bolo", u"lendo", u"golfinho"}


def recorta(folha, x1, y1, x2, y2, modo, nome=u""):
    c = folha.crop((x1, y1, x2, y2))
    if modo == u"foto":
        return c.convert(u"RGB")
    c = limpa_fundo(c)
    c = tira_halo(c)
    if nome in FRANJA_LARGA:
        # ⚠️ E NÃO É "COMER MAIS FUNDO": tentei `tira_halo(lim=212, voltas=3)` e o
        #    bolo PIOROU de 3,07% para 5,29% — comer a franja descobre o pixel de
        #    trás, que também é quase branco, e a conta sobe. O conserto que o
        #    próprio portão indica é outro: um SEGUNDO FLOOD-FILL pela borda,
        #    agora mais frouxo. A água entra pelo transparente que o primeiro
        #    deixou e apaga o quase-branco que ALCANÇA — o branco fechado dentro
        #    da figura (o corpo do golfinho a traço) ela nunca alcança.
        c = limpa_fundo(c, lim=216)
        c = tira_halo(c)
    c = aperta(c)
    if c is not None:
        c = aperta(tira_linha_impressa(c))
    return c


def main():
    if not os.path.isdir(FOLHAS):
        print(u"⛔ não achei %s" % FOLHAS)
        return 2
    abertas, feitas, origem = {}, [], {}
    cam = os.path.join(DEST, u"ORIGEM.json")
    if os.path.exists(cam):
        origem = json.load(io.open(cam, encoding=u"utf-8"))
    for nome, arq, x1, y1, x2, y2, modo in PECAS:
        if arq not in abertas:
            abertas[arq] = Image.open(os.path.join(FOLHAS, arq)).convert(u"RGB")
        c = recorta(abertas[arq], x1, y1, x2, y2, modo, nome)
        if c is None:
            print(u"  ⚠️  %-10s saiu VAZIA" % nome)
            continue
        if max(c.size) > MAIOR:
            f = float(MAIOR) / max(c.size)
            c = c.resize((max(1, int(c.width * f)), max(1, int(c.height * f))),
                         Image.LANCZOS)
        alvo = PREFIXO + nome + u".png"
        c.save(os.path.join(DEST, alvo), optimize=True)
        origem[alvo] = u"folha:%s" % DE_ONDE[arq]
        feitas.append((alvo, c.size))
        print(u"  ✓ %-16s %3dx%-3d  %-6s <- %s" % (alvo, c.width, c.height,
                                                   modo, arq[:3]))
    io.open(cam, u"w", encoding=u"utf-8").write(
        json.dumps(origem, indent=1, sort_keys=True, ensure_ascii=False))
    print(u"\n%d figuras, todas recortadas de folha de papel." % len(feitas))
    folha_de_contato(feitas)
    return 0


def folha_de_contato(feitas):
    from PIL import ImageDraw
    COLS, CEL, LAB = 5, 200, 26
    linhas = (len(feitas) + COLS - 1) // COLS
    p = Image.new(u"RGB", (COLS * (CEL + 10) + 10, linhas * (CEL + LAB + 10) + 10),
                  (250, 250, 248))
    d = ImageDraw.Draw(p)
    for i, (alvo, _) in enumerate(feitas):
        im = Image.open(os.path.join(DEST, alvo)).convert(u"RGBA")
        im.thumbnail((CEL, CEL))
        x = 10 + (i % COLS) * (CEL + 10)
        y = 10 + (i // COLS) * (CEL + LAB + 10)
        d.rectangle([x, y, x + CEL, y + CEL], outline=(215, 215, 210))
        fundo = Image.new(u"RGBA", im.size, (255, 255, 255, 255))
        fundo.alpha_composite(im)
        p.paste(fundo.convert(u"RGB"), (x + (CEL - im.width) // 2,
                                        y + (CEL - im.height) // 2))
        d.text((x + 3, y + CEL + 6), alvo[len(PREFIXO):-4], fill=(40, 44, 52))
    cam = os.path.join(AQUI, u"_contato.png")
    p.save(cam, optimize=True)
    print(u"folha de contato: %s  — OLHAR antes de seguir" % cam)


if __name__ == u"__main__":
    sys.exit(main())
