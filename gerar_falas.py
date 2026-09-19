# -*- coding: utf-8 -*-
u"""
============================================================
 ESQUELETO — gerador das falas da folha viva

 ⚠️ REGRA DA CASA: o `falas.json` é a VERDADE. Texto escrito aqui = voz gravada.
    Texto mudou = voz regravada (o `entregar.yml` compara o carimbo sha1). É isto
    que acaba com "a tela diz uma coisa e a voz diz outra" — e atividade sem
    `falas.json` NÃO TEM COMO SER CONFERIDA, porque mp3 não se lê.

 ⚠️ UMA FONTE SÓ. As palavras, as frases e os textos moram no bloco
    `/*DADOS-INI*/` do `index.html` e são LIDOS daqui. Nada de segunda lista
    para desencontrar: já custou caro nesta casa um relatório sair zero com a
    folha inteira respondida.

 ⚠️ TODA TELA É NARRADA, e o alto-falante entra também em CADA RESPOSTA que a
    criança toca. Regra do Marcos: *"o alto-falante nas respostas também, para
    ajudar os alunos que não sabem ler"*. Sem isso a criança que ainda soletra
    escolhe pelo tamanho da palavra e a folha vira sorteio.

 ⚠️ A DICA NUNCA DIZ A RESPOSTA. Ela manda olhar uma pista, ou faz outra
    pergunta. Responder no segundo erro não é ajudar: é tirar da criança a única
    chance de pensar de novo.

 ⚠️ PALAVRAS QUE A VOZ ERRA (medido, e o portão `_qa/falas.py` reprova):
    "complete" vira "complite" — usar "preencha". Letra solta ("som S") sai como
    o NOME da letra: ancorar num exemplo ("o som de SAPO").

 Uso:  python3 <pasta>/gerar_falas.py
 Saída: reescreve os blocos FALAS e VOZOK do index.html, o `falas.json` e o
        `voz.txt`.
============================================================
"""
from __future__ import print_function

import collections
import io
import json
import os
import re
import unicodedata

AQUI = os.path.dirname(os.path.abspath(__file__))
CAM = os.path.join(AQUI, u"index.html")
PREFIXO = u"nt_"                     # <- o prefixo desta atividade
VOZ = u"pt-BR-AntonioNeural"

D = io.open(CAM, encoding=u"utf-8").read()


def bloco(nome):
    u"""Lê um objeto do bloco DADOS do index.html. Uma fonte só.

    ⚠️ ELE CONTA AS CHAVES, e isso foi conserto de 15/set/2026. O esqueleto
       procurava o fim do objeto por uma marca de texto (`\n});`) — e QUALQUER
       objeto que não terminasse exatamente assim fazia a leitura passar
       adiante e engolir o bloco seguinte. No primeiro caderno do 2º ano os
       vinte e três blocos falharam de uma vez, todos com o mesmo erro, e a
       mensagem do json não dizia nada sobre a causa. Contar chave por chave
       (pulando as que estão DENTRO de texto) acha o fim de qualquer objeto.
    """
    i = D.find(u"var " + nome + u" = ")
    if i < 0:
        raise SystemExit(u"nao achei o bloco `var %s` no index.html" % nome)
    i = D.index(u"{", i)
    nivel, j, dentro, escapa = 0, i, False, False
    while j < len(D):
        c = D[j]
        if dentro:
            if escapa:
                escapa = False
            elif c == u"\\":
                escapa = True
            elif c == u'"':
                dentro = False
        else:
            if c == u'"':
                dentro = True
            elif c == u"{":
                nivel += 1
            elif c == u"}":
                nivel -= 1
                if nivel == 0:
                    j += 1
                    break
        j += 1
    txt = D[i:j]
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    txt = re.sub(r'"\s*\+\s*\n\s*"', "", txt)                 # junta "a" + "b"
    txt = re.sub(r'([\{,]\s*)"?([A-Za-zÀ-ÿ_0-9]+)"?\s*:', r'\1"\2":', txt)
    txt = re.sub(r",(\s*[\}\]])", r"\1", txt)
    return json.loads(txt)


# ⚠️⚠️ A ENTIDADE HTML TAMBÉM É MARCAÇÃO, e isto foi lição paga (15/set/2026,
#    caderno de inglês do 8º ano). O `lp` tirava as TAGS e deixava as
#    ENTIDADES, então a lista de ingredientes da pizza — escrita com `&middot;`
#    para virar o ponto que separa os itens — ia para a fila de gravação como
#    *"Oil and middot Tomato sauce and middot Some onions"*. O portão
#    `_qa/revisor.py` pegou; se não pegasse, a voz teria dito isso à criança.
_ENT = {u"&middot;": u",", u"&nbsp;": u" ", u"&amp;": u" e ", u"&mdash;": u" ",
        u"&ndash;": u" ", u"&hellip;": u" ", u"&quot;": u'"', u"&lt;": u"",
        u"&gt;": u"", u"&#39;": u"'", u"&apos;": u"'"}


def lp(s):
    u"""tira a marcação e deixa o texto do jeito que a voz vai dizer"""
    t = re.sub(r"<[^>]+>", " ", s or u"")
    for _e, _v in _ENT.items():
        t = t.replace(_e, _v)
    t = re.sub(r"\s+", u" ", t)
    # ⚠️ e a tag que vira espaco deixa um vao ANTES da pontuacao ("o cinema ."),
    #    que o `_qa/revisor.py` acusa — com razao: a voz faz a pausa no lugar
    #    errado. Cola a pontuacao de volta na palavra.
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)
    # ⚠️ E A VIRGULA DA PAUSA PODE ENCOSTAR NUMA QUE JA EXISTIA (15/set/2026):
    #    a frase "My dad, ___ travels a lot" virou "My dad,, travels a lot" —
    #    duas virgulas coladas, que o Edge TTS le como uma pausa estranha e
    #    longa demais. Uma so, sempre.
    t = re.sub(r",\s*,+", u",", t)
    return t.strip()


def ch(w):
    return re.sub(r"[^a-z]", "",
                  unicodedata.normalize("NFKD", w.lower())
                  .encode("ascii", "ignore").decode())


F = collections.OrderedDict()


def p(k, v):
    u"""⚠️ TODA fala passa por aqui LIMPA. Não é enfeite: quando a frase perde
    a tag, sobram dois espaços; a lacuna `o ___ pula` vira `o lacuna pula`; e um
    texto que já acaba em ponto ganha outro e sai `ela..`. Quem pega isso é o
    portão `0o` (`_qa/revisor.py`) — a criança OUVIRIA."""
    t = re.sub(r"\s+", u" ", (v or u"")).strip()
    t = re.sub(r"\s+([,.;:!?])", r"\1", t)     # espaço antes da pontuação
    t = re.sub(r"([,.;:!?])\1+", r"\1", t)     # ".." e ",,"
    t = re.sub(r"\.\s*\.", u".", t)
    if t and t[-1] not in u".!?:":
        t += u"."
    F[k] = t


def semLacuna(s):
    u"""⚠️ A LACUNA NÃO SE NARRA (regra da casa, `SEQUENCIAS-DIDATICAS §2c`):
    some com reticências, que é como um adulto leria em voz alta para a criança
    completar. A correção diz a frase INTEIRA."""
    return re.sub(r"\s*_{2,}\s*", u"… ", lp(s)).strip()


# ---------------------------------------------------------------------------
# AS FALAS DO MOTOR — estas toda folha viva tem
# ---------------------------------------------------------------------------
p(u"capa", u"Jornalista por um Dia. Trinta e cinco folhas sobre a not\u00edcia do jornal: "
           u"a foto e a sua legenda, a manchete e as quatro perguntas que toda not\u00edcia "
           u"responde. Escreva o seu nome ali embaixo e toque em Come\u00e7ar.")
p(u"folhaPronta", u"Folha pronta! Muito bem.")
p(u"escreva", u"Escreva a palavra usando o teclado.")
p(u"ligue", u"Toque numa pe\u00e7a do lado esquerdo e depois na do lado direito.")
p(u"toque_palavra", u"Primeiro toque numa pe\u00e7a ali embaixo. Depois toque na gaveta dela.")
p(u"quase", u"Quase! Tente de novo.")
p(u"cacatoque", u"Toque primeiro na primeira letra da palavra.")
p(u"novoCaderno", u"Caderno novo! Escreva o seu nome e toque em Come\u00e7ar.")
p(u"vozOn", u"Narra\u00e7\u00e3o ligada!")
p(u"fim", u"Voc\u00ea chegou ao fim! Agora um desafio para levar: procure um jornal "
          u"de verdade, em papel ou na tela, e ache nele as quatro coisas que voc\u00ea "
          u"aprendeu. Cad\u00ea a manchete? Cad\u00ea a foto? Cad\u00ea a legenda? E o come\u00e7o "
          u"que diz o qu\u00ea, quem, quando e onde?")

ENUN = [
 u"Uma foto de jornal conta uma coisa. Olhe bem e diga o que est\u00e1 acontecendo nela.",
 u"Olhe a foto com calma e marque tudo o que ela mostra. Depois toque em Conferir.",
 u"Toque numa foto e depois na legenda que fala dela.",
 u"A legenda \u00e9 a frase que fica embaixo da foto e explica o que ela mostra. Qual combina?",
 u"Puxe a legenda at\u00e9 a foto dela, ou toque numa e depois na outra.",
 u"Agora a legenda \u00e9 sua: escreva a palavra que falta. As casinhas dizem quantas letras tem.",
 u"A manchete \u00e9 a frase curta que chama o leitor, l\u00e1 no alto do jornal. Ache a manchete.",
 u"Agora a foto \u00e9 que manda: escolha a manchete que serve para ela.",
 u"Agora a manchete: toque na foto e depois no t\u00edtulo que o jornal daria a ela.",
 u"Toda not\u00edcia responde quatro perguntas. A primeira \u00e9: o que aconteceu?",
 u"A segunda pergunta: com quem aconteceu?",
 u"E as duas \u00faltimas: onde e quando.",
 u"Leia a not\u00edcia e toque nas palavras que dizem QUEM est\u00e1 na not\u00edcia. Depois confira.",
 u"Nesta outra, toque nas palavras que dizem ONDE a not\u00edcia aconteceu. Depois confira.",
 u"Voc\u00ea leu as duas not\u00edcias. Escreva o que elas contaram.",
 u"O jornal fez um quadro com o que se sabe do golfinho. Leve cada resposta para a linha dela.",
 u"Leia a frase. Ela \u00e9 o t\u00edtulo l\u00e1 do alto, ou a frase que fica embaixo da foto?",
 u"Agora separe: isto conta algo que aconteceu, ou chama voc\u00ea para alguma coisa?",
 u"Cada parte do jornal tem um nome. Ligue o nome ao que ele \u00e9.",
 u"Esta \u00e9 a folha de papel virando tela: puxe o nome da parte at\u00e9 o lugar dela na p\u00e1gina.",
 u"Marque s\u00f3 o que pertence mesmo ao jornal. Cuidado com os intrusos.",
 u"A not\u00edcia sai do jornal e vai para muitos lugares. Onde voc\u00ea a encontra?",
 u"Algu\u00e9m escreve a not\u00edcia, e escreve para algu\u00e9m ler. Quem s\u00e3o eles?",
 u"A not\u00edcia viaja. Marque por onde ela chega at\u00e9 voc\u00ea.",
 u"Na not\u00edcia, os fatos t\u00eam uma ordem. Toque no que aconteceu primeiro.",
 u"As cenas da not\u00edcia do passarinho est\u00e3o embaralhadas. Ponha cada uma no lugar dela.",
 u"Agora a not\u00edcia do golfinho. Da primeira cena \u00e0 \u00faltima.",
 u"Ache na grade a palavra que a pista descreve: toque na primeira letra e depois na \u00faltima.",
 u"Agora as palavras do jornal. Na grade n\u00e3o h\u00e1 acento: procure NOTICIA, n\u00e3o not\u00edcia.",
 u"Toque numa pista, escute e escreva a palavra.",
 u"Nem todo texto serve para a mesma coisa. Leia e diga para que serve.",
 u"E agora o assunto: do que a not\u00edcia trata?",
 u"Agora o jornal \u00e9 seu. Olhe a foto e escreva uma palavra que sirva de manchete.",
 u"O jornal fez um \u00e1lbum com as fotos do dia. D\u00ea a legenda certa a cada uma.",
 u"Voc\u00ea j\u00e1 fez tudo isto sem os nomes. Agora eles: leve cada exemplo para a linha dele."]
assert len(ENUN) == 35, len(ENUN)
for _i, _t in enumerate(ENUN):
    p(u"p%denun" % (_i + 1), _t)

# ---------------------------------------------------------------------------
# AS FALAS DAS FOLHAS — uma seção por folha, lendo os DADOS do index.html.
# Uma fonte só: o que está escrito lá é o que a voz diz.
# ---------------------------------------------------------------------------
ELOGIO = [u"Isso mesmo!", u"Muito bem!", u"Você acertou!", u"Boa!", u"Exatamente!",
          u"É isso aí!"]
DICAS = [u"Olhe a foto de novo, com calma. A resposta está nela.",
         u"Leia as opções em voz alta. Só uma combina com o que você viu.",
         u"Pergunte para você mesmo: isto é mesmo coisa de jornal?",
         u"Volte à notícia e leia devagar. Ela conta tudo."]


def elogio(n):
    return ELOGIO[n % len(ELOGIO)]


def dica(n):
    return DICAS[n % len(DICAS)]


ITENS = bloco(u"ITENS")


def pote(pi):
    v = ITENS[u"p%d" % pi]
    return v[0] if v and isinstance(v[0], list) else v


def palavras(*ws):
    for _w in ws:
        if _w:
            _t = lp(_w)
            _t = _t[0].upper() + _t[1:]
            p(u"pal_" + ch(_w), _t if _t[-1:] in u".!?" else _t + u".")


# --- as folhas de PERGUNTA (1, 4, 7, 8, 10, 11, 12, 22, 23, 25, 31, 32) ------
#     as que trazem NOTÍCIA em cima ganham também a fala `not_<k>`.
for _pi, _nome in ((1, u"OQUE"), (4, u"ESCLEG"), (7, u"MANCH1"), (8, u"MANCH2"),
                   (10, u"LIDE1"), (11, u"LIDE2"), (12, u"LIDE3"), (22, u"ONDE1"),
                   (23, u"QUEMFAZ"), (25, u"ANTES"), (31, u"FIN"), (32, u"ASS")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _X = _D[_k]
        palavras(*_X[u"ops"])
        if _X.get(u"t"):
            p(u"not_" + _k, lp(_X[u"t"]))
        p(u"prg_" + _k, lp(_X[u"f"]))
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + lp(_X[u"f"]) + u" " +
          _X[u"r"][0].upper() + _X[u"r"][1:])
        p(u"dica%d_%s" % (_pi, _k), dica(_n))

# --- 2, 21 e 24: marque vários -----------------------------------------------
_MARQDICA = {2: u"Vá uma por uma e pergunte: isto aparece MESMO na foto?",
             21: u"Pense no jornal que você já viu. Isto estava dentro dele?",
             24: u"Pense em como a notícia chega até a sua casa."}
for _pi, _nome in ((2, u"MARQ1"), (21, u"MARQ2"), (24, u"MARQ3")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _M = _D[_k]
        for _q in _M[u"pecas"]:
            _t = lp(_q[u"t"])
            p(u"mrc_%s_%s" % (_k, _q[u"k"]), _t[0].upper() + _t[1:] + u".")
        _ok = [lp(_q[u"t"]) for _q in _M[u"pecas"] if _q[u"ok"]]
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" São " + u", ".join(_ok) + u".")
        p(u"dica%d_%s" % (_pi, _k), _MARQDICA[_pi])

# --- 3 e 9: ligar a FOTO a um texto ------------------------------------------
_LIGDICA = {3: u"Olhe a foto e imagine quem contaria isso para alguém que não a viu.",
            9: u"A manchete é curta e chama. Qual delas cabe no que a foto mostra?"}
for _pi, _nome in ((3, u"LIGL"), (9, u"LIGM")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _L = _D[_k]
        p(u"fig_" + _k, u"Foto: " + _L[u"n"] + u".")
        p(u"lg_" + _k + u"_d", lp(_L[u"b"])[0].upper() + lp(_L[u"b"])[1:])
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " +
          _L[u"n"][0].upper() + _L[u"n"][1:] + u": " + lp(_L[u"b"]))
        p(u"dica%d_%s" % (_pi, _k), _LIGDICA[_pi])

# --- 19: ligar o nome à parte do jornal ---------------------------------------
LIGP = bloco(u"LIGP")
for _n, _k in enumerate(pote(19)):
    _L = LIGP[_k]
    p(u"lg_" + _k + u"_e", lp(_L[u"a"]) + u".")
    p(u"lg_" + _k + u"_d", lp(_L[u"b"])[0].upper() + lp(_L[u"b"])[1:] + u".")
    p(u"certo19_" + _k, elogio(_n) + u" " + lp(_L[u"a"]) + u" é " + lp(_L[u"b"]) + u".")
    p(u"dica19_" + _k, u"Pense numa página de jornal aberta na sua frente: onde fica isso?")

# --- 5 e 34: puxar a LEGENDA até a FOTO ---------------------------------------
for _pi, _nome in ((5, u"SOLTA1"), (34, u"ALBUM")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _X = _D[_k]
        p(u"fig_" + _k, u"Foto: " + _X[u"n"] + u".")
        p(u"rot_" + _k, lp(_X[u"rot"])[0].upper() + lp(_X[u"rot"])[1:])
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " +
          _X[u"n"][0].upper() + _X[u"n"][1:] + u": " + lp(_X[u"rot"]))
        p(u"dica%d_%s" % (_pi, _k), u"Leia a legenda e pergunte: em qual foto isso "
                                    u"está acontecendo?")

# --- 16, 20, 26 e 27: puxar até o lugar certo ---------------------------------
_SOLTXT = {16: (u"vlr_", u"Leia o nome da linha e pense no que o jornal contou do golfinho."),
           20: (u"rot_", u"Pense numa página de jornal: o que fica lá no alto, bem grande?"),
           26: (u"cena_", u"Conte a notícia do começo. O que tinha de acontecer antes disto?"),
           27: (u"cena_", u"Conte a notícia do começo. O que tinha de acontecer antes disto?")}
for _pi, _nome in ((16, u"QUADRO"), (20, u"PARTES"), (26, u"ORDEM1"), (27, u"ORDEM2")):
    _D = bloco(_nome)
    _pref, _dic = _SOLTXT[_pi]
    for _n, _k in enumerate(pote(_pi)):
        _X = _D[_k]
        _v = _X.get(u"v") or _X.get(u"rot")
        _po = lp(_X[u"pos"])
        _po = _po[0].upper() + _po[1:]
        p(u"pos_" + _k, _po + u".")
        p(_pref + _k, lp(_v)[0].upper() + lp(_v)[1:])
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _po + u": " + lp(_v))
        p(u"dica%d_%s" % (_pi, _k), _dic)

# --- 6 e 15: escrever nas casinhas --------------------------------------------
for _pi, _nome in ((6, u"GRD1"), (15, u"GRD2")):
    _D = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _G = _D[_k]
        p(u"grd_" + _k, semLacuna(_G[u"p"]) + u" " + lp(_G[u"d"]))
        _c = lp(_G[u"p"]).replace(u"___", _G[u"w"].lower()).replace(u"…", u" " + _G[u"w"].lower()).strip()
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _c[0].upper() + _c[1:])
        p(u"dica%d_%s" % (_pi, _k), u"Conte as casinhas e diga a palavra devagar, "
                                    u"letra por letra.")

# --- 33: a manchete é sua ------------------------------------------------------
PROD = bloco(u"PROD")
for _n, _k in enumerate(pote(33)):
    _X = PROD[_k]
    p(u"prd_" + _k, u"Escreva " + lp(_X[u"q"]) + u".")
    p(u"certo33_" + _k, elogio(_n) + u" A manchete é sua e combina com a foto.")
    p(u"dica33_" + _k, u"Manchete é curta. Diga em voz alta o que a foto mostra e "
                       u"guarde só a palavra mais importante.")

# --- 13 e 14: achar dentro da notícia ------------------------------------------
TXT = bloco(u"TXT")
_TXTDICA = {13: u"Quem é gente ou bicho nesta notícia? Leia linha por linha.",
            14: u"Procure os lugares: onde cada coisa aconteceu?"}
for _pi, _tk in ((13, u"tx1"), (14, u"tx2")):
    _T = TXT[_tk]
    _nw = 0
    for _lin in _T[u"linhas"]:
        for _w in _lin:
            p(u"tx%d_%d" % (_pi, _nw), _w)
            _nw += 1
    p(u"certo%d_t" % _pi, u"Muito bem! As palavras eram " + u", ".join(_T[u"ok"]) + u".")
    p(u"dica%d_t" % _pi, _TXTDICA[_pi])

# --- 17 e 18: as gavetas --------------------------------------------------------
GAV = bloco(u"GAV")
_GAVTXT = {u"m": u"Gaveta da manchete.", u"g": u"Gaveta da legenda.",
           u"n": u"Gaveta da notícia.", u"c": u"Gaveta do convite."}
for _gk, _G in GAV.items():
    for _C in _G[u"cols"]:
        p(u"gav_%s_%s" % (_gk, _C[u"k"]), _GAVTXT[_C[u"k"]])
# ⚠️ A EXPLICAÇÃO COMEÇA EM MAIÚSCULA porque vem DEPOIS do ponto final da
#    frase. Escrita em minúscula, saía "…plantou três árvores. é notícia" — e o
#    portão `0o` (`_qa/revisor.py`) acusou sete falas de uma vez.
_GAVCERTO = {u"m": u"É manchete — curta e lá do alto.",
             u"g": u"É legenda — ela explica a foto.",
             u"n": u"É notícia — conta o que aconteceu.",
             u"c": u"É convite — chama você."}
_GAVDICA = {u"gA": u"Manchete não tem ponto no fim e é bem curta. Legenda é uma frase "
                   u"inteira sobre a foto.",
            u"gB": u"Pergunte: isto já aconteceu, ou ainda vai acontecer e está "
                   u"chamando você?"}
for _pi, _gk in ((17, u"gA"), (18, u"gB")):
    for _n, _k in enumerate(pote(_pi)):
        _X = GAV[_gk][u"pal"][_k]
        _fr = lp(_X[u"p"])
        _fr = _fr[0].upper() + _fr[1:]
        if _fr[-1:] not in u".!?":
            _fr += u"."
        p(u"diz2_%s_%s" % (_gk, _k), _fr)
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" " + _fr + u" " + _GAVCERTO[_X[u"c"]])
        p(u"dica%d_%s" % (_pi, _k), _GAVDICA[_gk])

# --- 28 e 29: os caça-palavras ---------------------------------------------------
for _pi, _nome in ((28, u"CACA"), (29, u"CACA2")):
    _C = bloco(_nome)
    for _n, _k in enumerate(pote(_pi)):
        _P = _C[u"pal"][_k]
        p(u"cp_" + _k, _P[u"pista"][0].upper() + _P[u"pista"][1:] + u".")
        p(u"certo%d_%s" % (_pi, _k), elogio(_n) + u" Achou.")

# --- 30: a cruzadinha -------------------------------------------------------------
CRZD = bloco(u"CRZD")
for _n, _k in enumerate(pote(30)):
    _P = CRZD[_k]
    p(u"crz_" + _k, lp(_P[u"d"]) + u".")
    _di = lp(_P[u"d"])
    _di = _di[0].upper() + _di[1:]
    p(u"certo30_" + _k, elogio(_n) + u" " + _di + u": " + _P[u"p"].capitalize() + u".")
    p(u"dica30_" + _k, u"Conte as casinhas e lembre da página de jornal.")

# --- 35: o cartaz — os nomes vêm por último ---------------------------------------
CART = bloco(u"CART")
for _L in CART[u"linhas"]:
    p(u"cart_" + _L[u"k"], u"%s: %s. Por exemplo, %s" % (_L[u"t"].capitalize(),
                                                         lp(_L[u"d"]), lp(_L[u"e"])))
# ⚠️ MAIÚSCULA de novo: a explicação vem depois do ponto final do exemplo.
_CARTCERTO = {u"m": u"É a manchete — o título curto lá do alto.",
              u"g": u"É a legenda — a frase que explica a foto.",
              u"f": u"É a foto — a imagem do que aconteceu.",
              u"l": u"É o lide — o começo, que diz o quê, quem, quando e onde."}
for _n, _k in enumerate(pote(35)):
    _X = CART[u"exem"][_k]
    _ex = lp(_X[u"p"])
    _ex = _ex[0].upper() + _ex[1:]
    if _ex[-1:] not in u".!?":
        _ex += u"."
    p(u"ex_" + _k, _ex)
    p(u"certo35_" + _k, elogio(_n) + u" " + _ex + u" " + _CARTCERTO[_X[u"c"]])
    p(u"dica35_" + _k, u"Olhe o exemplo que já está em cada linha do cartaz e compare "
                       u"com este.")


# ==============================================================================
#  AS SÍLABAS FALADAS — e este bloco é obrigatório em caderno que fale sílaba
#
#  ⚠️⚠️ POR QUE NÃO DÁ PARA SINTETIZAR A SÍLABA SOLTA (e a casa já pagou por
#     isto DUAS vezes — set/2026 e 16/set/2026, as duas o Marcos ouvindo):
#     a voz não lê SOM, lê PALAVRA. Entregue "SA" a ela e ela soletra "esse-á";
#     "VA" vira "vê-á"; "ÇÃ" ela nem tenta, porque ç não começa palavra em
#     português. Escrever a sílaba "como se fala" conserta UM caso e nunca
#     fecha a família.
#
#  O QUE FUNCIONA é o contrário: gravar a PALAVRA INTEIRA — que a voz pronuncia
#  certo, porque é palavra de verdade — alinhar letra a letra com o
#  `ctc-forced-aligner` e CORTAR a sílaba de dentro dela. Quem faz isso é o
#  `_padrao/silabas_voz.py`, dentro do `entregar.yml`, lendo o `silabas.json`
#  que sai daqui. O portão é o `_qa/silabas.py`.
#
#  COMO SE USA: para cada palavra do caderno, uma linha
#      _reg(u"CAVALO", [u"CA", u"VA", u"LO"])
#  e, no app, a sílaba fala por `falarSilaba(null, 0, "VA")` — nunca por
#  `falar("sil_va")`. Caderno que não fala sílaba não escreve nada: o
#  `silabas.json` sai com `"palavras": {}` e o `entregar.yml` nem baixa o
#  alinhador por ele.
#
#  ⚠️ NÃO HÁ FALA DE RESERVA POR SÍLABA. Faltando o recorte, o app diz a
#     PALAVRA INTEIRA. Uma reserva sintetizada seria o defeito voltando pela
#     porta dos fundos — e calado, que é pior.
# ==============================================================================
_SIL_DE = {}          # palavra -> [sílabas, NA ORDEM da palavra]
_MAPA_SIL = {}        # sílaba  -> [palavra, posição]
_RECUSADAS = []


def _reg(palavra, silabas):
    u"""⚠️ A LISTA TEM DE ESTAR NA ORDEM DA PALAVRA. O alinhador corta pelos
    limites das letras: ["RO","CAR"] para CARRO faz sair "ro" onde devia sair
    "car" — e a criança ouve o pedaço errado, sem erro nenhum na tela. Folha de
    ORDENAR guarda as sílabas EMBARALHADAS: passe-as por `_ordena` antes.
    ⚠️ E ganha sempre a partição MAIS FINA: "PIPO"+"CA" fecha PIPOCA sem ser
    separação silábica, e sobrescrevendo PI-PO-CA deixaria a sílaba PI muda."""
    silabas = list(silabas)
    if u"".join(silabas).upper() != palavra.upper():
        _RECUSADAS.append((palavra, silabas))
        return
    velha = _SIL_DE.get(palavra.lower())
    if velha and len(velha) >= len(silabas):
        return
    _SIL_DE[palavra.lower()] = silabas


def _ordena(palavra, embaralhadas):
    u"""as mesmas sílabas na ORDEM em que formam a palavra — sem inventar
    nenhuma: encaixa da esquerda para a direita e desiste se não fechar."""
    resto, saida, alvo = list(embaralhadas), [], palavra.upper()
    while alvo:
        for _i, _sb in enumerate(resto):
            if alvo.startswith(_sb.upper()):
                saida.append(_sb)
                alvo = alvo[len(_sb):]
                resto.pop(_i)
                break
        else:
            return None
    return saida if not resto else None


def _achaSilaba(s):
    u"""a palavra de onde a sílaba será recortada. Ganha a MAIS CURTA: menos
    letras na gravação, menos lugar para o alinhador errar."""
    cand = [_w for _w in sorted(_SIL_DE) if s in _SIL_DE[_w]]
    if not cand:
        return None
    _w = min(cand, key=lambda w: (len(_SIL_DE[w]), len(w), w))
    return [_w, _SIL_DE[_w].index(s)]


def _mapeia(soltas):
    u"""monta o SILMAP das sílabas que o app fala sozinhas, e DEVOLVE as órfãs.
    ⚠️ Sílaba órfã não é erro — o app diz a palavra inteira — mas tem de sair
    IMPRESSA, senão aquele botão emudece sem ninguém saber. Distratora que não
    mora em palavra nenhuma do caderno pede uma PALAVRA-CARREGADORA: uma
    palavra de verdade, curta, registrada só para ser gravada e cortada."""
    orfas = []
    for _s in sorted(set(soltas)):
        _achou = _achaSilaba(_s)
        if _achou:
            _MAPA_SIL[_s] = _achou
        else:
            orfas.append(_s)
    # e a PALAVRA INTEIRA de cada uma precisa existir como fala: é dela que o
    # recorte sai, e é ela que o app diz quando o recorte falta.
    for _w in sorted(_SIL_DE):
        p(u"pal_" + ch(_w), _w.upper() + u".")
    return orfas


_ORFAS = _mapeia([])          # <- passe aqui TODA sílaba que o app fala sozinha


# ---------------------------------------------------------------------------
# A SAÍDA
# ---------------------------------------------------------------------------
def chave(s):
    u"""O nome do mp3 sai do TEXTO, não da chave da fala — assim duas chaves que
    dizem a mesma frase gravam um arquivo só."""
    s = re.sub(r"\s+", u" ", s or u"").strip().lower()
    hh = 5381
    for c in s:
        hh = ((hh * 33) ^ ord(c)) & 0xFFFFFFFF
    d, out = hh, u""
    if d == 0:
        return u"0"
    while d:
        out = u"0123456789abcdefghijklmnopqrstuvwxyz"[d % 36] + out
        d //= 36
    return out


falas, vistos = [], {}
for k in sorted(F.keys()):
    txt = F[k]
    if not txt:
        continue
    c = chave(txt)
    if c in vistos:
        continue
    vistos[c] = 1
    falas.append({u"id": PREFIXO + c, u"texto": txt, u"voz": VOZ})

html = io.open(CAM, encoding=u"utf-8").read()
blocoF = (u"/*FALAS-INI*/\nvar FALAS = "
          + json.dumps(F, ensure_ascii=False, indent=1, sort_keys=True) + u";\n/*FALAS-FIM*/")
blocoV = (u"/*VOZOK-INI*/var VOZOK = "
          + json.dumps(dict((c, 1) for c in vistos), ensure_ascii=False) + u";/*VOZOK-FIM*/")
novo = re.sub(r"/\*FALAS-INI\*/.*?/\*FALAS-FIM\*/", lambda m: blocoF, html, flags=re.S)
novo = re.sub(r"/\*VOZOK-INI\*/.*?/\*VOZOK-FIM\*/", lambda m: blocoV, novo, flags=re.S)

# ⭐ o `silabas.json` é o que o `entregar.yml` lê para cortar cada sílaba de
#    dentro do mp3 da palavra inteira, e o `SILMAP` é o que o app usa para saber
#    de qual palavra veio cada pedaço. Uma fonte só para os dois.
io.open(os.path.join(AQUI, u"silabas.json"), u"w", encoding=u"utf-8").write(
    json.dumps({u"prefixo": PREFIXO, u"voz": VOZ,
                u"palavras": dict((w, _SIL_DE[w]) for w in sorted(_SIL_DE))},
               ensure_ascii=False, indent=1))
blocoS = (u"/*SILMAP-INI*/var SILMAP = "
          + json.dumps(_MAPA_SIL, ensure_ascii=False, sort_keys=True) + u";/*SILMAP-FIM*/")
novo = re.sub(r"/\*SILMAP-INI\*/.*?/\*SILMAP-FIM\*/", lambda m: blocoS, novo, flags=re.S)
io.open(CAM, u"w", encoding=u"utf-8").write(novo)
io.open(os.path.join(AQUI, u"falas.json"), u"w", encoding=u"utf-8").write(
    json.dumps(falas, ensure_ascii=False, indent=1))
io.open(os.path.join(AQUI, u"voz.txt"), u"w", encoding=u"utf-8").write(VOZ + u"\n")
print(u"FALAS: %d chaves; falas.json: %d fala(s) para gravar; "
      u"silabas: %d palavra(s) para recortar, %d silaba(s) no mapa"
      % (len(F), len(falas), len(_SIL_DE), len(_MAPA_SIL)))
if _ORFAS:
    print(u"   \u26a0\ufe0f %d silaba(s) SEM palavra de origem (o app dira a palavra "
          u"inteira): %s" % (len(_ORFAS), u", ".join(_ORFAS)))
if _RECUSADAS:
    print(u"   \u26a0\ufe0f %d lista(s) recusada(s) por nao formarem a palavra: %s"
          % (len(_RECUSADAS), u", ".join(
              u"%s=%s" % (w, u"-".join(sl)) for w, sl in _RECUSADAS[:8])))
