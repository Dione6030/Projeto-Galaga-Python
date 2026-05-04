import random
import time
import os
import curses
from colorama import init, Fore

init(autoreset=True)

# Apenas use emojis se for no linux, windows não tem suporte completo a emojis com curses no terminal
USE_EMOJI = False

if USE_EMOJI:
    inimigo = "👾"
    obstaculo = "☄️"
    personagem = "🚀"
    tiro = "⚡"
    morte = "💥"
    espaco = "✨"
else:
    inimigo = "M"
    obstaculo = "#"
    personagem = "A"
    tiro = "|"
    morte = "X"
    espaco = "."

vidas = 3
pontuacao = 0

linhas = 15
colunas = 20

tiros = []
explosoes = {}
jogador_col = colunas // 2

print(Fore.RED + "==" + Fore.BLUE + "==" + Fore.GREEN + "==" + Fore.YELLOW + "==" + Fore.CYAN + "==" + Fore.MAGENTA + " JOGO DO GALAGA " + Fore.CYAN + "==" + Fore.YELLOW + "==" + Fore.GREEN + "==" + Fore.BLUE + "==" + Fore.RED + "==")
mostrar_placar = input(Fore.YELLOW + "Deseja ver o placar? (S/N): ").lower()
if mostrar_placar == "s":
    if os.path.isfile("placar_galaga.txt"):
        with open("placar_galaga.txt", "r") as arq:
            dados = arq.readlines()
            
            if dados:
                print()
                print("="*43)
                print(Fore.YELLOW + "------------< PLACAR DO GALAGA >------------")
                print("="*43)
                print(Fore.CYAN + "Nº Nome do Jogador.........: Pontos.: Tempo.:")
                
                for posicao, linha in enumerate(dados, start=1):
                    partes = linha.split(";")
                    print(Fore.WHITE + f"{posicao:2d} {partes[0]:25s}   {int(partes[1]):2d}   {float(partes[2]):6.2f} seg")
            else:
                print(Fore.YELLOW + "Nenhum jogo registrado no placar.")
    else:
        print(Fore.YELLOW + "Placar não encontrado. Jogue para criar um novo placar!")

nome = input(Fore.MAGENTA + "Nome do Jogador: ")

tutorial = input(Fore.YELLOW + "Deseja ver o tutorial? (S/N): ").lower()
if tutorial == "s":
    print(Fore.CYAN + "\nTutorial:")
    print(Fore.GREEN + "1. Use as teclas A e D para mover o foguete (🚀/A) para a esquerda ou direita.")
    print(Fore.GREEN + "2. Use a tecla S para atirar.")
    print(Fore.GREEN + "3. Use a tecla Enter para continuar ou pular turno.")
    print(Fore.GREEN + "4. Evite colidir com os inimigos (👾/M) e obstáculos (🌠/#).")
    print(Fore.GREEN + "5. Destrua os inimigos para ganhar pontos.")
    print(Fore.GREEN + "6. Obstáculos são indestrutíveis.")
    time.sleep(15)

def cria_matriz():
    return [[espaco for _ in range(colunas)] for _ in range(linhas)]

def cria_frame(matriz, jogador_col, tiros):
    frame = [linha[:] for linha in matriz]
    frame[linhas - 1][jogador_col] = sprite_jogador
    for (tiro_linha, tiro_col) in tiros:
        if 0 <= tiro_linha < linhas and 0 <= tiro_col < colunas:
            frame[tiro_linha][tiro_col] = tiro
    return frame

def garante_linhas_colunas(frame, stdscr):
    Y0 = 2
    max_colunas, max_linhas = stdscr.getmaxyx()
    
    for num, linha in enumerate(frame):
        y = Y0 + num
        if y >= max_colunas:
            break
        row = "".join(linha) if USE_EMOJI else " ".join(linha)
        stdscr.addstr(y, 0, row[: max_linhas - 1])


def mostra_matriz(stdscr, matriz, jogador_col, hud, tiros):
    stdscr.clear()
    max_colunas, max_linhas = stdscr.getmaxyx()
    stdscr.addstr(0, 0, hud[: max_linhas - 1])
    
    frame = cria_frame(matriz, jogador_col, tiros)
    garante_linhas_colunas(frame, stdscr)
    stdscr.refresh()

def escolhe_inimigo_obstaculo(linha):
    for num in range(colunas):
        aleatorio = random.random()
        if aleatorio < 0.35:
            linha[num] = inimigo
        elif aleatorio < 0.45:
            linha[num] = obstaculo

def gera_desafio():
    linha = [espaco for _ in range(colunas)]
    escolhe_inimigo_obstaculo(linha)
    return linha

def colisao(matriz, jogador_col):
    return matriz[linhas - 2][jogador_col] in (inimigo, obstaculo)

def coloca_desafio(matriz):
    nova_linha = gera_desafio()
    for num in range(colunas):
        matriz[0][num] = nova_linha[num]

def rola_matriz(matriz, jogador_col):

    for i in range(linhas - 2, 0, -1):
        for j in range(colunas):
            matriz[i][j] = matriz[i - 1][j]
    coloca_desafio(matriz)
    
    for i in range(colunas):
        matriz[linhas -1][i] = espaco

def acerto(linha, col, matriz, duracao=0.25):
    global explosoes
    matriz[linha][col] = morte
    explosoes[(linha, col)] = time.monotonic() + duracao
    return 10

def atualiza_explosoes(matriz):
    now = time.monotonic()
    acabou = [pos for pos, fim in explosoes.items() if now >= fim]
    for (l, c) in acabou:
        if matriz[l][c] == morte:
            matriz[l][c] = espaco
        del explosoes[(l, c)]

def disparar(tiros, jogador_col):
    tiros.append((linhas - 2, jogador_col))

def processa_tiros(matriz, tiros):
    global pontuacao
    novos_tiros = []
    
    for (tiro_linha, tiro_col) in tiros:
        distancia = tiro_linha - 1
        if distancia < 0:
            continue
        
        celula = matriz[distancia][tiro_col]
        if celula == inimigo:
            pontuacao += acerto(distancia, tiro_col, matriz)
        elif celula == obstaculo:
            continue
        else: 
            novos_tiros.append((distancia, tiro_col))
    tiros[:] = novos_tiros

tempo_inicial = time.time()
def main(stdscr):
    global vidas, level, pontuacao, jogador_col, tiros, sprite_jogador
    stdscr.timeout(33)
    matriz = cria_matriz()
    
    tempo_explosao = 0.0
    tempo_invulneravel = 0.0
    
    intervalo_queda = 0.5
    acumula_tempo_queda = 0.0
    ultimo = time.monotonic()
    
    try:
        curses.curs_set(0)
    except Exception:
        pass
    
    while vidas > 0:
        now = time.monotonic()
        dt = now - ultimo
        ultimo = now
        acumula_tempo_queda += dt
        
        sprite_jogador = morte if now < tempo_explosao else personagem
        
        hud = (f"Jogador: {nome} | Vidas: {'❤️' * max(vidas, 0)} | Pontos: {pontuacao}")
        mostra_matriz(stdscr, matriz, jogador_col, hud, tiros)
        
        key = stdscr.getch()
        if key in [ord('a'), ord('A')]:
            jogador_col = max(0, jogador_col -1)
        elif key in [ord('d'), ord('D')]:
            jogador_col = min(colunas - 1, jogador_col + 1)
        elif key in [ord('s'), ord('S')]:
            disparar(tiros, jogador_col)

        processa_tiros(matriz, tiros)
        atualiza_explosoes(matriz)

        if acumula_tempo_queda >= intervalo_queda:
            acumula_tempo_queda -= intervalo_queda
            rola_matriz(matriz, jogador_col)
            
            if colisao(matriz, jogador_col) and now >= tempo_invulneravel:
                vidas -= 1
                tempo_explosao = now + 0.5
                tempo_invulneravel = tempo_explosao
        
        

if __name__ == "__main__":
    curses.wrapper(main)

print(Fore.RED + "\nGame Over! Você perdeu todas as vidas.")

tempo_final = time.time()
duracao = int(tempo_final - tempo_inicial)

print(Fore.CYAN + f"Tempo de Jogo: {duracao:.2f} segundos")
print(Fore.GREEN + f"Pontuação Final: {pontuacao} pontos")

dados = []
if os.path.isfile("placar_galaga.txt"):
    with open("placar_galaga.txt", "r") as arq:
        dados = arq.readlines()

dados.append(f"{nome};{pontuacao};{duracao:.2f}\n")

with open("placar_galaga.txt", "a+") as arq:
    arq.write(f"{nome};{pontuacao};{duracao:.2f}\n")

ranking = sorted(dados, key=lambda x: (int(x.split(';')[1]), float(x.split(';')[2]) * -1), reverse=True)

print()
print("="*43)
print(Fore.YELLOW + "------------< PLACAR DO GALAGA >------------")
print("="*43)
print(Fore.CYAN + "Nº Nome do Jogador.........: Pontos.: Tempo.:")

posicao = 0
for posicao, linha in enumerate(ranking, start=1):
    partes = linha.split(";")
    
    if partes[0] == nome and int(partes[1]) == pontuacao and float(partes[2]) == duracao:
        print(Fore.RED + f"{posicao:2d} {partes[0]:25s}   {int(partes[1]):2d}   {float(partes[2]):6.2f} seg")
    else:
        print(Fore.WHITE + f"{posicao:2d} {partes[0]:25s}   {int(partes[1]):2d}   {float(partes[2]):6.2f} seg")