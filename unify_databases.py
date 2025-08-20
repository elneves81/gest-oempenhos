#!/usr/bin/env python3
"""
Script para unificar bancos - usar apenas instance/empenhos.db
"""

import sqlite3
import os
import shutil
from datetime import datetime

def unify_databases():
    root_db = 'empenhos.db'
    instance_db = 'instance/empenhos.db'
    
    print("🔄 Unificando bancos de dados...")
    
    if not os.path.exists(root_db):
        print("❌ empenhos.db não existe na raiz!")
        return False
    
    if not os.path.exists(instance_db):
        print("❌ instance/empenhos.db não existe!")
        return False
    
    # 1. Fazer backup do banco da raiz
    backup_name = f'empenhos_root_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    backup_path = os.path.join('instance', backup_name)
    
    print(f"💾 Fazendo backup: {backup_path}")
    shutil.copy2(root_db, backup_path)
    
    # 2. Verificar se instance/empenhos.db tem mais dados
    conn_root = sqlite3.connect(root_db)
    conn_instance = sqlite3.connect(instance_db)
    
    # Verificar registros principais
    cursor_root = conn_root.cursor()
    cursor_instance = conn_instance.cursor()
    
    print("\n📊 Comparando dados:")
    
    tables_to_check = ['users', 'empenhos', 'contratos', 'chat_sessions', 'chat_messages']
    
    for table in tables_to_check:
        try:
            cursor_root.execute(f"SELECT COUNT(*) FROM {table}")
            root_count = cursor_root.fetchone()[0]
        except:
            root_count = 0
            
        try:
            cursor_instance.execute(f"SELECT COUNT(*) FROM {table}")
            instance_count = cursor_instance.fetchone()[0]
        except:
            instance_count = 0
            
        print(f"  {table}: raiz={root_count}, instance={instance_count}")
        
        if root_count > instance_count:
            print(f"  ⚠️ Banco da raiz tem mais dados em {table}!")
    
    conn_root.close()
    conn_instance.close()
    
    # 3. Remover banco da raiz
    print(f"\n🗑️ Removendo {root_db}...")
    os.remove(root_db)
    
    print("✅ Unificação concluída!")
    print(f"📁 Banco único: {instance_db}")
    print(f"💾 Backup salvo: {backup_path}")
    
    # 4. Verificar resultado
    print("\n🔍 Verificação final:")
    print(f"  - empenhos.db existe: {os.path.exists(root_db)}")
    print(f"  - instance/empenhos.db existe: {os.path.exists(instance_db)}")
    
    return True

if __name__ == "__main__":
    print("🎯 UNIFICAÇÃO DE BANCOS DE DADOS")
    print("=" * 50)
    print("Estratégia: Manter apenas instance/empenhos.db")
    print("Banco da raiz será movido para backup")
    print("=" * 50)
    
    confirm = input("\nConfirma a unificação? (s/N): ").lower().strip()
    
    if confirm == 's':
        success = unify_databases()
        if success:
            print("\n🎉 Sucesso! Agora você tem apenas um banco.")
            print("💡 O Flask usará automaticamente instance/empenhos.db")
        else:
            print("\n❌ Erro na unificação!")
    else:
        print("\n🚫 Operação cancelada.")
