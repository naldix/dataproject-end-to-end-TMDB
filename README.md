# Data Pipeline End-to-End - TMDB API
Bem-vindo ao pipeline TMDB API com arquitetura medalhão

## Sobre o projeto
A ideia do projeto foi construir um pipeline de dados mais próximo do mercado de trabalho, passando por ingestão, tratamento e modelagem. Tudo isso conteinerizado dentro do Docker e orquetrado pelo Apache AirFlow.
Foi realizado o desenvolvimento completo do pipeline de dados end-to-end integrando a API do TMDB (The Movie Database), com arquitetura medallion (Bronze, Silver e Gold), orquestrado pelo Apache Airflow em ambiente Docker e com persistência no PostgreSQL. O fluxo automatizado realiza extração, transformação e carga dos dados de forma modular e escalável.

- A camada Bronze é responsável pela ingestão e armazenamento histórico dos dados brutos
- A camada Silver é onde os dados são filtrados, limpos e enriquecidos
- A camada Gold é responsável pela geração das agregações e análises

O próximo passo é a conexão da camada Gold (tabelas com regras de negócio e agregações realizadas) ao Power BI para a criação de dashboards.

## Arquitetura
![Arquitetura](assets/Project_TMDB.drawio.png)

## Tech Stack
- Docker: Utilizado para containerizar toda a aplicação, incluindo o Airflow e o PostgreSQL, garantindo um ambiente isolado, reprodutível e fácil de executar em qualquer máquina.
- Apache Airflow: Responsável pela orquestração do pipeline, agendando e monitorando a execução automatizada de cada etapa do fluxo ETL de forma sequencial e confiável.
- PostgreSQL: Banco de dados relacional utilizado para persistir os dados, armazenando desde os dados da silver até os dados prontos para análise.
- Python: Linguagem principal utilizada para desenvolver todos os módulos do pipeline, incluindo a extração dos dados da API do TMDB, as transformações e a carga no banco de dados.
- SQL: Utilizado para criação das tabelas, queries de transformação e manipulação dos dados dentro do PostgreSQL ao longo das camadas Silver e Gold.
- Power BI: Ferramenta de visualização utilizada na etapa final do projeto, conectando-se à camada Gold do PostgreSQL para a criação de dashboards e análises orientadas ao negócio.
- GitHub: Utilizado para versionamento do código, controle de alterações e hospedagem do repositório do projeto.

# Utilização do Projeto
1. Clone o repositório:
```bash
git clone https://github.com/naldix/dataproject-end-to-end-TMDB.git
```

2. Configure as variáveis de ambiente:

O projeto possui o arquivo .env.example com as variáveis necessárias. Obtenha a chave de API do TMDB e cole ao arquivo.

3. Rode o arquivo docker-compose:
```bash
docker-compose up -d
```
Isso vai inicializar o Airflow, PostgreSQL e os contêiners dentro do Docker.

4. Acesse a aplicação pelo AirFlow:
Abra o navegador e navegue para http://localhost:8080

## Contribuição
Fique a vontade para contribuir ao projeto e/ou entrar em contato para dicas de melhoria e/ou críticas.