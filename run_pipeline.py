import subprocess
import sys

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

    resultado = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )
    
    print(resultado.stdout)
    print(resultado.stderr)

    if resultado.returncode != 0:
        print(f"\nErro ao rodar: {' '.join(cmd)}")
        sys.exit(1)

print("\n Pipeline concluído com sucesso!")