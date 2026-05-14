# Data Pipeline End-to-End - TMDB API

## Sobre o projeto
A ideia do projeto foi construir um pipeline de dados mais próximo do mercado de trabalho, passando por ingestão, tratamento e modelagem. Tudo isso conteinerizado dentro do Docker e orquetrado pelo Apache AirFlow.
Foi realizado o desenvolvimento completo do pipeline de dados end-to-end integrando a API do TMDB (The Movie Database), com arquitetura medallion (Bronze, Silver e Gold), orquestrado pelo Apache Airflow em ambiente Docker e com persistência no PostgreSQL. O fluxo automatizado realiza extração, transformação e carga dos dados de forma modular e escalável.

- A camada Bronze é responsável pela ingestão e armazenamento histórico dos dados brutos
- A camada Silver é onde os dados são filtrados, limpos e enriquecidos
- A camada Gold é responsável pela geração das agregações e análises

O próximo passo é a conexão da camada Gold (tabelas com regras de negócio e agregações realizadas) ao Power BI para a criação de dashboards.

## Arquitetura
![Arquitetura](assets/Project_TMDB.drawio.png)