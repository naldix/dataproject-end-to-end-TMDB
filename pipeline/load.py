import pandas as pd
import logging
import time
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

def transformar_fact_movies(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    resultado = pd.DataFrame()
    resultado["movie_id"] = df["id"]
    resultado["title"] = df["title"]
    resultado["release_year"] = pd.to_datetime(df["release_date"], errors="coerce").dt.year
    resultado["release_month"] = pd.to_datetime(df["release_date"], errors="coerce").dt.month
    resultado["decade"] = (resultado["release_year"] // 10 * 10).astype("Int64")
    resultado["popularity"] = df["popularity"]
    resultado["vote_average"] = df["vote_average"]
    resultado["vote_count"] = df["vote_count"]
    resultado["budget"] = df["budget"]
    resultado["revenue"] = df["revenue"]
    resultado["profit"] = df["revenue"] - df["budget"]
    resultado["roi"] = resultado.apply(
        lambda row: round((row["profit"] / row["budget"]) * 100, 2)
        if row["budget"] and row["budget"] > 0 else None, axis=1
    )
    resultado["runtime"] = df["runtime"]
    resultado["query"] = df["query"]
    resultado["generated_at"] = datetime.now()

    resultado.drop_duplicates(subset="movie_id", inplace=True)
    return resultado

def transformar_fact_tv_shows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    resultado = pd.DataFrame()
    resultado["tv_show_id"] = df["id"]
    resultado["name"] = df["name"]
    resultado["first_air_year"] = pd.to_datetime(df["first_air_date"], errors="coerce").dt.year
    resultado["first_air_month"] = pd.to_datetime(df["first_air_date"], errors="coerce").dt.month
    resultado["decade"] = (resultado["first_air_year"] // 10 * 10).astype("Int64")
    resultado["popularity"] = df["popularity"]
    resultado["vote_average"] = df["vote_average"]
    resultado["vote_count"] = df["vote_count"]
    resultado["number_of_seasons"] = df["number_of_seasons"]
    resultado["number_of_episodes"]= df["number_of_episodes"]
    resultado["in_production"] = df["in_production"]
    resultado["query"] = df["query"]
    resultado["generated_at"] = datetime.now()

    resultado.drop_duplicates(subset="tv_show_id", inplace=True)
    return resultado

def transformar_dim_genre(df_movie_genres: pd.DataFrame, df_tv_genres: pd.DataFrame, df_movies: pd.DataFrame, df_tv: pd.DataFrame) -> pd.DataFrame:
    registros = []

    #Gêneros de filmes
    if not df_movie_genres.empty and not df_movies.empty:
        merged = df_movie_genres.merge(df_movies[["id", "vote_average", "popularity"]], left_on="movie_id", right_on="id", how="left")
        for (gid, gname), grupo in merged.groupby(["genre_id", "genre_name"]):
            registros.append({
                "genre_id": gid,
                "genre_name": gname,
                "type": "movie",
                "total_titles": grupo["movie_id"].nunique(),
                "avg_vote": round(grupo["vote_average"].mean(), 2),
                "avg_popularity": round(grupo["popularity"].mean(), 2),
                "generated_at": datetime.now()
            })

    #Gêneros de séries
    if not df_tv_genres.empty and not df_tv.empty:
        merged = df_tv_genres.merge(df_tv[["id", "vote_average", "popularity"]], left_on="tv_show_id", right_on="id", how="left")
        for (gid, gname), grupo in merged.groupby(["genre_id", "genre_name"]):
            registros.append({
                "genre_id": gid,
                "genre_name": gname,
                "type": "tv",
                "total_titles": grupo["tv_show_id"].nunique(),
                "avg_vote": round(grupo["vote_average"].mean(), 2),
                "avg_popularity": round(grupo["popularity"].mean(), 2),
                "generated_at": datetime.now()
            })

    return pd.DataFrame(registros)

def transformar_dim_person(df_movie_cast: pd.DataFrame, df_movie_crew: pd.DataFrame,
    df_tv_cast: pd.DataFrame, df_tv_crew: pd.DataFrame,
    df_movies: pd.DataFrame, df_tv: pd.DataFrame) -> pd.DataFrame:
    registros = {}

    def processar(df, id_col, tipo, role, df_ref, ref_id):
        if df.empty or df_ref.empty:
            return
        merged = df.merge(df_ref[["id", "vote_average", "popularity"]], left_on=id_col, right_on="id", how="left", suffixes=("", "_ref"))
        for person_id, grupo in merged.groupby("person_id"):
            chave = (person_id, role)
            if chave not in registros:
                registros[chave] = {
                    "person_id": person_id,
                    "name": grupo["name"].iloc[0],
                    "role": role,
                    "total_movies": 0,
                    "total_tv_shows": 0,
                    "avg_vote": 0,
                    "avg_popularity": 0,
                    "generated_at": datetime.now()
                }
            registros[chave][f"total_{tipo}s"] += grupo[id_col].nunique()
            registros[chave]["avg_vote"] = round(grupo["vote_average"].mean(), 2)
            registros[chave]["avg_popularity"] = round(grupo["popularity_ref"].mean(), 2)

    processar(df_movie_cast, "movie_id", "movie", "actor", df_movies, "id")
    processar(df_tv_cast, "tv_show_id", "tv_show", "actor", df_tv, "id")
    processar(df_movie_crew, "movie_id", "movie", "crew", df_movies, "id")
    processar(df_tv_crew, "tv_show_id", "tv_show", "crew", df_tv, "id")

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

def salvar_gold(df: pd.DataFrame, tabela: str):
    if df.empty:
        print(f"[GOLD] DataFrame vazio, pulando {tabela}")
        return
    engine = get_engine()
    with engine.begin() as conn:
        conn.exec_driver_sql(f"TRUNCATE TABLE {tabela}")
    df.to_sql(tabela, engine, if_exists="append", index=False, method="multi")
    print(f"[GOLD] {len(df)} registros salvos em {tabela}")

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

    #Fatos
    df_fact_movies = transformar_fact_movies(df_movies)
    salvar_gold(df_fact_movies, "gold_fact_movies")

    df_fact_tv = transformar_fact_tv_shows(df_tv)
    salvar_gold(df_fact_tv, "gold_fact_tv_shows")

    #Dimensões
    df_dim_genre = transformar_dim_genre(df_movie_genres, df_tv_genres, df_movies, df_tv)
    salvar_gold(df_dim_genre, "gold_dim_genre")

    df_dim_person = transformar_dim_person(df_movie_cast, df_movie_crew, df_tv_cast, df_tv_crew, df_movies, df_tv)
    salvar_gold(df_dim_person, "gold_dim_person")

    df_dim_time = transformar_dim_time(df_movies, df_tv)
    salvar_gold(df_dim_time, "gold_dim_time")

    fim = time.time()

    logger.info("======================================")
    logger.info("[GOLD] Agregação concluída")
    logger.info(f"[GOLD] Tempo total: {round((fim - inicio)/60, 2)} minutos")
    logger.info(f"[GOLD] Fact Movies: {len(df_fact_movies)}")
    logger.info(f"[GOLD] Fact TV Shows: {len(df_fact_tv)}")
    logger.info(f"[GOLD] Dim Genre: {len(df_dim_genre)}")
    logger.info(f"[GOLD] Dim Person: {len(df_dim_person)}")
    logger.info(f"[GOLD] Dim Time: {len(df_dim_time)}")
    logger.info("======================================")

if __name__ == "__main__":
    executar_gold()