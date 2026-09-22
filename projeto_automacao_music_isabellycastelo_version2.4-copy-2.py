import os
import sqlite3
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# ==========================================
# CONFIGURAÇÕES DO SPOTIFY
# ==========================================
SPOTIPY_CLIENT_ID = "2afb6b4ba69e4aeaa32b965e9c3e51cc"
SPOTIPY_CLIENT_SECRET = "f5a27ecd48e048e7969194bc35c8c8d5"
SPOTIPY_REDIRECT_URI = "http://127.0.0.1:8888/callback"
SCOPE = "playlist-modify-public playlist-modify-private"

# ==========================================
# BANCO DE DADOS LOCAL
# ==========================================
def inicializar_banco():
    with sqlite3.connect("historico_spotify.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_criacao TEXT,
                emocao TEXT,
                nome_playlist TEXT,
                total_musicas INTEGER
            )
            """
        )
        conn.commit()


def salvar_historico(data_criacao, emocao, nome_playlist, total_musicas):
    with sqlite3.connect("historico_spotify.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico (data_criacao, emocao, nome_playlist, total_musicas)
            VALUES (?, ?, ?, ?)
            """,
            (data_criacao, emocao, nome_playlist, total_musicas),
        )
        conn.commit()


def obter_historico():
    with sqlite3.connect("historico_spotify.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data_criacao, emocao, nome_playlist, total_musicas FROM historico ORDER BY id DESC"
        )
        return cursor.fetchall()


# ==========================================
# MAPEAMENTO DE EMOÇÕES
# ==========================================
MAPA_EMOCOES = {
    "😊 Feliz": "pop feliz hits",
    "😢 Triste": "sad acoustic piano",
    "⚡ Energético": "rock workout motivation",
    "🧘 Calmo": "lofi chill relax",
    "❤️ Romântico": "love songs romanticas",
    "🔥 Festa": "party dance hits",
    "📚 Foco / Estudo": "deep focus study beats",
}

# ==========================================
# TEMAS DA INTERFACE (PADRONIZADO)
# ==========================================
TEMAS = {
    "claro": {
        "fundo": "#FFF0F5",          # Rosa Bebê
        "container": "#FFE4E1",      # Rosa Suave
        "btn_primario": "#FFF2A3",   # Amarelo Pastel
        "btn_secundario": "#FFF7C2", # Amarelo Pastel Claro
        "texto": "#4A4A4A",          # Grafite
        "destaque": "#FF69B4",       # HotPink
        "tabela_hdr": "#FFE4E1",
    },
    "escuro": {
        "fundo": "#2A2438",          # Roxo Escuro Profundo
        "container": "#3B3355",      # Roxo Médio
        "btn_primario": "#C77DFF",   # Roxo Claro Neon
        "btn_secundario": "#5C4B7D", # Lilás Sóbrio
        "texto": "#F3E8FF",          # Texto Claro
        "destaque": "#E0AFA0",       # Destaque Quente
        "tabela_hdr": "#5C4B7D",
    },
}


# ==========================================
# APLICAÇÃO PRINCIPAL
# ==========================================
class SpotifyApp:

    def __init__(self, root):
        self.root = root
        self.root.title("Spotify - Gerador de Playlists por Emoção")
        self.root.geometry("600x680")

        self.tema_atual = "escuro"
        self.sp = None

        inicializar_banco()
        self.montar_interface()
        self.aplicar_tema()

    def conectar_spotify(self):
        try:
            auth_manager = SpotifyOAuth(
                client_id=SPOTIPY_CLIENT_ID,
                client_secret=SPOTIPY_CLIENT_SECRET,
                redirect_uri=SPOTIPY_REDIRECT_URI,
                scope=SCOPE,
            )
            self.sp = spotipy.Spotify(auth_manager=auth_manager)
            user_info = self.sp.current_user()
            messagebox.showinfo(
                "Sucesso", f"Conectado como: {user_info['display_name']}"
            )
            self.lbl_status.config(text="🟢 Conectado ao Spotify", fg="#1DB954")
        except Exception as e:
            messagebox.showerror("Erro de Autenticação", f"Falha ao conectar: {e}")

    def alternar_tema(self):
        self.tema_atual = "claro" if self.tema_atual == "escuro" else "escuro"
        self.aplicar_tema()

    def aplicar_tema(self):
        t = TEMAS[self.tema_atual]

        # Atualiza as cores gerais da janela e frames
        self.root.configure(bg=t["fundo"])
        self.frame_main.configure(bg=t["fundo"])
        self.frame_topo.configure(bg=t["fundo"])
        self.lbl_titulo.configure(bg=t["fundo"], fg=t["texto"])
        self.lbl_status.configure(bg=t["fundo"])
        self.frame_card.configure(bg=t["container"])
        self.lbl_emocao.configure(bg=t["container"], fg=t["texto"])
        self.lbl_historico.configure(bg=t["fundo"], fg=t["texto"])

        # Estilo dos Botões
        self.btn_login.configure(bg=t["btn_primario"], fg="#000000" if self.tema_atual == "claro" else "#FFFFFF")
        self.btn_gerar.configure(bg=t["btn_primario"], fg="#000000" if self.tema_atual == "claro" else "#FFFFFF")
        self.btn_tema.configure(
            bg=t["btn_secundario"],
            fg=t["texto"],
            text="☀️ Tema Claro" if self.tema_atual == "escuro" else "🌙 Tema Escuro",
        )

        # Configuração do Estilo da Tabela (Treeview)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background=t["container"],
            fieldbackground=t["container"],
            foreground=t["texto"],
            rowheight=25,
        )
        style.configure(
            "Treeview.Heading",
            background=t["tabela_hdr"],
            foreground=t["texto"],
            font=("Helvetica", 9, "bold"),
        )

    def montar_interface(self):
        self.frame_main = tk.Frame(self.root)
        self.frame_main.pack(fill="both", expand=True, padx=20, pady=15)

        # Topo
        self.frame_topo = tk.Frame(self.frame_main)
        self.frame_topo.pack(fill="x", pady=(0, 15))

        self.lbl_titulo = tk.Label(
            self.frame_topo, text="🎵 Spotify Vibe Maker", font=("Helvetica", 16, "bold")
        )
        self.lbl_titulo.pack(side="left")

        self.btn_tema = tk.Button(
            self.frame_topo,
            command=self.alternar_tema,
            bd=0,
            cursor="hand2",
            padx=10,
            pady=4,
        )
        self.btn_tema.pack(side="right")

        # Status da Conexão
        self.lbl_status = tk.Label(
            self.frame_main,
            text="🔴 Não Conectado (Clique em Conectar)",
            font=("Helvetica", 9, "bold"),
            fg="#FF5555",
        )
        self.lbl_status.pack(anchor="w", pady=(0, 10))

        # Botão de Login
        self.btn_login = tk.Button(
            self.frame_main,
            text="🔑 Conectar Conta do Spotify",
            font=("Helvetica", 10, "bold"),
            bd=0,
            pady=8,
            cursor="hand2",
            command=self.conectar_spotify,
        )
        self.btn_login.pack(fill="x", pady=(0, 15))

        # Card de Seleção de Emoção
        self.frame_card = tk.Frame(self.frame_main, bd=0)
        self.frame_card.pack(fill="x", pady=(0, 15), ipadx=10, ipady=10)

        self.lbl_emocao = tk.Label(
            self.frame_card, text="Escolha a Emoção / Vibe do seu momento:"
        )
        self.lbl_emocao.pack(anchor="w", padx=10, pady=(5, 5))

        self.combo_emocao = ttk.Combobox(
            self.frame_card, values=list(MAPA_EMOCOES.keys()), state="readonly"
        )
        self.combo_emocao.set("😊 Feliz")
        self.combo_emocao.pack(fill="x", padx=10, pady=(0, 10))

        # Botão Gerar Playlist
        self.btn_gerar = tk.Button(
            self.frame_main,
            text="⚡ Criar Playlist no Spotify",
            font=("Helvetica", 11, "bold"),
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.gerar_playlist_async,
        )
        self.btn_gerar.pack(fill="x", pady=(0, 15))

        # Histórico
        self.lbl_historico = tk.Label(
            self.frame_main, text="📋 Histórico de Playlists", font=("Helvetica", 11, "bold")
        )
        self.lbl_historico.pack(anchor="w", pady=(0, 5))

        colunas = ("data", "emocao", "nome", "musicas")
        self.tabela = ttk.Treeview(
            self.frame_main, columns=colunas, show="headings", height=8
        )
        self.tabela.heading("data", text="Data")
        self.tabela.heading("emocao", text="Emoção")
        self.tabela.heading("nome", text="Nome da Playlist")
        self.tabela.heading("musicas", text="Músicas")

        self.tabela.column("data", width=110)
        self.tabela.column("emocao", width=110)
        self.tabela.column("nome", width=240)
        self.tabela.column("musicas", width=60)
        self.tabela.pack(fill="both", expand=True)

        self.atualizar_tabela()

    def gerar_playlist_async(self):
        if not self.sp:
            messagebox.showwarning(
                "Atenção", "Conecte sua conta do Spotify antes de criar uma playlist!"
            )
            return
        threading.Thread(target=self.gerar_playlist, daemon=True).start()

    def gerar_playlist(self):
        emocao_selecionada = self.combo_emocao.get()
        termo_busca = MAPA_EMOCOES[emocao_selecionada]
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M")
        nome_playlist = f"Vibe {emocao_selecionada} - Auto"

        try:
            resultados = self.sp.search(q=termo_busca, type="track", limit=15)
            
            if not resultados or "tracks" not in resultados or not resultados["tracks"]["items"]:
                messagebox.showwarning("Aviso", "Nenhuma música foi encontrada para essa busca.")
                return

            faixas = resultados["tracks"]["items"]
            uris = [faixa["uri"] for faixa in faixas if "uri" in faixa]

            if not uris:
                messagebox.showwarning("Aviso", "Nenhuma faixa válida foi localizada.")
                return

            user_id = self.sp.current_user()["id"]
            playlist = self.sp.user_playlist_create(
                user=user_id,
                name=nome_playlist,
                public=True,
                description=f"Playlist criada automaticamente para a vibe: {emocao_selecionada}",
            )

            self.sp.playlist_add_items(playlist_id=playlist["id"], items=uris)

            salvar_historico(data_atual, emocao_selecionada, nome_playlist, len(uris))
            self.root.after(0, self.atualizar_tabela)

            messagebox.showinfo(
                "Sucesso!", f"Playlist '{nome_playlist}' criada no seu Spotify com sucesso!"
            )

        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao criar a playlist: {e}")

    def atualizar_tabela(self):
        for item in self.tabela.get_children():
            self.tabela.delete(item)
        for linha in obter_historico():
            self.tabela.insert("", "end", values=linha)


if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyApp(root)
    root.mainloop()