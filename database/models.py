from sqlalchemy import text
from database.connection import get_engine

def criar_tabelas():
    engine = get_engine()

    with engine.begin() as conn:

        #Silver Filmes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_movies (
                id INTEGER PRIMARY KEY,
                title TEXT,
                original_title TEXT,
                release_date DATE,
                original_language TEXT,
                popularity FLOAT,
                vote_average FLOAT,
                vote_count INTEGER,
                budget BIGINT,
                revenue BIGINT,
                runtime INTEGER,
                status TEXT,
                tagline TEXT,
                overview TEXT,
                collection_id INTEGER,
                collection_name TEXT,
                query TEXT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Silver Séries
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_tv_shows (
                id INTEGER PRIMARY KEY,
                name TEXT,
                original_name TEXT,
                first_air_date DATE,
                last_air_date DATE,
                original_language TEXT,
                popularity FLOAT,
                vote_average FLOAT,
                vote_count INTEGER,
                number_of_seasons INTEGER,
                number_of_episodes INTEGER,
                in_production BOOLEAN,
                status  TEXT,
                type TEXT,
                tagline TEXT,
                overview TEXT,
                query TEXT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Silver Gêneros_filmes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_movie_genres (
                movie_id INTEGER,
                genre_id INTEGER,
                genre_name TEXT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Silver Gêneros_séries
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_tv_genres (
                tv_show_id INTEGER,
                genre_id INTEGER,
                genre_name TEXT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Silver Elenco_filmes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_movie_cast (
                movie_id INTEGER,
                person_id INTEGER,
                name TEXT,
                character TEXT,
                cast_order INTEGER,
                popularity FLOAT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Silver Elenco_séries
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_tv_cast (
                tv_show_id INTEGER,
                person_id INTEGER,
                name TEXT,
                character TEXT,
                cast_order INTEGER,
                popularity FLOAT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Silver Equipe_filmes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_movie_crew (
                movie_id INTEGER,
                person_id INTEGER,
                name TEXT,
                job TEXT,
                department TEXT,
                popularity FLOAT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Silver Equipe_séries
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_tv_crew (
                tv_show_id INTEGER,
                person_id INTEGER,
                name TEXT,
                job TEXT,
                department TEXT,
                popularity FLOAT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Silver Redes_plataformas_séries
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_tv_networks (
                tv_show_id INTEGER,
                network_id INTEGER,
                network_name TEXT,
                origin_country TEXT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Silver Temporadas
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS silver_tv_seasons (
                tv_show_id INTEGER,
                season_id INTEGER,
                season_number INTEGER,
                name TEXT,
                air_date DATE,
                episode_count INTEGER,
                vote_average FLOAT,
                loaded_at TIMESTAMP DEFAULT NOW()
            );
        """))

        #Gold Fato_filmes
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_fact_movies (
                movie_id INTEGER,
                genre_id INTEGER,
                title TEXT,
                release_year INTEGER,
                release_month INTEGER,
                decade INTEGER,
                full_date DATE,
                date_id INTEGER,
                popularity FLOAT,
                vote_average FLOAT,
                vote_count INTEGER,
                budget BIGINT,
                revenue BIGINT,
                profit BIGINT,
                roi FLOAT,
                runtime INTEGER,
                query TEXT,
                generated_at TIMESTAMP DEFAULT NOW(),
                          
                PRIMARY KEY (movie_id, genre_id)
            );
        """))

        #Gold Fato_séries
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_fact_tv_shows (
                tv_show_id INTEGER,
                genre_id INTEGER,
                name TEXT,
                network_id INTEGER,
                first_air_year INTEGER,
                first_air_month INTEGER,
                decade INTEGER,
                full_date DATE,
                date_id INTEGER,
                popularity FLOAT,
                vote_average FLOAT,
                vote_count INTEGER,
                number_of_seasons INTEGER,
                number_of_episodes INTEGER,
                in_production BOOLEAN,
                query TEXT,
                generated_at TIMESTAMP DEFAULT NOW(),
                          
                PRIMARY KEY (tv_show_id, genre_id, network_id)
            );
        """))

        #Gold Dim_gênero_movie
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_dim_movie_genre (
                genre_id INTEGER PRIMARY KEY,
                genre_name TEXT,
                total_movies INTEGER,
                avg_vote FLOAT,
                avg_popularity FLOAT,
                generated_at TIMESTAMP DEFAULT NOW()

            );
        """))

        #Gold Dim_gênero_tv_show
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_dim_tv_genre (
                genre_id INTEGER PRIMARY KEY,
                genre_name TEXT,
                total_tv_shows INTEGER,
                avg_vote FLOAT,
                avg_popularity FLOAT,
                generated_at TIMESTAMP DEFAULT NOW()

            );
        """))

        #Gold Dim_pessoa
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_dim_person (
                person_id INTEGER,
                name TEXT,
                role TEXT,
                total_movies INTEGER,
                total_tv_shows INTEGER,
                avg_vote FLOAT,
                person_popularity FLOAT,
                avg_popularity FLOAT,
                generated_at TIMESTAMP DEFAULT NOW(),
                          
                PRIMARY KEY (person_id, role)
            );
        """))

        #Gold Dim_tempo
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gold_fact_time (
                year INTEGER ,
                month INTEGER,
                decade INTEGER,
                total_movies INTEGER,
                total_tv_shows INTEGER,
                avg_movie_vote FLOAT,
                avg_tv_vote FLOAT,
                generated_at TIMESTAMP DEFAULT NOW(),
                          
                PRIMARY KEY(year, month)
            );
        """))

        #Gold date
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS gold_dim_date (
            date_id INTEGER PRIMARY KEY,
            year INTEGER,
            month INTEGER,
            quarter INTEGER,
            decade INTEGER,
            full_date DATE
        );
        """))         

        #Gold Network
        conn.execute(text("""
        CREATE TABLE IF NOT EXISTS gold_dim_network (
            network_id INTEGER PRIMARY KEY,
            network_name TEXT,
            origin_country TEXT,
            total_tv_shows INTEGER,
            avg_vote FLOAT,
            avg_popularity FLOAT,
            generated_at TIMESTAMP DEFAULT NOW()
        );
        """))           

    print("[DB] Tabelas criadas/verificadas com sucesso!")