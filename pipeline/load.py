import pandas as pd
import logging
import time
from sqlalchemy import text
from datetime import datetime
from database.connection import get_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def carregar_silver(tabela: str) -> pd.DataFrame:
    engine = get_engine()
    try:
        df = pd.read_sql(f"SELECT * FROM {tabela}", engine)
        print(f"[GOLD] {len(df)} registros carregados de {tabela}")
        return df
    except Exception as e:
        print(f"[GOLD] Erro ao carregar {tabela}: {e}")
        return pd.DataFrame()

def salvar_gold(df: pd.DataFrame, tabela: str):
    if df.empty:
        print(f"[GOLD] DataFrame vazio, pulando {tabela}")
        return
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {tabela} CASCADE"))
    df.to_sql(tabela, engine, if_exists="append", index=False, method="multi")
    print(f"[GOLD] {len(df)} registros salvos em {tabela}")  

def transformar_dim_date(df_movies: pd.DataFrame, df_tv: pd.DataFrame) -> pd.DataFrame:
    datas = []
 
    if not df_movies.empty:
        datas += pd.to_datetime(df_movies["release_date"], errors="coerce").dropna().tolist()
 
    if not df_tv.empty:
        datas += pd.to_datetime(df_tv["first_air_date"], errors="coerce").dropna().tolist()
 
    if not datas:
        return pd.DataFrame()
 
    df = pd.DataFrame({"data": datas}).drop_duplicates()
    df["year"] = df["data"].dt.year.astype(int)
    df["month"] = df["data"].dt.month.astype(int)
    df["quarter"] = df["data"].dt.quarter.astype(int)
    df["decade"] = (df["year"] // 10 * 10).astype(int)
    df["date_id"] = df["year"] * 100 + df["month"]
    df["full_date"] = df["data"].dt.date
 
    return df[["date_id", "year", "month", "quarter", "decade", "full_date"]].drop_duplicates(subset="date_id")

def transformar_dim_movie_genre(df_movie_genres: pd.DataFrame, df_movies: pd.DataFrame) -> pd.DataFrame:

    if df_movie_genres.empty or df_movies.empty:
        return pd.DataFrame()

    merged = df_movie_genres.merge(
        df_movies[["id", "vote_average", "popularity"]],
        left_on="movie_id",
        right_on="id",
        how="left"
    )

    registros = []

    for (gid, gname), grupo in merged.groupby(["genre_id", "genre_name"]):
        registros.append({
            "genre_id": gid,
            "genre_name": gname,
            "total_movies": grupo["movie_id"].nunique(),
            "avg_vote": round(grupo["vote_average"].mean(), 2),
            "avg_popularity": round(grupo["popularity"].mean(), 2),
            "generated_at": datetime.now()
        })

    return pd.DataFrame(registros)

def transformar_dim_tv_genre(df_tv_genres: pd.DataFrame, df_tv: pd.DataFrame) -> pd.DataFrame:

    if df_tv_genres.empty or df_tv.empty:
        return pd.DataFrame()

    merged = df_tv_genres.merge(
        df_tv[["id", "vote_average", "popularity"]],
        left_on="tv_show_id",
        right_on="id",
        how="left"
    )

    registros = []

    for (gid, gname), grupo in merged.groupby(["genre_id", "genre_name"]):
        registros.append({
            "genre_id": gid,
            "genre_name": gname,
            "total_tv_shows": grupo["tv_show_id"].nunique(),
            "avg_vote": round(grupo["vote_average"].mean(), 2),
            "avg_popularity": round(grupo["popularity"].mean(), 2),
            "generated_at": datetime.now()
        })

    return pd.DataFrame(registros)

def transformar_dim_person(df_movie_cast: pd.DataFrame, df_movie_crew: pd.DataFrame,
    df_tv_cast: pd.DataFrame, df_tv_crew: pd.DataFrame,
    df_movies: pd.DataFrame, df_tv: pd.DataFrame) -> pd.DataFrame:
    registros = {}

    def processar(df, id_col, tipo, role, df_ref):
        if df.empty or df_ref.empty:
            return
        merged = df.merge(
        df_ref[["id", "vote_average", "popularity"]].rename(columns={"popularity":"content_popularity","vote_average":  "content_vote_average"}),
        left_on=id_col,
        right_on="id",
        how="left"
    )
        
        for person_id, grupo in merged.groupby("person_id"):
            chave = (person_id, role)

            person_popularity = (
                round(grupo["content_popularity"].mean(), 2)
                if "content_popularity" in grupo.columns
                else 0
            )

            if chave not in registros:
                registros[chave] = {
                    "person_id": person_id,
                    "name": grupo["name"].iloc[0],
                    "role": role,
                    "total_movies": 0,
                    "total_tv_shows": 0,
                    "avg_vote": 0,
                    "avg_popularity": 0,
                    "generated_at": datetime.now(),
                    "person_popularity": person_popularity
                }
            registros[chave][f"total_{tipo}s"] += grupo[id_col].nunique()
            registros[chave]["avg_vote"] = round(grupo["content_vote_average"].mean(), 2)
            registros[chave]["avg_popularity"] = round(grupo["content_popularity"].mean(), 2)

    processar(df_movie_cast, "movie_id", "movie", "actor", df_movies)
    processar(df_tv_cast, "tv_show_id", "tv_show", "actor", df_tv)
    processar(df_movie_crew, "movie_id", "movie", "crew", df_movies)
    processar(df_tv_crew, "tv_show_id", "tv_show", "crew", df_tv)

    return pd.DataFrame(list(registros.values()))

def transformar_dim_time(df_movies: pd.DataFrame, df_tv: pd.DataFrame) -> pd.DataFrame:
    registros = {}

    if not df_movies.empty:
        df_movies["release_year"] = pd.to_datetime(df_movies["release_date"], errors="coerce").dt.year
        df_movies["release_month"] = pd.to_datetime(df_movies["release_date"], errors="coerce").dt.month
        for (year, month), grupo in df_movies.groupby(["release_year", "release_month"]):
            chave = (year, month)
            if chave not in registros:
                registros[chave] = {
                    "year": year, "month": month,
                    "decade": int(year // 10 * 10),
                    "total_movies": 0, "total_tv_shows": 0,
                    "avg_movie_vote": 0, "avg_tv_vote": 0,
                    "generated_at": datetime.now()
                }
            registros[chave]["total_movies"] += len(grupo)
            registros[chave]["avg_movie_vote"] = round(grupo["vote_average"].mean(), 2)

    if not df_tv.empty:
        df_tv["first_air_year"] = pd.to_datetime(df_tv["first_air_date"], errors="coerce").dt.year
        df_tv["first_air_month"] = pd.to_datetime(df_tv["first_air_date"], errors="coerce").dt.month
        for (year, month), grupo in df_tv.groupby(["first_air_year", "first_air_month"]):
            chave = (year, month)
            if chave not in registros:
                registros[chave] = {
                    "year": year, "month": month,
                    "decade": int(year // 10 * 10),
                    "total_movies": 0, "total_tv_shows": 0,
                    "avg_movie_vote": 0, "avg_tv_vote": 0,
                    "generated_at": datetime.now()
                }
            registros[chave]["total_tv_shows"] += len(grupo)
            registros[chave]["avg_tv_vote"] = round(grupo["vote_average"].mean(), 2)

    return pd.DataFrame(list(registros.values()))

def transformar_dim_network(df_networks: pd.DataFrame, df_tv: pd.DataFrame) -> pd.DataFrame:
    if df_networks.empty or df_tv.empty:
        return pd.DataFrame()

    merged = df_networks.merge(df_tv[["id", "vote_average", "popularity"]], left_on="tv_show_id", right_on="id", how="left")

    registros = []

    for network_id, grupo in merged.groupby("network_id"):
        registros.append({
            "network_id": network_id,
            "network_name": grupo["network_name"].iloc[0],
            "origin_country": grupo["origin_country"].iloc[0],
            "total_tv_shows": grupo["tv_show_id"].nunique(),
            "avg_vote": round(grupo["vote_average"].mean(), 2),
            "avg_popularity": round(grupo["popularity"].mean(), 2),
            "generated_at": datetime.now()
        })

    return pd.DataFrame(registros)

def transformar_fact_movies(df: pd.DataFrame, df_movie_genres: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    
    resultado = df.copy()
    resultado = resultado.rename(columns={"id": "movie_id"})
    resultado["release_year"]  = pd.to_datetime(resultado["release_date"], errors="coerce").dt.year
    resultado["release_month"] = pd.to_datetime(resultado["release_date"], errors="coerce").dt.month
    resultado["decade"]  = resultado["release_year"].fillna(0).astype(int) // 10 * 10
    resultado["date_id"] = resultado["release_year"].fillna(0).astype(int) * 100 + resultado["release_month"].fillna(0).astype(int)
    resultado["profit"]  = resultado["revenue"] - resultado["budget"]
    resultado["roi"]     = resultado.apply(
        lambda row: round((row["profit"] / row["budget"]) * 100, 2)
        if row["budget"] and row["budget"] > 0 else None, axis=1
    )
    resultado["full_date"] = resultado["release_date"]
    resultado = resultado.merge(df_movie_genres[["movie_id", "genre_id"]], on="movie_id", how="left")
    resultado = resultado.dropna(subset=["genre_id"])
    resultado["genre_id"] = resultado["genre_id"].astype(int)
    resultado["generated_at"] = datetime.now()

    colunas = ["movie_id", "genre_id", "title", "overview", "poster_url", "backdrop_url", "release_year", "release_month", "decade", "full_date", "date_id",
               "popularity", "vote_average", "vote_count", "budget", "revenue", "profit",
               "roi", "runtime", "query", "generated_at"]
    resultado = resultado[[c for c in colunas if c in resultado.columns]]
    resultado.drop_duplicates(subset=["movie_id", "genre_id"], inplace=True)

    print("SHAPE FINAL:", resultado.shape)
    print(resultado.head())
    
    return resultado

def transformar_fact_tv_shows(df: pd.DataFrame, df_tv_genres: pd.DataFrame, df_tv_networks: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    resultado = df.copy()
    resultado = resultado.rename(columns={"id": "tv_show_id"})
    resultado["first_air_year"]  = pd.to_datetime(resultado["first_air_date"], errors="coerce").dt.year
    resultado["first_air_month"] = pd.to_datetime(resultado["first_air_date"], errors="coerce").dt.month
    resultado["decade"]  = resultado["first_air_year"].fillna(0).astype(int) // 10 * 10
    resultado["date_id"] = resultado["first_air_year"].fillna(0).astype(int) * 100 + resultado["first_air_month"].fillna(0).astype(int)
    resultado["full_date"] = resultado["first_air_date"]
    resultado = resultado.merge(df_tv_genres[["tv_show_id", "genre_id"]], on="tv_show_id", how="left")
    resultado = resultado.merge(df_tv_networks[["tv_show_id", "network_id"]], on="tv_show_id", how="left")
    resultado = resultado.dropna(subset=["genre_id", "network_id"])
    resultado["genre_id"] = resultado["genre_id"].astype(int)
    resultado["network_id"] = resultado["network_id"].astype(int)
    resultado["generated_at"] = datetime.now()

    colunas = ["tv_show_id", "genre_id", "name", "overview", "poster_url", "backdrop_url",  "network_id", "first_air_year", "first_air_month", "decade", "full_date", "date_id",
               "popularity", "vote_average", "vote_count", "number_of_seasons",
               "number_of_episodes", "in_production", "query", "generated_at"]
    resultado = resultado[[c for c in colunas if c in resultado.columns]]
    resultado.drop_duplicates(subset=["tv_show_id", "genre_id", "network_id"], inplace=True)

    return resultado

def transformar_bridge_person(
    df_movie_cast, df_movie_crew,
    df_tv_cast, df_tv_crew
):
    # Bridge filmes
    cast_movies = pd.DataFrame()
    if not df_movie_cast.empty:
        cast_movies = df_movie_cast[["movie_id","person_id","name","character","cast_order"]].copy()
        cast_movies["role"] = "actor"
        cast_movies["job"] = None

    crew_movies = pd.DataFrame()
    if not df_movie_crew.empty:
        crew_movies = df_movie_crew[["movie_id","person_id","name","job"]].copy()
        crew_movies["role"] = "crew"
        crew_movies["character"] = None
        crew_movies["cast_order"] = None

    df_bridge_movies = pd.concat([cast_movies, crew_movies], ignore_index=True)
    df_bridge_movies.drop_duplicates(subset=["movie_id","person_id","role"], inplace=True)

    # Bridge séries
    cast_tv = pd.DataFrame()
    if not df_tv_cast.empty:
        cast_tv = df_tv_cast[["tv_show_id","person_id","name","character","cast_order"]].copy()
        cast_tv["role"] = "actor"
        cast_tv["job"] = None

    crew_tv = pd.DataFrame()
    if not df_tv_crew.empty:
        crew_tv = df_tv_crew[["tv_show_id","person_id","name","job"]].copy()
        crew_tv["role"] = "crew"
        crew_tv["character"] = None
        crew_tv["cast_order"] = None

    df_bridge_tv = pd.concat([cast_tv, crew_tv], ignore_index=True)
    df_bridge_tv.drop_duplicates(subset=["tv_show_id","person_id","role"], inplace=True)

    return df_bridge_movies, df_bridge_tv

def executar_gold():
    inicio = time.time()

    logger.info("======================================")
    logger.info("[GOLD] Iniciando agregação")
    logger.info("======================================")

    # Carrega Silver
    df_movies = carregar_silver("silver_movies")
    df_tv = carregar_silver("silver_tv_shows")
    df_movie_genres = carregar_silver("silver_movie_genres")
    df_tv_genres = carregar_silver("silver_tv_genres")
    df_movie_cast = carregar_silver("silver_movie_cast")
    df_tv_cast = carregar_silver("silver_tv_cast")
    df_movie_crew = carregar_silver("silver_movie_crew")
    df_tv_crew = carregar_silver("silver_tv_crew")
    df_tv_networks = carregar_silver("silver_tv_networks")

    #Dimensões
    logger.info("[GOLD] Gerando dim_date...")
    df_dim_date = transformar_dim_date(df_movies, df_tv)
    salvar_gold(df_dim_date, "gold_dim_date")
 
    logger.info("[GOLD] Gerando dim_movie_genre...")
    df_dim_movie_genre = transformar_dim_movie_genre(df_movie_genres, df_movies)
    salvar_gold(df_dim_movie_genre, "gold_dim_movie_genre")

    logger.info("[GOLD] Gerando dim_tv_genre...")
    df_dim_tv_genre = transformar_dim_tv_genre(df_tv_genres, df_tv)
    salvar_gold(df_dim_tv_genre, "gold_dim_tv_genre")
 
    logger.info("[GOLD] Gerando dim_person...")
    df_dim_person = transformar_dim_person(df_movie_cast, df_movie_crew, df_tv_cast, df_tv_crew, df_movies, df_tv)
    salvar_gold(df_dim_person, "gold_dim_person")
 
    logger.info("[GOLD] Gerando fact_time...")
    df_dim_time = transformar_dim_time(df_movies, df_tv)
    salvar_gold(df_dim_time, "gold_fact_time")

    logger.info("[GOLD] Gerando dim_network...")
    df_dim_network = transformar_dim_network(df_tv_networks, df_tv)
    salvar_gold(df_dim_network, "gold_dim_network")

    logger.info("[GOLD] Gerando bridges person...")
    df_bridge_movies, df_bridge_tv = transformar_bridge_person(df_movie_cast, df_movie_crew, df_tv_cast, df_tv_crew)
    salvar_gold(df_bridge_movies, "gold_bridge_movie_person")
    salvar_gold(df_bridge_tv, "gold_bridge_tvshow_person")
 
    #Fatos
    logger.info("[GOLD] Gerando fact_movies...")
    df_fact_movies = transformar_fact_movies(df_movies, df_movie_genres)
    salvar_gold(df_fact_movies, "gold_fact_movies")
 
    logger.info("[GOLD] Gerando fact_tv_shows...")
    df_fact_tv = transformar_fact_tv_shows(df_tv, df_tv_genres, df_tv_networks)
    salvar_gold(df_fact_tv, "gold_fact_tv_shows")

    fim = time.time()

    logger.info("======================================")
    logger.info("[GOLD] Agregação concluída")
    logger.info(f"[GOLD] Tempo total: {round((fim - inicio)/60, 2)} minutos")
    logger.info(f"[GOLD] Dim Date: {len(df_dim_date)}")
    logger.info(f"[GOLD] Bridge Movies: {len(df_bridge_movies)}")
    logger.info(f"[GOLD] Bridge Tv Shows: {len(df_bridge_tv)}") 
    logger.info(f"[GOLD] Dim Genre Movie: {len(df_dim_movie_genre)}")
    logger.info(f"[GOLD] Dim Genre Movie: {len(df_dim_tv_genre)}")
    logger.info(f"[GOLD] Dim Person: {len(df_dim_person)}")
    logger.info(f"[GOLD] Fact Time: {len(df_dim_time)}")
    logger.info(f"[GOLD] Dim Network: {len(df_dim_network)}")
    logger.info(f"[GOLD] Fact Movies: {len(df_fact_movies)}")
    logger.info(f"[GOLD] Fact TV Shows: {len(df_fact_tv)}")
    logger.info("======================================")

if __name__ == "__main__":
    executar_gold()