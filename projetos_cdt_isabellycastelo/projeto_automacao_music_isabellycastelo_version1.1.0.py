import json
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk
from faker import Faker
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Configuração do Faker (para geração de dados fictícios/simulações)
fake = Faker("pt_BR")


WEATHER_API_KEY = "SUA_CHAVE_OPENWEATHER"
CITY_NAME = "Sao Paulo"

SPOTIPY_CLIENT_ID = "SEU_CLIENT_ID_SPOTIFY"
SPOTIPY_CLIENT_SECRET = "SEU_CLIENT_SECRET_SPOTIFY"
SPOTIPY_REDIRECT_URI = "http://localhost:8888/callback"



def inicializar_banco():
    """Cria a tabela no banco de dados SQLite se não existir."""
    conn = sqlite3.connect("historico_playlists.db")
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
    conn.close()


def salvar_historico(data_criacao, humor, clima, nome_playlist, total_musicas):
    """Salva os dados da playlist gerada no SQLite."""
    conn = sqlite3.connect("historico_playlists.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO historico (data_criacao, humor, clima, nome_playlist, total_musicas)
        VALUES (?, ?, ?, ?, ?)
    """,
        (data_criacao, humor, clima, nome_playlist, total_musicas),
    )
    conn.commit()
    conn.close()


def obter_historico_banco():
    """Busca o histórico armazenado no SQLite."""
    conn = sqlite3.connect("historico_playlists.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT data_criacao, humor, clima, nome_playlist, total_musicas FROM historico ORDER BY id DESC"
    )
    registros = cursor.fetchall()
    conn.close()
    return registros


# ==========================================
# LÓGICA DE CLIMA E SPOTIFY
# ==========================================
def obter_clima(cidade, api_key):
    """Consulta a previsão do tempo via OpenWeatherMap."""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_key}&lang=pt_br&units=metric"
        resposta = requests.get(url, timeout=5).json()

        if resposta.get("cod") == 200:
            clima = resposta["weather"][0]["main"].lower()
            return clima
    except Exception as e:
        print(f"Erro ao consultar clima: {e}")
    return "clear"


def mapear_termo_busca(clima, humor):
    """Mapeia clima e humor em termos de pesquisa."""
    termos = {
        "feliz": "happy pop upbeat",
        "triste": "sad acoustic chill",
        "energetico": "rock workout party",
        "calmo": "ambient lofi relax",
        "romantico": "romantic love songs",
        "nostalgico": "80s 90s classics",
    }
    termo = termos.get(humor, "pop")

    if "rain" in clima or "drizzle" in clima:
        termo += " rain chill"
    elif "clear" in clima:
        termo += " summer vibe"

    return termo


# ==========================================
# INTERFACE GRÁFICA (Tkinter)
# ==========================================
class AplicacaoMusica:

    def __init__(self, root):
        self.root = root
        self.root.title("Assistente Musical Inteligente")
        self.root.geometry("520x600")
        self.root.configure(bg="#f0f2f5")

        inicializar_banco()

        # Título
        tk.Label(
            root,
            text="🎵 Assistente Musical",
            font=("Helvetica", 18, "bold"),
            bg="#f0f2f5",
            fg="#1db954",
        ).pack(pady=10)

        # Frame de Seleção
        frame_form = tk.LabelFrame(
            root, text=" Configurações ", bg="#f0f2f5", font=("Helvetica", 10, "bold")
        )
        frame_form.pack(padx=20, pady=10, fill="x")

        # Seleção de Humor
        tk.Label(frame_form, text="Como você está se sentindo?", bg="#f0f2f5").pack(
            anchor="w", padx=10, pady=(10, 2)
        )
        self.combo_humor = ttk.Combobox(
            frame_form,
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
        self.combo_humor.pack(padx=10, pady=5, fill="x")

        # Botão Principal
        self.btn_gerar = tk.Button(
            root,
            text="⚡ Gerar Playlist no Spotify",
            bg="#1db954",
            fg="white",
            font=("Helvetica", 11, "bold"),
            command=self.gerar_playlist,
        )
        self.btn_gerar.pack(padx=20, pady=10, fill="x")

        # Botões Secundários (Faker e JSON)
        frame_acoes = tk.Frame(root, bg="#f0f2f5")
        frame_acoes.pack(padx=20, pady=5, fill="x")

        tk.Button(
            frame_acoes,
            text="🎲 Gerar Teste (Faker)",
            command=self.simular_com_faker,
            width=20,
        ).pack(side="left", padx=5)
        tk.Button(
            frame_acoes,
            text="💾 Exportar JSON",
            command=self.exportar_json,
            width=20,
        ).pack(side="right", padx=5)

        # Tabela de Histórico (Treeview)
        tk.Label(
            root,
            text="📋 Histórico de Playlists Geradas",
            font=("Helvetica", 11, "bold"),
            bg="#f0f2f5",
        ).pack(anchor="w", padx=20, pady=(15, 5))

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
        self.tabela.column("playlist", width=160)
        self.tabela.column("músicas", width=40)

        self.tabela.pack(padx=20, pady=5, fill="both", expand=True)

        self.atualizar_tabela()

    def gerar_playlist(self):
        humor = self.combo_humor.get()
        clima = obter_clima(CITY_NAME, WEATHER_API_KEY)
        termo_busca = mapear_termo_busca(clima, humor)
        nome_playlist = f"Vibe: {humor.capitalize()} ({clima.capitalize()})"

        try:
            sp = spotipy.Spotify(
                auth_manager=SpotifyOAuth(
                    client_id=SPOTIPY_CLIENT_ID,
                    client_secret=SPOTIPY_CLIENT_SECRET,
                    redirect_uri=SPOTIPY_REDIRECT_URI,
                    scope="playlist-modify-public",
                )
            )

            user_id = sp.current_user()["id"]
            resultados = sp.search(q=termo_busca, limit=10, type="track")
            faixas_uris = [
                track["uri"] for track in resultados["tracks"]["items"]
            ]

            if not faixas_uris:
                messagebox.showwarning(
                    "Aviso", "Nenhuma música encontrada no Spotify."
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

            # Grava no SQLite usando a data atual real
            data_atual = fake.date_time_this_minute().strftime(
                "%Y-%m-%d %H:%M"
            )
            salvar_historico(
                data_atual, humor, clima, nome_playlist, len(faixas_uris)
            )

            self.atualizar_tabela()
            messagebox.showinfo(
                "Sucesso", f"Playlist '{nome_playlist}' criada no Spotify!"
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Falha na integração: {e}")

    def simular_com_faker(self):
        """Usa a biblioteca Faker para simular a criação de uma playlist fictícia para testes."""
        humor = self.combo_humor.get()
        clima_falso = fake.random_element(
            elements=("ensolarado", "chuvoso", "nublado")
        )
        data_falsa = fake.date_time_this_month().strftime("%Y-%m-%d %H:%M")
        nome_falso = f"Vibe: {humor.capitalize()} ({fake.word().capitalize()})"
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
        """Atualiza a exibição da tabela com os registros do SQLite."""
        for item in self.tabela.get_children():
            self.tabela.delete(item)

        for linha in obter_historico_banco():
            self.tabela.insert("", "end", values=linha)

    def exportar_json(self):
        """Exporta o histórico do SQLite para um arquivo JSON estruturado."""
        registros = obter_historico_banco()
        dados_json = []

        for item in registros:
            dados_json.append(
                {
                    "data_criacao": item[0],
                    "humor": item[1],
                    "clima": item[2],
                    "nome_playlist": item[3],
                    "total_musicas": item[4],
                }
            )

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
# INICIALIZAÇÃO DO PROGRAMA
# ==========================================
if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacaoMusica(root)
    root.mainloop()