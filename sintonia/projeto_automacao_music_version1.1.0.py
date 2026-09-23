import os
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv

# Carrega credenciais do .env
load_dotenv(override=True)

WEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")
CITY_NAME = "Sao Paulo"


def obter_clima():
    if not WEATHER_API_KEY:
        return "Desconhecido"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={CITY_NAME}&appid={WEATHER_API_KEY}&units=metric&lang=pt_br"
    try:
        res = requests.get(url).json()
        if res.get("cod") == 200:
            return res["weather"][0]["description"].capitalize()
    except Exception:
        pass
    return "Ensolarado"


def inicializar_spotify():
    scope = "user-modify-playback-state user-read-playback-state playlist-modify-public playlist-modify-private"
    try:
        auth = SpotifyOAuth(
            client_id=SPOTIPY_CLIENT_ID,
            client_secret=SPOTIPY_CLIENT_SECRET,
            redirect_uri=SPOTIPY_REDIRECT_URI,
            scope=scope
        )
        return spotipy.Spotify(auth_manager=auth)
    except Exception as e:
        print(f"Erro ao autenticar com o Spotify: {e}")
        return None


def main():
    print("=" * 40)
    print("   ASSISTENTE MUSICAL INTELIGENTE (CLI)")
    print("=" * 40 + "\n")

    clima = obter_clima()
    print(f"📍 Clima atual em {CITY_NAME}: {clima}\n")

    humores = ["Feliz", "Triste", "Energético", "Calmo", "Romântico", "Nostálgico"]
    print("Escolha seu humor:")
    for i, h in enumerate(humores, 1):
        print(f" {i}. {h}")

    opcao = input("\nDigite o número correspondente (1-6): ").strip()
    idx = int(opcao) - 1 if opcao.isdigit() and 1 <= int(opcao) <= 6 else 0
    humor_escolhido = humores[idx]

    artista = input("Digite o nome de um artista (opcional, ou pressione ENTER): ").strip()

    termo = f"{humor_escolhido} {clima}"
    if artista:
        termo = f"{artista} {termo}"

    print(f"\n🔍 Buscando playlist para: '{termo}'...")

    sp = inicializar_spotify()
    if not sp:
        return

    try:
        resultados = sp.search(q=termo, type="playlist", limit=1)
        items = resultados.get("playlists", {}).get("items", [])

        if items:
            playlist = items[0]
            print(f"\n🎵 Playlist Encontrada: {playlist['name']}")
            print(f"🔗 Link: {playlist['external_urls']['spotify']}")

            devices = sp.devices()
            if devices.get("devices"):
                sp.start_playback(context_uri=playlist["uri"])
                print("▶ Reprodução iniciada no seu dispositivo Spotify!")
            else:
                print("⚠️ Abra o app do Spotify em seu computador ou celular para reproduzir.")
        else:
            print("\n❌ Nenhuma playlist encontrada para estes parâmetros.")
    except Exception as e:
        print(f"\nErro ao processar playlist: {e}")


if __name__ == "__main__":
    main()