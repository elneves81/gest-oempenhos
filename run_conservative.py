#!/usr/bin/env python3
"""
🏛️ SISTEMA DE EMPENHOS MUNICIPAL - VERSÃO CONSERVADORA
======================================================
Dashboard mantendo o estilo original com melhorias técnicas
"""

from waitress import serve
from app import app, db
import logging
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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
            
            # Criar usuário admin padrão se não existir
            from models import User
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@sistema.com',
                    nome='Administrador',
                    is_admin=True
                )
                admin.set_password('admin123')
                db.session.add(admin)
                db.session.commit()
                logger.info("✅ Usuário admin criado - Login: admin, Senha: admin123")
            else:
                logger.info("✅ Usuário admin já existe")
                
            logger.info("✅ Tabelas do banco criadas/verificadas")
            
    except Exception as e:
        logger.error(f"❌ Erro ao criar estrutura: {e}")

def main():
    """Função principal"""
    print("🏛️  SISTEMA DE EMPENHOS MUNICIPAL")
    print("=" * 50)
    print("🎯 Versão: Dashboard Conservador")
    print("📋 Estilo: Original com correções técnicas")
    print("=" * 50)
    
    # Criar estrutura necessária
    criar_estrutura()
    
    # Configurações do servidor
    host = '0.0.0.0'
    port = 8001
    threads = 4
    connection_limit = 50
    
    print("⚙️  CONFIGURAÇÕES")
    print("-" * 30)
    print(f"🌐 Host: {host}")
    print(f"🔌 Porta: {port}")
    print(f"🧵 Threads: {threads}")
    print(f"🔗 Conexões: {connection_limit}")
    print("-" * 30)
    print("📍 ENDEREÇOS DE ACESSO")
    print(f"   • Local: http://127.0.0.1:{port}")
    print(f"   • Rede: http://10.0.50.79:{port}")
    print("-" * 30)
    print("✅ CARACTERÍSTICAS")
    print("   • Layout original preservado")
    print("   • Sidebar com gradiente laranja")
    print("   • Bootstrap Icons mantidos")
    print("   • Monitoramento de vencimentos")
    print("   • Gráfico simples e discreto")
    print("   • Templates sem current_user problemático")
    print("   • Standards Mode garantido")
    print("-" * 30)
    print("🔑 ACESSO")
    print("   • Usuário: admin")
    print("   • Senha: admin123")
    print("-" * 30)
    print("💡 Para parar: Ctrl+C")
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
