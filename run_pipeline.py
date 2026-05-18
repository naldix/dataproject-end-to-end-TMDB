import subprocess
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

comandos = [
    ["docker-compose", "exec", "airflow-webserver", "python", "-c", "from database.models import criar_tabelas; criar_tabelas()"],
    ["docker-compose", "exec", "airflow-webserver", "python", "-m", "pipeline.extract"],
    ["docker-compose", "exec", "airflow-webserver", "python", "-m", "pipeline.transform"],
    ["docker-compose", "exec", "airflow-webserver", "python", "-m", "pipeline.load"],
]

for cmd in comandos:
    print(f"\n{'='*50}")
    print(f"Rodando: {' '.join(cmd)}")
    print('='*50)

    try:
        resultado = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore",
            check=True
        )

        print(resultado.stdout)
        
        if resultado.stderr:
            print(resultado.stderr)

    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro ao rodar: {' '.join(cmd)}")
        print(e.stdout)
        print(e.stderr)
        sys.exit(1)

print("\n Pipeline concluído com sucesso!")