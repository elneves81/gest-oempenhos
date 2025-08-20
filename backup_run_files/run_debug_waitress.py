#!/usr/bin/env python3
"""
Script Waitress com DEBUG ativado para diagnosticar erros
"""

from waitress import serve
from app import app
import os
import multiprocessing
import logging

def run_debug_waitress():
    """Roda Waitress com debug para diagnóstico"""
    
    # Detectar CPUs disponíveis
    cpu_count = multiprocessing.cpu_count()
    
    print("🔍 WAITRESS COM DEBUG ATIVADO")
    print("=" * 50)
    print("✅ Servidor: Waitress (Debug)")
    print("✅ Modo: Diagnóstico de Erros")
    print(f"✅ CPUs: {cpu_count}")
    print("-" * 50)
    
    # Configurações de DEBUG
    os.environ['FLASK_ENV'] = 'development'
    app.config['DEBUG'] = True
    app.config['TESTING'] = False
    
    # Configurar logging
    logging.basicConfig(level=logging.DEBUG)
    
    # Configurações do servidor
    host = '0.0.0.0'
    port = 8001  # Porta diferente para não conflitar
    
    # Threads reduzidas para debug
    threads = 4
    connection_limit = 50
    
    print(f"📍 Rodando em:")
    print(f"   • Local: http://127.0.0.1:{port}")
    print(f"   • Rede: http://10.0.50.79:{port}")
    print("-" * 50)
    print(f"⚡ Threads: {threads}")
    print(f"🔗 Conexões: {connection_limit}")
    print(f"🐛 DEBUG: ATIVADO")
    print("-" * 50)
    print("💡 Para parar: Ctrl+C")
    print("🔍 Erros aparecerão no console")
    print("=" * 50)
    
    try:
        # Iniciar servidor Waitress com debug
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            connection_limit=connection_limit,
            channel_timeout=120,
            cleanup_interval=30,
            send_bytes=8192,
            recv_bytes=8192,
            ident='EmpenhosDEBUG'
        )
        
    except KeyboardInterrupt:
        print("\n\n✅ Servidor debug parado")
    except Exception as e:
        print(f"\n❌ Erro no servidor: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_debug_waitress()
