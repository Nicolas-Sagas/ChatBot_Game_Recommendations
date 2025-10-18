# services.py
import os
import requests
import google.generativeai as genai
from dotenv import load_dotenv
from pathlib import Path

caminho_base = Path(__file__).resolve().parent
caminho_env = caminho_base / ".env"
load_dotenv(dotenv_path=caminho_env)

# Dicionário de IDs de busca para cada tipo de dado
SITES_DE_BUSCA = {
    "geral": os.getenv("SEARCH_ENGINE_ID_GERAL"),
    "lojas": os.getenv("SEARCH_ENGINE_ID_LOJAS"),
    "tempo": os.getenv("SEARCH_ENGINE_ID_TEMPO")
}

def configurar_e_obter_modelo_ia():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERRO: A chave GEMINI_API_KEY não foi encontrada no arquivo .env!")
        return None
    try:
        genai.configure(api_key=api_key)
        modelo = genai.GenerativeModel("gemini-pro-latest")
        print("✅ Modelo de IA configurado com sucesso!")
        return modelo
    except Exception as e:
        print(f"ERRO: Não foi possível conectar à IA: {e}")
        return None

def buscar_na_internet(query: str, tipo_busca="geral") -> str:
    """Função de busca aprimorada que pode usar diferentes mecanismos de busca."""
    api_key = os.getenv("SEARCH_API_KEY")
    engine_id = SITES_DE_BUSCA.get(tipo_busca) # Usa o ID correto para o tipo de busca
    
    if not api_key or not engine_id:
        return f"Erro: Configuração da API de Busca para '{tipo_busca}' não encontrada no .env. Verifique a variável SEARCH_ENGINE_ID_{tipo_busca.upper()}."

    print(f"INFO: Buscando por '{query}' no mecanismo '{tipo_busca}'...")
    url = f"https://www.googleapis.com/customsearch/v1?key={api_key}&cx={engine_id}&q={query}&num=3"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "items" not in data or not data["items"]:
            return "Nenhum resultado encontrado."

        resultados_formatados = ""
        for item in data.get("items", []):
            titulo = item.get("title", "")
            trecho = item.get("snippet", "").replace("\n", " ")
            link = item.get("link", "")
            resultados_formatados += f"Título: {titulo}\nTrecho: {trecho}\nLink: {link}\n\n"
        
        return resultados_formatados
    except Exception as e:
        print(f"--- ERRO DETALHADO DA BUSCA ({tipo_busca}) ---\n{e}\n--- FIM DO ERRO ---")
        return f"Ocorreu um erro ao buscar na internet ({tipo_busca})."