import json
import sqlite3
import threading
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
from faker import Faker
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Configuração do Faker
fake = Faker("pt_BR")

# ==========================================
# CONFIGURAÇÕES DE API
# Preencha com suas credenciais do Spotify e OpenWeather.
# Caso deixe os valores padrão ou incorretos, o app operará em modo de simulação visual.
# ==========================================
WEATHER_API_KEY = "SUA_CHAVE_OPENWEATHER"
CITY_NAME = "Sao Paulo"

SPOTIPY_CLIENT_ID = "2afb6b4ba69e4aeaa32b965e9c3e51cc"
SPOTIPY_CLIENT_SECRET = "f5a27ecd48e048e7969194bc35c8c8d5"
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:8888/callback"

# ==========================================
# PALETAS DE CORES (TEMAS)
# ==========================================
TEMAS = {
    "claro": {
        "fundo": "#FFF0F5",  # Rosa Bebê
        "container": "#FFE4E1",  # Rosa Suave
        "btn_primario": "#FFF2A3",  # Amarelo Pastel
        "btn_secundario": "#FFF7C2",  # Amarelo Pastel Claro
        "texto": "#4A4A4A",  # Grafite
        "destaque": "#FF69B4",  # HotPink
        "tabela_hdr": "#FFE4E1",
    },
    "escuro": {
        "fundo": "#2A2438",  # Roxo Escuro Profundo
        "container": "#3B3355",  # Roxo Médio
        "btn_primario": "#C77DFF",  # Roxo Claro Neon
        "btn_secundario": "#5C4B7D",  # Lilás Sóbrio
        "texto": "#F3E8FF",  # Texto Claro
        "destaque": "#E0AFA0",  # Destaque Quente
        "tabela_hdr": "#5C4B7D",
    },
}


# ==========================================
# BANCO DE DADOS
# ==========================================
def inicializar_banco():
    with sqlite3.connect("historico_playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_criacao TEXT,
                humor TEXT,
                clima TEXT,
                nome_playlist TEXT,
                total_musicas INTEGER
            )
            """
        )
        conn.commit()


def salvar_historico(data_criacao, humor, clima, nome_playlist, total_musicas):
    with sqlite3.connect("historico_playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico (data_criacao, humor, clima, nome_playlist, total_musicas)
            VALUES (?, ?, ?, ?, ?)
            """,
            (data_criacao, humor, clima, nome_playlist, total_musicas),
        )
        conn.commit()


def obter_historico_banco():
    with sqlite3.connect("historico_playlists.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data_criacao, humor, clima, nome_playlist, total_musicas FROM historico ORDER BY id DESC"
        )
        return cursor.fetchall()


# ==========================================
# LÓGICA DE CLIMA E NOMES DE PLAYLIST
# ==========================================
def obter_clima(cidade, api_key):
    if api_key == "f190d8a0735419d985475ff1c8262eb2" or not api_key:
        return "ensolarado"
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}&lang=pt_br&units=metric"
        resposta = requests.get(url, timeout=4).json()
        if resposta.get("cod") == 200:
            return resposta["weather"][0]["main"].lower()
    except Exception as e:
        print(f"Aviso OpenWeather: {e}")
    return "ensolarado"


def gerar_nome_playlist_limpo(humor, clima):
    """Gera um nome de playlist limpo, amigável e sem formatações estranhas."""
    humor_cap = humor.capitalize()

    if "rain" in clima or "drizzle" in clima or clima == "chuvoso":
        return f"Sons para um Dia Chuvoso ({humor_cap})"
    elif "clear" in clima or clima == "ensolarado":
        return f" {humor_cap} de Verão"
    elif "cloud" in clima or clima == "nublado":
        return f"Sessão {humor_cap} em Dia Nublado"
    else:
        return f"Playlist {humor_cap}"


def mapear_termo_busca(clima, humor):
    termos = {
        "feliz": "happy pop upbeat",
        "triste": "sad acoustic chill",
        "energetico": "rock workout party",
        "calmo": "ambient lofi relax",
        "romantico": "romantic love songs",
        "nostalgico": "80s 90s classics",
    }
    termo = termos.get(humor, "pop")
    if "rain" in clima or "drizzle" in clima or clima == "chuvoso":
        termo += " rain chill"
    elif "clear" in clima or clima == "ensolarado":
        termo += " summer vibe"
    return termo


# ==========================================
# INTERFACE GRÁFICA (TKINTER)
# ==========================================
class AplicacaoMusica:

    def __init__(self, root):
        self.root = root
        self.root.title("Assistente Musical Inteligente")
        self.root.geometry("640x550")

        self.modo_escuro = False
        self.tema_atual = TEMAS["claro"]

        inicializar_banco()

        # Cabeçalho / Barra Superior
        self.frame_topo = tk.Frame(root)
        self.frame_topo.pack(fill="x", padx=20, pady=(10, 0))

        self.lbl_titulo = tk.Label(
            self.frame_topo,
            text="🎵 Assistente Musical",
            font=("Helvetica", 16, "bold"),
        )
        self.lbl_titulo.pack(side="left")

        self.btn_tema = tk.Button(
            self.frame_topo,
            text="🌙 Modo Escuro",
            font=("Helvetica", 9, "bold"),
            command=self.alternar_tema,
            relief="flat",
            cursor="hand2",
        )
        self.btn_tema.pack(side="right")

        # Configurações / Formulário
        self.frame_form = tk.LabelFrame(
            root,
            text=" Configurações ",
            font=("Helvetica", 10, "bold"),
            bd=1,
            relief="solid",
        )
        self.frame_form.pack(padx=20, pady=10, fill="x")

        self.lbl_humor = tk.Label(
            self.frame_form, text="Como você está se sentindo?"
        )
        self.lbl_humor.pack(anchor="w", padx=10, pady=(10, 2))

        self.combo_humor = ttk.Combobox(
            self.frame_form,
            values=[
                "feliz",
                "triste",
                "energetico",
                "calmo",
                "romantico",
                "nostalgico",
            ],
            state="readonly",
        )
        self.combo_humor.set("feliz")
        self.combo_humor.pack(padx=10, pady=(0, 10), fill="x")

        # Botão Principal (Ação)
        self.btn_gerar = tk.Button(
            root,
            text="⚡ Gerar Playlist no Spotify",
            font=("Helvetica", 11, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.iniciar_geracao_async,
        )
        self.btn_gerar.pack(padx=20, pady=5, fill="x")

        # Botões Secundários
        self.frame_acoes = tk.Frame(root)
        self.frame_acoes.pack(padx=20, pady=5, fill="x")

        self.btn_faker = tk.Button(
            self.frame_acoes,
            text="🎲 Gerar Teste (Faker)",
            relief="flat",
            cursor="hand2",
            command=self.simular_com_faker,
            width=20,
        )
        self.btn_faker.pack(side="left", padx=(0, 5), expand=True, fill="x")

        self.btn_json = tk.Button(
            self.frame_acoes,
            text="💾 Exportar JSON",
            relief="flat",
            cursor="hand2",
            command=self.exportar_json,
            width=20,
        )
        self.btn_json.pack(side="right", padx=(5, 0), expand=True, fill="x")

        # Tabela de Histórico
        self.lbl_historico = tk.Label(
            root,
            text="📋 Histórico de Playlists Geradas",
            font=("Helvetica", 11, "bold"),
        )
        self.lbl_historico.pack(anchor="w", padx=20, pady=(15, 5))

        colunas = ("data", "humor", "clima", "playlist", "músicas")
        self.tabela = ttk.Treeview(
            root, columns=colunas, show="headings", height=8
        )

        self.tabela.heading("data", text="Data/Hora")
        self.tabela.heading("humor", text="Humor")
        self.tabela.heading("clima", text="Clima")
        self.tabela.heading("playlist", text="Nome da Playlist")
        self.tabela.heading("músicas", text="Qtd")

        self.tabela.column("data", width=110)
        self.tabela.column("humor", width=70)
        self.tabela.column("clima", width=70)
        self.tabela.column("playlist", width=180)
        self.tabela.column("músicas", width=40)

        self.tabela.pack(padx=20, pady=5, fill="both", expand=True)

        self.aplicar_tema()
        self.atualizar_tabela()

    # ==========================================
    # SISTEMA DE TEMAS E INTERFACE
    # ==========================================
    def alternar_tema(self):
        self.modo_escuro = not self.modo_escuro
        self.tema_atual = (
            TEMAS["escuro"] if self.modo_escuro else TEMAS["claro"]
        )
        self.btn_tema.config(
            text="☀️ Modo Claro" if self.modo_escuro else "🌙 Modo Escuro"
        )
        self.aplicar_tema()

    def aplicar_tema(self):
        t = self.tema_atual

        self.root.configure(bg=t["fundo"])
        self.frame_topo.configure(bg=t["fundo"])
        self.frame_acoes.configure(bg=t["fundo"])

        self.lbl_titulo.configure(bg=t["fundo"], fg=t["destaque"])
        self.lbl_historico.configure(bg=t["fundo"], fg=t["destaque"])

        self.frame_form.configure(
            bg=t["container"], fg=t["texto"], bd=0
        )
        self.lbl_humor.configure(bg=t["container"], fg=t["texto"])

        self.btn_tema.configure(
            bg=t["container"], fg=t["texto"], activebackground=t["btn_primario"]
        )
        self.btn_gerar.configure(
            bg=t["btn_primario"],
            fg="#222222" if not self.modo_escuro else "#FFFFFF",
            activebackground=t["destaque"],
        )
        self.btn_faker.configure(
            bg=t["btn_secundario"],
            fg=t["texto"],
            activebackground=t["btn_primario"],
        )
        self.btn_json.configure(
            bg=t["btn_secundario"],
            fg=t["texto"],
            activebackground=t["btn_primario"],
        )

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=t["container"],
            fieldbackground=t["container"],
            foreground=t["texto"],
            rowheight=25,
            font=("Helvetica", 9),
        )
        style.configure(
            "Treeview.Heading",
            background=t["tabela_hdr"],
            foreground=t["texto"],
            font=("Helvetica", 9, "bold"),
        )
        style.map("Treeview", background=[("selected", t["destaque"])])

    # ==========================================
    # LÓGICA DE NEGÓCIO E EVENTOS
    # ==========================================
    def iniciar_geracao_async(self):
        self.btn_gerar.config(state="disabled", text="⏳ Conectando...")
        threading.Thread(target=self.gerar_playlist, daemon=True).start()

    def gerar_playlist(self):
        humor = self.combo_humor.get()
        clima = obter_clima(CITY_NAME, WEATHER_API_KEY)
        termo_busca = mapear_termo_busca(clima, humor)
        nome_playlist = gerar_nome_playlist_limpo(humor, clima)

        # Verifica se as credenciais do Spotify foram preenchidas
        if (
            SPOTIPY_CLIENT_ID == "SEU_CLIENT_ID_SPOTIFY"
            or not SPOTIPY_CLIENT_ID
        ):
            # Modo Simulado (sem credenciais de API ativas)
            data_atual = fake.date_time_this_minute().strftime(
                "%Y-%m-%d %H:%M"
            )
            total_faixas = 10
            salvar_historico(
                data_atual, humor, clima, nome_playlist, total_faixas
            )

            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Modo de Simulação",
                    f"Playlist '{nome_playlist}' registrada no histórico!\n\n(Insira chaves válidas do Spotify para sincronizar diretamente na sua conta).",
                ),
            )
            self.root.after(0, self.atualizar_tabela)
            self.root.after(0, self._restaurar_botao_gerar)
            return

        # Tentativa de integração com Spotify via API oficial
        try:
            sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=SPOTIPY_CLIENT_ID,
                    client_secret=SPOTIPY_CLIENT_SECRET,
                    redirect_uri=SPOTIPY_REDIRECT_URI,
                    scope="playlist-modify-public",
                    open_browser=True,
                )
            )

            user_id = sp.current_user()["id"]
            resultados = sp.search(q=termo_busca, limit=10, type="track")
            faixas_uris = [
                track["uri"] for track in resultados["tracks"]["items"]
            ]

            if not faixas_uris:
                self.root.after(
                    0,
                    lambda: messagebox.showwarning(
                        "Aviso", "Nenhuma música encontrada no Spotify."
                    ),
                )
                return

            playlist = sp.user_playlist_create(
                user=user_id,
                name=nome_playlist,
                public=True,
                description="Criada automaticamente por Clima e Humor",
            )
            sp.playlist_add_items(
                playlist_id=playlist["id"], items=faixas_uris
            )

            data_atual = fake.date_time_this_minute().strftime(
                "%Y-%m-%d %H:%M"
            )
            salvar_historico(
                data_atual, humor, clima, nome_playlist, len(faixas_uris)
            )

            self.root.after(0, self._sucesso_geracao, nome_playlist)

        except Exception as e:
            # Em caso de erro de conexão/autenticação no Spotify, registra localmente para não bloquear a aula
            data_atual = fake.date_time_this_minute().strftime(
                "%Y-%m-%d %H:%M"
            )
            salvar_historico(data_atual, humor, clima, nome_playlist, 10)
            self.root.after(0, self.atualizar_tabela)

            self.root.after(
                0,
                lambda: messagebox.showwarning(
                    "Aviso Spotify",
                    f"Playlist gerada e salva localmente!\n(Aviso de conexão API: {e})",
                ),
            )
        finally:
            self.root.after(0, self._restaurar_botao_gerar)

    def _sucesso_geracao(self, nome_playlist):
        self.atualizar_tabela()
        messagebox.showinfo(
            "Sucesso", f"Playlist '{nome_playlist}' criada no Spotify!"
        )

    def _restaurar_botao_gerar(self):
        self.btn_gerar.config(
            state="normal", text="⚡ Gerar Playlist no Spotify"
        )

    def simular_com_faker(self):
        humor = self.combo_humor.get()
        clima_falso = fake.random_element(
            elements=("ensolarado", "chuvoso", "nublado")
        )
        data_falsa = fake.date_time_this_month().strftime("%Y-%m-%d %H:%M")
        nome_falso = gerar_nome_playlist_limpo(humor, clima_falso)
        total_musicas = fake.random_int(min=5, max=15)

        salvar_historico(
            data_falsa, humor, clima_falso, nome_falso, total_musicas
        )
        self.atualizar_tabela()
        messagebox.showinfo(
            "Simulação (Faker)",
            "Registro fictício gerado com sucesso via Faker!",
        )

    def atualizar_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for linha in obter_historico_banco():
            self.tabela.insert("", "end", values=linha)

    def exportar_json(self):
        registros = obter_historico_banco()
        dados_json = [
            {
                "data_criacao": item[0],
                "humor": item[1],
                "clima": item[2],
                "nome_playlist": item[3],
                "total_musicas": item[4],
            }
            for item in registros
        ]

        try:
            with open("historico_playlists.json", "w", encoding="utf-8") as f:
                json.dump(dados_json, f, ensure_ascii=False, indent=4)
            messagebox.showinfo(
                "Exportar JSON",
                "Dados exportados com sucesso para 'historico_playlists.json'!",
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar JSON: {e}")


# ==========================================
# INICIALIZAÇÃO
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacaoMusica(root)
    root.mainloop()