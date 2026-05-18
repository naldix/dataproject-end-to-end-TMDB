import requests
import pandas as pd
import os
import time
import logging
from datetime import datetime
from dotenv import load_dotenv
from deltalake.writer import write_deltalake

load_dotenv()

API_KEY = os.getenv("TMDB_API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LISTAS PADRÃO
def buscar_filmes(endpoint: str, paginas: int = 10) -> list:
    filmes = []

    for page in range(1, paginas + 1):
        url = f"{BASE_URL}/movie/{endpoint}"

        params = {
            "api_key": API_KEY,
            "language": "pt-BR",
            "page": page
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        dados = response.json()

        filmes.extend(dados.get("results", []))

        time.sleep(0.3)

    return filmes


def buscar_series(endpoint: str, paginas: int = 10) -> list:
    series = []

    for page in range(1, paginas + 1):
        url = f"{BASE_URL}/tv/{endpoint}"

        params = {
            "api_key": API_KEY,
            "language": "pt-BR",
            "page": page
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        dados = response.json()

        series.extend(dados.get("results", []))

        time.sleep(0.3)

    return series

# DISCOVER
def buscar_discover_movies(paginas: int = 50) -> list:
    filmes = []

    for page in range(1, paginas + 1):
        url = f"{BASE_URL}/discover/movie"

        params = {
            "api_key": API_KEY,
            "language": "pt-BR",
            "sort_by": "popularity.desc",
            "vote_count.gte": 50,
            "page": page
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        dados = response.json()

        filmes.extend(dados.get("results", []))

        time.sleep(0.3)

    return filmes


def buscar_discover_series(paginas: int = 50) -> list:
    series = []

    for page in range(1, paginas + 1):
        url = f"{BASE_URL}/discover/tv"

        params = {
            "api_key": API_KEY,
            "language": "pt-BR",
            "sort_by": "popularity.desc",
            "vote_count.gte": 50,
            "page": page
        }

        response = requests.get(url, params=params)
        response.raise_for_status()

        dados = response.json()

        series.extend(dados.get("results", []))

        time.sleep(0.3)

    return series

# DETALHES
def buscar_detalhes_filme(filme_id: int) -> dict:
    url = f"{BASE_URL}/movie/{filme_id}"

    params = {
        "api_key": API_KEY,
        "language": "pt-BR"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()


def buscar_detalhes_serie(serie_id: int) -> dict:
    url = f"{BASE_URL}/tv/{serie_id}"

    params = {
        "api_key": API_KEY,
        "language": "pt-BR"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()

# CRÉDITOS
def buscar_credits_filme(filme_id: int) -> dict:
    url = f"{BASE_URL}/movie/{filme_id}/credits"

    params = {
        "api_key": API_KEY,
        "language": "pt-BR"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()


def buscar_credits_serie(serie_id: int) -> dict:
    url = f"{BASE_URL}/tv/{serie_id}/credits"

    params = {
        "api_key": API_KEY,
        "language": "pt-BR"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json()

# TRENDING
def buscar_trending(tipo: str) -> list:
    url = f"{BASE_URL}/trending/{tipo}/week"

    params = {
        "api_key": API_KEY,
        "language": "pt-BR"
    }

    response = requests.get(url, params=params)
    response.raise_for_status()

    return response.json().get("results", [])

# SALVAR BRONZE
def salvar_bronze(dados: list, nome: str) -> str:
    if not dados:
        print(f"[BRONZE] Nenhum dado para salvar em {nome}")
        return None

    df = pd.json_normalize(dados)

    df["carregado_em"] = datetime.now().isoformat()

    caminho = f"data/bronze/{nome}"

    os.makedirs(caminho, exist_ok=True)

    write_deltalake(
        caminho,
        df,
        mode="append",
        schema_mode="merge"
    )

    print(f"[BRONZE] {len(df)} registros salvos em: {caminho}")

    return caminho

# PIPELINE BRONZE
def executar_bronze():
    inicio = time.time()

    logger.info("======================================")
    logger.info("[BRONZE] Iniciando extração")
    logger.info("======================================")

    # FILMES
    ids_filmes = set()

    populares = buscar_filmes("popular")
    salvar_bronze(populares, "filmes_populares")
    ids_filmes.update([f["id"] for f in populares])

    top_rated = buscar_filmes("top_rated")
    salvar_bronze(top_rated, "filmes_top_rated")
    ids_filmes.update([f["id"] for f in top_rated])

    trending_filmes = buscar_trending("movie")
    salvar_bronze(trending_filmes, "filmes_trending")
    ids_filmes.update([f["id"] for f in trending_filmes])

    upcoming = buscar_filmes("upcoming")
    salvar_bronze(upcoming, "filmes_upcoming")
    ids_filmes.update([f["id"] for f in upcoming])

    discover_filmes = buscar_discover_movies()
    salvar_bronze(discover_filmes, "filmes_discover")
    ids_filmes.update([f["id"] for f in discover_filmes])

    # DETALHES E CRÉDITOS FILMES
    detalhes_filmes = []
    elenco_filmes = []
    equipe_filmes = []

    for i, filme_id in enumerate(ids_filmes, start=1):
        print(f"[BRONZE] Processando filme {i}/{len(ids_filmes)} - ID {filme_id}")
        try:
            detalhes = buscar_detalhes_filme(filme_id)
            detalhes_filmes.append(detalhes)

            credits = buscar_credits_filme(filme_id)

            for membro in credits.get("cast", []):
                membro["filme_id"] = filme_id
                elenco_filmes.append(membro)

            for membro in credits.get("crew", []):
                membro["filme_id"] = filme_id
                equipe_filmes.append(membro)

            time.sleep(0.3)

        except Exception as e:
            print(f"[BRONZE] Erro no filme {filme_id}: {e}")

    salvar_bronze(detalhes_filmes, "filmes_detalhes")
    salvar_bronze(elenco_filmes, "filmes_elenco")
    salvar_bronze(equipe_filmes, "filmes_equipe")

    # SÉRIES
    ids_series = set()

    populares_s = buscar_series("popular")
    salvar_bronze(populares_s, "series_populares")
    ids_series.update([s["id"] for s in populares_s])

    top_rated_s = buscar_series("top_rated")
    salvar_bronze(top_rated_s, "series_top_rated")
    ids_series.update([s["id"] for s in top_rated_s])

    trending_series = buscar_trending("tv")
    salvar_bronze(trending_series, "series_trending")
    ids_series.update([s["id"] for s in trending_series])

    discover_series = buscar_discover_series()
    salvar_bronze(discover_series, "series_discover")
    ids_series.update([s["id"] for s in discover_series])

    # DETALHES E CRÉDITOS SÉRIES
    detalhes_series = []
    elenco_series = []
    equipe_series = []

    for i, serie_id in enumerate(ids_series, start=1):
        print(f"[BRONZE] Processando série {i}/{len(ids_series)} - ID {serie_id}")
        try:
            detalhes = buscar_detalhes_serie(serie_id)
            detalhes_series.append(detalhes)

            credits = buscar_credits_serie(serie_id)

            for membro in credits.get("cast", []):
                membro["serie_id"] = serie_id
                elenco_series.append(membro)

            for membro in credits.get("crew", []):
                membro["serie_id"] = serie_id
                equipe_series.append(membro)

            time.sleep(0.3)

        except Exception as e:
            print(f"[BRONZE] Erro na série {serie_id}: {e}")

    salvar_bronze(detalhes_series, "series_detalhes")
    salvar_bronze(elenco_series, "series_elenco")
    salvar_bronze(equipe_series, "series_equipe")

    fim = time.time()

    logger.info("======================================")
    logger.info("[BRONZE] Extração concluída")
    logger.info(f"[BRONZE] Tempo total: {round((fim - inicio)/60, 2)} minutos")
    logger.info(f"[BRONZE] Total filmes processados: {len(ids_filmes)}")
    logger.info(f"[BRONZE] Total séries processadas: {len(ids_series)}")
    logger.info("======================================")


if __name__ == "__main__":
    executar_bronze()