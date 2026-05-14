from datetime import datetime, timedelta
import sys
import logging

sys.path.append('/opt/airflow')

from airflow import DAG
from airflow.operators.python import PythonOperator

from pipeline.extract import executar_bronze
from pipeline.transform import executar_silver
from pipeline.load import executar_gold

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

default_args = {
    "owner": "arnaldo",
    "depends_on_past": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5)
}

def iniciar_extract():
    logger.info("========== INICIANDO CAMADA BRONZE ==========")

def finalizar_extract():
    logger.info("========== BRONZE FINALIZADA ==========")

def iniciar_transform():
    logger.info("========== INICIANDO CAMADA SILVER ==========")

def finalizar_transform():
    logger.info("========== SILVER FINALIZADA ==========")

def iniciar_load():
    logger.info("========== INICIANDO CAMADA GOLD ==========")

def finalizar_load():
    logger.info("========== GOLD FINALIZADA ==========")

with DAG(
    dag_id = "pipeline_tmdb",
    description = "Pipeline ETL TMDB com camadas Bronze, Silver e Gold",
    default_args = default_args,
    start_date = datetime(2026, 5, 12),
    schedule_interval = '0 12 * * *',
    catchup = False,
    tags = ["tmdb", "etl", "data-engineering"]
) as dag:
    
    log_inicio_extract = PythonOperator(
        task_id = "log_inicio_extract",
        python_callable = iniciar_extract
    )

    extract_bronze = PythonOperator(
        task_id = "extract_bronze",
        python_callable = executar_bronze
    )

    log_fim_extract = PythonOperator(
        task_id = "log_fim_extract",
        python_callable = finalizar_extract
    )

    log_inicio_transform = PythonOperator(
        task_id = "log_inicio_transform",
        python_callable = iniciar_transform
    )

    transform_silver = PythonOperator(
        task_id = "transform_silver",
        python_callable = executar_silver
    )

    log_fim_transform = PythonOperator(
        task_id = "log_fim_transform",
        python_callable = finalizar_transform
    )

    log_inicio_load = PythonOperator(
        task_id = "log_inicio_load",
        python_callable = iniciar_load
    )

    load_gold = PythonOperator(
        task_id = "load_gold",
        python_callable = executar_gold
    )

    log_fim_load = PythonOperator(
        task_id = "log_fim_load",
        python_callable = finalizar_load
    )

    (log_inicio_extract >> extract_bronze >> log_fim_extract >> log_inicio_transform >> transform_silver >> log_fim_transform >> log_inicio_load >> load_gold >> log_fim_load)