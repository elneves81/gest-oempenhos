#!/usr/bin/env python3
"""
Script para rodar o sistema em modo PRODUÇÃO LOCAL
usando Waitress (servidor WSGI profissional)
"""

from waitress import serve
from app import app
import os

def run_production():
    """Roda o sistema em modo produção local"""
    
    print("🚀 INICIANDO SISTEMA EM MODO PRODUÇÃO LOCAL")
    print("=" * 50)
    print("✅ Servidor: Waitress (Produção)")
    print("✅ Ambiente: Local")
    print("✅ Performance: Otimizada para 15+ usuários")
    print("✅ Segurança: Melhorada")
    print("-" * 50)
    
    # Configurações de produção
    os.environ['FLASK_ENV'] = 'production'
    app.config['DEBUG'] = False
    
    # Configurações do servidor
    host = '0.0.0.0'  # Permite acesso de outros computadores na rede
    port = 8000       # Porta diferente do desenvolvimento
    
    print(f"📍 Rodando em:")
    print(f"   • Local: http://127.0.0.1:{port}")
    print(f"   • Rede: http://10.0.50.79:{port}")
    print("-" * 50)
    print("💡 Para parar: Ctrl+C")
    print("🔄 Sem auto-reload (mais estável)")
    print("⚡ Performance otimizada para 15+ usuários simultâneos")
    print("🏢 Ideal para prefeituras com múltiplos funcionários")
    print("=" * 50)
    
    try:
        # Iniciar servidor Waitress
        serve(
            app,
            host=host,
            port=port,
            threads=20,       # Suporta 20 usuários simultâneos
            cleanup_interval=30,
            channel_timeout=120,
            connection_limit=100,  # Máximo 100 conexões
            send_bytes=18000       # Buffer otimizado
        )
    except KeyboardInterrupt:
        print("\n\n✅ Servidor parado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no servidor: {e}")

if __name__ == "__main__":
    run_production()
