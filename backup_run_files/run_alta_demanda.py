#!/usr/bin/env python3
"""
Script para ALTA DEMANDA - 15 a 30 usuários simultâneos
Configurações otimizadas para prefeituras com muitos funcionários
"""

from waitress import serve
from app import app
import os
import multiprocessing

def run_high_capacity():
    """Roda o sistema para alta demanda de usuários"""
    
    # Detectar CPUs disponíveis
    cpu_count = multiprocessing.cpu_count()
    
    print("🚀 INICIANDO SISTEMA EM MODO ALTA DEMANDA")
    print("=" * 60)
    print("✅ Servidor: Waitress (Produção)")
    print("✅ Ambiente: Local de Alta Performance")
    print(f"✅ CPUs Detectadas: {cpu_count}")
    print("✅ Usuários Simultâneos: 15-30")
    print("✅ Otimizado para Prefeituras")
    print("-" * 60)
    
    # Configurações de produção
    os.environ['FLASK_ENV'] = 'production'
    app.config['DEBUG'] = False
    
    # Configurações do servidor
    host = '0.0.0.0'
    port = 8000
    
    # Configurações otimizadas baseadas no hardware
    threads = min(30, cpu_count * 8)  # Até 30 threads
    connection_limit = 200
    
    print(f"📍 Rodando em:")
    print(f"   • Local: http://127.0.0.1:{port}")
    print(f"   • Rede: http://10.0.50.79:{port}")
    print("-" * 60)
    print(f"⚡ Threads: {threads}")
    print(f"🔗 Conexões Máximas: {connection_limit}")
    print(f"💾 Buffer Otimizado: 32KB")
    print(f"⏱️  Timeout: 300 segundos")
    print("-" * 60)
    print("💡 Para parar: Ctrl+C")
    print("🏢 Ideal para prefeituras com muitos funcionários")
    print("📊 Monitore o uso de CPU e memória")
    print("=" * 60)
    
    try:
        # Iniciar servidor Waitress com configurações de alta performance
        serve(
            app,
            host=host,
            port=port,
            
            # Threading otimizado
            threads=threads,
            
            # Configurações de conexão
            connection_limit=connection_limit,
            channel_timeout=300,
            cleanup_interval=30,
            
            # Configurações de buffer
            send_bytes=32000,      # Buffer maior
            recv_bytes=32000,
            
            # Configurações de timeout
            asyncore_use_poll=True,
            
            # Log de acesso
            ident='EmpenhosPrefeitura'
        )
        
    except KeyboardInterrupt:
        print("\n\n✅ Servidor parado pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no servidor: {e}")
        print("💡 Dica: Verifique se a porta 8000 está livre")

if __name__ == "__main__":
    run_high_capacity()
