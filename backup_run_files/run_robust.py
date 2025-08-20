#!/usr/bin/env python3
"""
🚀 SISTEMA DE EMPENHOS MUNICIPAL
====================================
Versão Robusta com Dashboard Completo
"""

from waitress import serve
from app import app, db
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def criar_estrutura():
    """Criar estrutura necessária do projeto"""
    try:
        # Criar diretórios necessários
        dirs = [
            'instance',
            'uploads',
            'uploads/contratos',
            'logs'
        ]
        
        for dir_path in dirs:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                logger.info(f"✅ Diretório criado: {dir_path}")
        
        # Criar tabelas se não existirem
        with app.app_context():
            db.create_all()
            logger.info("✅ Tabelas do banco criadas/verificadas")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar estrutura: {e}")

def main():
    """Função principal"""
    print("🏛️  SISTEMA DE EMPENHOS MUNICIPAL")
    print("=" * 50)
    print("🔧 Versão: Dashboard Robusto")
    print("🏛️  Desenvolvido para: Gestão Municipal")
    print("=" * 50)
    
    # Criar estrutura necessária
    criar_estrutura()
    
    # Configurações do servidor
    host = '0.0.0.0'
    port = 8001
    threads = 6
    connection_limit = 100
    
    print("📊 CONFIGURAÇÕES DO SERVIDOR")
    print("-" * 30)
    print(f"🌐 Host: {host}")
    print(f"🔌 Porta: {port}")
    print(f"🧵 Threads: {threads}")
    print(f"🔗 Conexões máx: {connection_limit}")
    print("-" * 30)
    print("📍 ENDEREÇOS DE ACESSO")
    print(f"   • Local: http://127.0.0.1:{port}")
    print(f"   • Rede: http://10.0.50.79:{port}")
    print("-" * 30)
    print("🎯 FUNCIONALIDADES IMPLEMENTADAS")
    print("   ✅ Dashboard com monitoramento de contratos")
    print("   ✅ Categorização por vencimento (30/60+ dias)")
    print("   ✅ Gráficos interativos com Chart.js")
    print("   ✅ Cards responsivos com Bootstrap 5")
    print("   ✅ Ícones Font Awesome")
    print("   ✅ Templates robustos sem erros")
    print("   ✅ Sistema de autenticação Flask-Login")
    print("   ✅ Gestão completa de empenhos e contratos")
    print("   ✅ Sistema de relatórios")
    print("   ✅ Importação de dados")
    print("-" * 30)
    print("💡 Para parar: Ctrl+C")
    print("🔍 Logs em tempo real abaixo:")
    print("=" * 50)
    
    try:
        # Iniciar servidor Waitress
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            connection_limit=connection_limit,
            cleanup_interval=30,
            channel_timeout=120
        )
    except KeyboardInterrupt:
        print("\n🛑 Servidor parado pelo usuário")
    except Exception as e:
        logger.error(f"❌ Erro no servidor: {e}")
        print(f"❌ ERRO: {e}")

if __name__ == '__main__':
    main()
