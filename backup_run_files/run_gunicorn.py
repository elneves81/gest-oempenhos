#!/usr/bin/env python3
"""
Script alternativo para rodar com Gunicorn
(Funciona melhor no Linux, mas roda no Windows também)
"""

import subprocess
import sys
import os

def run_gunicorn():
    """Roda o sistema com Gunicorn"""
    
    print("🚀 INICIANDO SISTEMA COM GUNICORN")
    print("=" * 50)
    print("✅ Servidor: Gunicorn (Produção)")
    print("✅ Workers: 4 processos")
    print("✅ Performance: Alta para 15+ usuários")
    print("-" * 50)
    
    # Comando Gunicorn
    cmd = [
        "C:/Users/Elber/Documents/GitHub/empenhos/.venv/Scripts/gunicorn.exe",
        "--bind", "0.0.0.0:8000",
        "--workers", "4",         # 4 processos para mais usuários
        "--timeout", "120",
        "--worker-class", "sync",
        "--worker-connections", "1000",
        "--max-requests", "2000", # Mais requisições por worker
        "--max-requests-jitter", "100",
        "--preload-app",          # Carrega app uma vez (mais eficiente)
        "--access-logfile", "-",
        "app:app"
    ]
    
    print(f"📍 Rodando em: http://127.0.0.1:8000")
    print("💡 Para parar: Ctrl+C")
    print("=" * 50)
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\n✅ Servidor parado pelo usuário")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Erro: {e}")
    except FileNotFoundError:
        print("\n❌ Gunicorn não encontrado. Use run_production.py com Waitress")

if __name__ == "__main__":
    run_gunicorn()
