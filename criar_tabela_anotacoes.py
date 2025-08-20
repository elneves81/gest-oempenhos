#!/usr/bin/env python3
"""
Script para criar a tabela de anotações de contratos
"""

from app import app
from models import db, AnotacaoContrato

def criar_tabela_anotacoes():
    """Cria a tabela de anotações de contratos"""
    
    print("🔧 Criando tabela de anotações de contratos...")
    
    with app.app_context():
        try:
            # Criar todas as tabelas que ainda não existem
            db.create_all()
            
            print("✅ Tabela de anotações criada com sucesso!")
            print("📋 Estrutura da tabela:")
            print("   - id (chave primária)")
            print("   - contrato_id (FK para contratos)")
            print("   - usuario_id (FK para users)")
            print("   - texto (texto da anotação)")
            print("   - data_criacao")
            print("   - data_atualizacao")
            print("   - nome_arquivo (opcional)")
            print("   - caminho_arquivo (opcional)")
            print("   - tipo_arquivo (opcional)")
            print("   - tamanho_arquivo (opcional)")
            
        except Exception as e:
            print(f"❌ Erro ao criar tabela: {str(e)}")
            return False
    
    return True

if __name__ == '__main__':
    criar_tabela_anotacoes()
