"""
Tentativa do Youtube Music
"""
import json
import os
import sqlite3
import threading
import tkinter as tk
import webbrowser
from tkinter import messagebox, ttk
from faker import Faker
from ytmusicapi import YTMusic

fake = Faker("pt_BR")
OAUTH_FILE = "oauth.json"


def inicializar_banco():
    with sqlite3.connect("historico_ytmusic.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS historico (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_criacao TEXT,
                humor TEXT,
                nome_playlist TEXT,
                total_musicas INTEGER
            )
            """
        )
        conn.commit()


def salvar_historico(data_criacao, humor, nome_playlist, total_musicas):
    with sqlite3.connect("historico_ytmusic.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO historico (data_criacao, humor, nome_playlist, total_musicas)
            VALUES (?, ?, ?, ?)
            """,
            (data_criacao, humor, nome_playlist, total_musicas),
        )
        conn.commit()


def obter_historico_banco():
    with sqlite3.connect("historico_ytmusic.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT data_criacao, humor, nome_playlist, total_musicas FROM historico ORDER BY id DESC"
        )
        return cursor.fetchall()


def mapear_termo_humor(humor):
    termos = {
        "feliz": "músicas animadas pop",
        "triste": "sad acoustic songs",
        "energetico": "rock treino motivacional",
        "calmo": "lofi relaxante ambient",
        "romantico": "músicas apaixonadas romanticas",
        "nostalgico": "anos 80 e 90 nostalgicas",
        "entediado": "indie pop chill groove",
        "bravo": "heavy metal hard rock agressive",
        "ansioso": "meditation ambient calming sounds",
        "estudando": "lofi hip hop study beats",
        "festa": "funk dance party hits",
        "foco": "deep focus instrumental synthwave",
    }
    return termos.get(humor, "músicas pop")


LISTA_HUMORES = [
    "feliz",
    "triste",
    "energetico",
    "calmo",
    "romantico",
    "nostalgico",
    "entediado",
    "bravo",
    "ansioso",
    "estudando",
    "festa",
    "foco",
]


class AplicacaoYouTubeMusic:

    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Music - Gerador & Player")
        self.root.geometry("550x650")
        self.root.configure(bg="#0F0F0F")

        inicializar_banco()
        self.ytmusic = None

        self.container_principal = tk.Frame(self.root, bg="#0F0F0F")
        self.container_principal.pack(fill="both", expand=True)

        self.verificar_autenticacao_inicial()

    def verificar_autenticacao_inicial(self):
        if os.path.exists(OAUTH_FILE):
            try:
                self.ytmusic = YTMusic(OAUTH_FILE)
                self.exibir_tela_playlists()
                return
            except Exception:
                pass
        self.exibir_tela_login()

    def exibir_tela_login(self):
        self.limpar_container()

        frame_login = tk.Frame(self.container_principal, bg="#0F0F0F")
        frame_login.pack(expand=True)

        lbl_logo = tk.Label(
            frame_login,
            text="▶",
            font=("Helvetica", 60, "bold"),
            fg="#FF0000",
            bg="#0F0F0F",
        )
        lbl_logo.pack(pady=(0, 5))

        lbl_titulo = tk.Label(
            frame_login,
            text="Fazer login no YouTube Music",
            font=("Helvetica", 16, "bold"),
            fg="#FFFFFF",
            bg="#0F0F0F",
        )
        lbl_titulo.pack(pady=5)

        lbl_sub = tk.Label(
            frame_login,
            text="Autentique via navegador para permitir a criação e reprodução de playlists.",
            font=("Helvetica", 10),
            fg="#AAAAAA",
            bg="#0F0F0F",
            wraplength=350,
            justify="center",
        )
        lbl_sub.pack(pady=(0, 20))

        btn_conectar = tk.Button(
            frame_login,
            text="🔒 Conectar Conta Google",
            font=("Helvetica", 11, "bold"),
            bg="#3EA6FF",
            fg="#0F0F0F",
            activebackground="#65B8FF",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.iniciar_oauth_async,
        )
        btn_conectar.pack(pady=10)

    def iniciar_oauth_async(self):
        threading.Thread(target=self.realizar_login_oauth, daemon=True).start()

    def realizar_login_oauth(self):
        try:
            YTMusic.setup(filepath=OAUTH_FILE)
            self.ytmusic = YTMusic(OAUTH_FILE)
            self.root.after(
                0,
                lambda: messagebox.showinfo(
                    "Sucesso", "Conta conectada com sucesso!"
                ),
            )
            self.root.after(0, self.exibir_tela_playlists)
        except Exception as e:
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Erro de Login", f"Falha ao conectar: {e}"
                ),
            )

    def exibir_tela_playlists(self):
        self.limpar_container()

        frame_topo = tk.Frame(self.container_principal, bg="#0F0F0F")
        frame_topo.pack(fill="x", padx=20, pady=(15, 5))

        lbl_titulo = tk.Label(
            frame_topo,
            text="▶ YouTube Music Assistant",
            font=("Helvetica", 15, "bold"),
            fg="#FFFFFF",
            bg="#0F0F0F",
        )
        lbl_titulo.pack(side="left")

        lbl_status = tk.Label(
            frame_topo,
            text="🟢 Conectado",
            font=("Helvetica", 9),
            fg="#00FF7F",
            bg="#0F0F0F",
        )
        lbl_status.pack(side="right")

        frame_form = tk.LabelFrame(
            self.container_principal,
            text=" Seleção de Vibe ",
            font=("Helvetica", 10, "bold"),
            fg="#FFFFFF",
            bg="#212121",
            bd=1,
            relief="solid",
        )
        frame_form.pack(padx=20, pady=10, fill="x")

        lbl_humor = tk.Label(
            frame_form,
            text="Qual vibe você deseja ouvir agora?",
            fg="#FFFFFF",
            bg="#212121",
        )
        lbl_humor.pack(anchor="w", padx=10, pady=(10, 2))

        self.combo_humor = ttk.Combobox(
            frame_form, values=LISTA_HUMORES, state="readonly"
        )
        self.combo_humor.set("feliz")
        self.combo_humor.pack(padx=10, pady=(0, 15), fill="x")

        self.btn_gerar = tk.Button(
            self.container_principal,
            text="⚡ Criar e Tocar Agora",
            font=("Helvetica", 11, "bold"),
            bg="#FF0000",
            fg="#FFFFFF",
            activebackground="#CC0000",
            bd=0,
            pady=8,
            cursor="hand2",
            command=self.iniciar_geracao_async,
        )
        self.btn_gerar.pack(padx=20, pady=5, fill="x")

        frame_acoes = tk.Frame(self.container_principal, bg="#0F0F0F")
        frame_acoes.pack(padx=20, pady=5, fill="x")

        btn_faker = tk.Button(
            frame_acoes,
            text="🎲 Teste (Faker)",
            bg="#383838",
            fg="#FFFFFF",
            bd=0,
            cursor="hand2",
            command=self.simular_com_faker,
        )
        btn_faker.pack(side="left", padx=(0, 5), expand=True, fill="x")

        btn_json = tk.Button(
            frame_acoes,
            text="💾 Exportar JSON",
            bg="#383838",
            fg="#FFFFFF",
            bd=0,
            cursor="hand2",
            command=self.exportar_json,
        )
        btn_json.pack(side="right", padx=(5, 0), expand=True, fill="x")

        lbl_historico = tk.Label(
            self.container_principal,
            text="📋 Histórico de Playlists Geradas",
            font=("Helvetica", 11, "bold"),
            fg="#FFFFFF",
            bg="#0F0F0F",
        )
        lbl_historico.pack(anchor="w", padx=20, pady=(15, 5))

        colunas = ("data", "humor", "playlist", "musicas")
        self.tabela = ttk.Treeview(
            self.container_principal, columns=colunas, show="headings", height=8
        )

        self.tabela.heading("data", text="Data/Hora")
        self.tabela.heading("humor", text="Humor")
        self.tabela.heading("playlist", text="Nome da Playlist")
        self.tabela.heading("musicas", text="Qtd Músicas")

        self.tabela.column("data", width=120)
        self.tabela.column("humor", width=90)
        self.tabela.column("playlist", width=220)
        self.tabela.column("musicas", width=60)

        self.tabela.pack(padx=20, pady=5, fill="both", expand=True)

        self.aplicar_estilo_tabela()
        self.atualizar_tabela()

    def iniciar_geracao_async(self):
        self.btn_gerar.config(
            state="disabled", text="⏳ Gerando e Abrindo Player..."
        )
        threading.Thread(target=self.gerar_e_tocar_playlist, daemon=True).start()

    def gerar_e_tocar_playlist(self):
        humor = self.combo_humor.get()
        termo_busca = mapear_termo_humor(humor)
        nome_playlist = f"Vibe {humor.capitalize()} - YT Music"
        data_atual = fake.date_time_this_minute().strftime("%Y-%m-%d %H:%M")

        try:
            # 1. Busca faixas
            resultados = self.ytmusic.search(
                query=termo_busca, filter="songs", limit=10
            )
            video_ids = [item["videoId"] for item in resultados if "videoId" in item]

            if not video_ids:
                self.root.after(
                    0,
                    lambda: messagebox.showwarning(
                        "Aviso", "Nenhuma música foi encontrada no YouTube."
                    ),
                )
                return

            # 2. Cria a playlist no YouTube Music
            playlist_id = self.ytmusic.create_playlist(
                title=nome_playlist,
                description=f"Playlist gerada automaticamente para a vibe {humor}.",
                video_ids=video_ids,
            )

            # 3. Salva no banco de dados local
            salvar_historico(data_atual, humor, nome_playlist, len(video_ids))
            self.root.after(0, self.atualizar_tabela)

            # 4. Abre o navegador direto na playlist com autostart
            url_playlist = f"https://music.youtube.com/watch?v={video_ids[0]}&list={playlist_id}&play=1"
            webbrowser.open(url_playlist)

        except Exception as e:
            self.root.after(
                0,
                lambda: messagebox.showerror(
                    "Erro", f"Falha ao gerar/tocar playlist: {e}"
                ),
            )
        finally:
            self.root.after(0, self._restaurar_botao_gerar)

    def _restaurar_botao_gerar(self):
        self.btn_gerar.config(state="normal", text="⚡ Criar e Tocar Agora")

    def simular_com_faker(self):
        humor = self.combo_humor.get()
        data_falsa = fake.date_time_this_month().strftime("%Y-%m-%d %H:%M")
        nome_falso = f"Vibe {humor.capitalize()} (Faker)"
        total_musicas = fake.random_int(min=5, max=15)

        salvar_historico(data_falsa, humor, nome_falso, total_musicas)
        self.atualizar_tabela()
        messagebox.showinfo(
            "Simulação", "Registro simulado criado via Faker com sucesso!"
        )

    def atualizar_tabela(self):
        if hasattr(self, "tabela"):
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
                "nome_playlist": item[2],
                "total_musicas": item[3],
            }
            for item in registros
        ]

        try:
            with open("historico_ytmusic.json", "w", encoding="utf-8") as f:
                json.dump(dados_json, f, ensure_ascii=False, indent=4)
            messagebox.showinfo(
                "JSON", "Histórico exportado para 'historico_ytmusic.json'!"
            )
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao exportar JSON: {e}")

    def aplicar_estilo_tabela(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#212121",
            fieldbackground="#212121",
            foreground="#FFFFFF",
            rowheight=25,
            font=("Helvetica", 9),
        )
        style.configure(
            "Treeview.Heading",
            background="#383838",
            foreground="#FFFFFF",
            font=("Helvetica", 9, "bold"),
        )
        style.map("Treeview", background=[("selected", "#FF0000")])

    def limpar_container(self):
        for widget in self.container_principal.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AplicacaoYouTubeMusic(root)
    root.mainloop()