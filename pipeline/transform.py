import pandas as pd
import os
import logging
import time
from datetime import datetime
from deltalake import DeltaTable
from database.connection import get_engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def carregar_bronze(nome: str) -> pd.DataFrame:
    caminho = f"data/bronze/{nome}"
    if not os.path.exists(caminho):
        print(f"[SILVER] Caminho não encontrado: {caminho}")
        return pd.DataFrame()
    dt = DeltaTable(caminho)
    df = dt.to_pandas()
    print(f"[SILVER] {len(df)} registros carregados de {nome} (versão {dt.version()})")
    return df

def transformar_movies(df_detalhes: pd.DataFrame) -> pd.DataFrame:
    colunas = {
        "id": "id",
        "title": "title",
        "original_title": "original_title",
        "release_date": "release_date",
        "original_language": "original_language",
        "popularity": "popularity",
        "vote_average": "vote_average",
        "vote_count": "vote_count",
        "budget": "budget",
        "revenue": "revenue",
        "runtime": "runtime",
        "status": "status",
        "tagline": "tagline",
        "overview": "overview",
    }

    colunas_existentes = {k: v for k, v in colunas.items() if k in df_detalhes.columns}
    df = df_detalhes[list(colunas_existentes.keys())].copy()
    df.rename(columns=colunas_existentes, inplace=True)

    # Coleção
    if "belongs_to_collection.id" in df_detalhes.columns:
        df["collection_id"] = df_detalhes["belongs_to_collection.id"]
        df["collection_name"] = df_detalhes["belongs_to_collection.name"]
    else:
        df["collection_id"] = None
        df["collection_name"] = None

    #Tipagem
    df = df.dropna(subset=["id"])
    df["id"] = df["id"].astype(int)
    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce").fillna(0).astype(int)
    df["budget"] = pd.to_numeric(df["budget"], errors="coerce").fillna(0).astype(int)
    df["revenue"] = pd.to_numeric(df["revenue"], errors="coerce").fillna(0).astype(int)
    df["runtime"] = pd.to_numeric(df["runtime"], errors="coerce").fillna(0).astype(int)
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce")
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")

    #Limpeza
    df.drop_duplicates(subset="id", inplace=True)
    df.dropna(subset=["id", "title"], inplace=True)

    df["query"] = "tmdb_pipeline"
    df["loaded_at"] = datetime.now()

    return df

def transformar_tv_shows(df_detalhes: pd.DataFrame) -> pd.DataFrame:
    colunas = {
        "id": "id",
        "name": "name",
        "original_name": "original_name",
        "first_air_date": "first_air_date",
        "last_air_date": "last_air_date",
        "original_language": "original_language",
        "popularity": "popularity",
        "vote_average": "vote_average",
        "vote_count": "vote_count",
        "number_of_seasons": "number_of_seasons",
        "number_of_episodes": "number_of_episodes",
        "in_production": "in_production",
        "status": "status",
        "type": "type",
        "tagline": "tagline",
        "overview": "overview",
    }

    colunas_existentes = {k: v for k, v in colunas.items() if k in df_detalhes.columns}
    df = df_detalhes[list(colunas_existentes.keys())].copy()
    df.rename(columns=colunas_existentes, inplace=True)

    #Tipagem
    df = df.dropna(subset=["id"])
    df["id"] = df["id"].astype(int)
    df["vote_count"] = pd.to_numeric(df["vote_count"], errors="coerce").fillna(0).astype(int)
    df["number_of_seasons"] = pd.to_numeric(df["number_of_seasons"], errors="coerce").fillna(0).astype(int)
    df["number_of_episodes"] = pd.to_numeric(df["number_of_episodes"], errors="coerce").fillna(0).astype(int)
    df["popularity"] = pd.to_numeric(df["popularity"], errors="coerce")
    df["vote_average"] = pd.to_numeric(df["vote_average"], errors="coerce")
    df["in_production"] = df["in_production"].astype(bool)
    df["first_air_date"] = pd.to_datetime(df["first_air_date"], errors="coerce")
    df["last_air_date"] = pd.to_datetime(df["last_air_date"], errors="coerce")

    #Limpeza
    df.drop_duplicates(subset="id", inplace=True)
    df.dropna(subset=["id", "name"], inplace=True)

    df["query"] = "tmdb_pipeline"
    df["loaded_at"] = datetime.now()

    return df

import numpy as np

def transformar_generos(df_detalhes: pd.DataFrame, id_col: str, tabela_col: str) -> pd.DataFrame:
    registros = []
    for _, row in df_detalhes.iterrows():
        generos = row.get("genres")
        if isinstance(generos, np.ndarray):
            generos = generos.tolist()
        elif isinstance(generos, str):
            try:
                import ast
                generos = ast.literal_eval(generos)
            except Exception:
                continue

        if isinstance(generos, list):
            for genero in generos:
                registros.append({
                    tabela_col: row[id_col],
                    "genre_id": genero.get("id"),
                    "genre_name": genero.get("name"),
                    "loaded_at": datetime.now()
                })
    return pd.DataFrame(registros)

def transformar_cast(df: pd.DataFrame, id_col: str, tabela_col: str) -> pd.DataFrame:
    colunas = {
        id_col: tabela_col,
        "id": "person_id",
        "name": "name",
        "character": "character",
        "order": "cast_order",
        "popularity": "popularity",
    }
    colunas_existentes = {k: v for k, v in colunas.items() if k in df.columns}
    resultado = df[list(colunas_existentes.keys())].rename(columns=colunas_existentes)
    resultado["loaded_at"] = datetime.now()
    resultado.drop_duplicates(inplace=True)
    return resultado

def transformar_crew(df: pd.DataFrame, id_col: str, tabela_col: str) -> pd.DataFrame:
    colunas = {
        id_col: tabela_col,
        "id": "person_id",
        "name": "name",
        "job": "job",
        "department": "department",
        "popularity": "popularity",
    }
    colunas_existentes = {k: v for k, v in colunas.items() if k in df.columns}
    resultado = df[list(colunas_existentes.keys())].rename(columns=colunas_existentes)
    resultado["loaded_at"] = datetime.now()
    resultado.drop_duplicates(inplace=True)
    return resultado

def transformar_networks(df_detalhes: pd.DataFrame) -> pd.DataFrame:
    registros = []
    for _, row in df_detalhes.iterrows():
        networks = row.get("networks")

        if isinstance(networks, np.ndarray):
            networks = networks.tolist()

        if isinstance(networks, list):
            for network in networks:
                registros.append({
                    "tv_show_id": row["id"],
                    "network_id": network.get("id"),
                    "network_name": network.get("name"),
                    "origin_country": network.get("origin_country"),
                    "loaded_at": datetime.now()
                })
    df = pd.DataFrame(registros)
    df.drop_duplicates(subset=["tv_show_id", "network_id"], inplace=True)
    return df        

def transformar_seasons(df_detalhes: pd.DataFrame) -> pd.DataFrame:
    registros = []
    for _, row in df_detalhes.iterrows():
        seasons = row.get("seasons")

        if isinstance(seasons, np.ndarray):
            seasons = seasons.tolist()

        if isinstance(seasons, list):
            for season in seasons:
                registros.append({
                    "tv_show_id": row["id"],
                    "season_id": season.get("id"),
                    "season_number": season.get("season_number"),
                    "name": season.get("name"),
                    "air_date": season.get("air_date"),
                    "episode_count": season.get("episode_count"),
                    "vote_average": season.get("vote_average"),
                    "loaded_at": datetime.now()
                })
    df = pd.DataFrame(registros)
    df.drop_duplicates(subset=["tv_show_id", "season_id"], inplace=True)
    return df

def salvar_silver(df: pd.DataFrame, tabela: str):
    if df.empty:
        print(f"[SILVER] DataFrame vazio, pulando {tabela}")
        return
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tabela} CASCADE"))
    df.to_sql(tabela, engine, if_exists="append", index=False, method="multi")
    print(f"[SILVER] {len(df)} registros salvos em {tabela}")

def executar_silver():
    inicio = time.time()
    
    logger.info("======================================")
    logger.info("[SILVER] Iniciando transformação")
    logger.info("======================================")

    #Filmes
    df_movie_details = carregar_bronze("filmes_detalhes")

    if not df_movie_details.empty:
        df_movies = transformar_movies(df_movie_details)
        salvar_silver(df_movies, "silver_movies")

        df_movie_genres = transformar_generos(df_movie_details, "id", "movie_id")
        salvar_silver(df_movie_genres, "silver_movie_genres")

    df_movie_cast = carregar_bronze("filmes_elenco")
    if not df_movie_cast.empty:
        df_cast = transformar_cast(df_movie_cast, "filme_id", "movie_id")
        salvar_silver(df_cast, "silver_movie_cast")

    df_movie_crew = carregar_bronze("filmes_equipe")
    if not df_movie_crew.empty:
        df_crew = transformar_crew(df_movie_crew, "filme_id", "movie_id")
        salvar_silver(df_crew, "silver_movie_crew")

    #Séries
    df_tv_details = carregar_bronze("series_detalhes")
    if not df_tv_details.empty:
        df_tv = transformar_tv_shows(df_tv_details)
        salvar_silver(df_tv, "silver_tv_shows")

        df_tv_genres = transformar_generos(df_tv_details, "id", "tv_show_id")
        salvar_silver(df_tv_genres, "silver_tv_genres")

        df_networks = transformar_networks(df_tv_details)
        salvar_silver(df_networks, "silver_tv_networks")

        df_seasons = transformar_seasons(df_tv_details)
        salvar_silver(df_seasons, "silver_tv_seasons")

    df_tv_cast = carregar_bronze("series_elenco")
    if not df_tv_cast.empty:
        df_cast_tv = transformar_cast(df_tv_cast, "serie_id", "tv_show_id")
        salvar_silver(df_cast_tv, "silver_tv_cast")

    df_tv_crew = carregar_bronze("series_equipe")
    if not df_tv_crew.empty:
        df_crew_tv = transformar_crew(df_tv_crew, "serie_id", "tv_show_id")
        salvar_silver(df_crew_tv, "silver_tv_crew")

    fim = time.time()

    logger.info("======================================")
    logger.info("[SILVER] Transformação concluída")
    logger.info(f"[SILVER] Tempo total: {round((fim - inicio)/60, 2)} minutos")
    logger.info(f"[SILVER] Filmes processados: {len(df_movies) if 'df_movies' in locals() else 0}")
    logger.info(f"[SILVER] Séries processadas: {len(df_tv) if 'df_tv' in locals() else 0}")
    logger.info("======================================")

if __name__ == "__main__":
    executar_silver()