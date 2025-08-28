#!/usr/bin/env python3
"""
Script para migrar dados do SQLite para MySQL (XAMPP)
"""

import sqlite3
import mysql.connector
from mysql.connector import Error
import os
from datetime import datetime

class DataMigrator:
    def __init__(self):
        # Configuração SQLite
        self.sqlite_db = 'instance/data.db'
        self.sqlite_chat_db = 'chat_msn.db'
        
        # Configuração MySQL
        self.mysql_config = {
            'host': 'localhost',
            'port': 3306,
            'user': 'root',
            'password': '',  # Senha padrão XAMPP (vazia)
            'database': 'chat_empenhos',
            'charset': 'utf8mb4'
        }
    
    def connect_sqlite(self, db_path):
        """Conecta ao SQLite"""
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
            return conn
        except Exception as e:
            print(f"❌ Erro ao conectar SQLite {db_path}: {e}")
            return None
    
    def connect_mysql(self):
        """Conecta ao MySQL"""
        try:
            conn = mysql.connector.connect(**self.mysql_config)
            return conn
        except Error as e:
            print(f"❌ Erro ao conectar MySQL: {e}")
            return None
    
    def check_mysql_connection(self):
        """Verifica se MySQL está rodando"""
        print("🔍 Verificando conexão MySQL...")
        conn = self.connect_mysql()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✅ MySQL conectado! Versão: {version[0]}")
            conn.close()
            return True
        return False
    
    def backup_sqlite_data(self):
        """Faz backup dos dados SQLite"""
        print("💾 Fazendo backup dos dados SQLite...")
        
        backup_dir = f"backup_sqlite_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup banco principal
        if os.path.exists(self.sqlite_db):
            os.system(f'copy "{self.sqlite_db}" "{backup_dir}\\data_backup.db"')
            print(f"✅ Backup principal: {backup_dir}\\data_backup.db")
        
        # Backup banco chat
        if os.path.exists(self.sqlite_chat_db):
            os.system(f'copy "{self.sqlite_chat_db}" "{backup_dir}\\chat_backup.db"')
            print(f"✅ Backup chat: {backup_dir}\\chat_backup.db")
    
    def migrate_main_tables(self):
        """Migra tabelas principais (empenhos, contratos, etc.)"""
        print("📊 Migrando dados principais...")
        
        sqlite_conn = self.connect_sqlite(self.sqlite_db)
        mysql_conn = self.connect_mysql()
        
        if not sqlite_conn or not mysql_conn:
            return False
        
        try:
            # Migrar tabela users
            self.migrate_table(
                sqlite_conn, mysql_conn, 
                'users', 
                ['id', 'username', 'email', 'password_hash', 'role', 'created_at']
            )
            
            # Migrar tabela empenho
            self.migrate_table(
                sqlite_conn, mysql_conn,
                'empenho',
                ['id', 'numero', 'valor', 'data_emissao', 'descricao', 'responsavel']
            )
            
            # Migrar tabela contrato
            self.migrate_table(
                sqlite_conn, mysql_conn,
                'contrato',
                ['id', 'numero', 'objeto', 'valor', 'data_inicio', 'data_fim', 'empresa']
            )
            
            # Migrar tabela nota_fiscal
            self.migrate_table(
                sqlite_conn, mysql_conn,
                'nota_fiscal',
                ['id', 'numero', 'valor', 'data_emissao', 'fornecedor', 'descricao']
            )
            
            print("✅ Migração de dados principais concluída!")
            return True
            
        except Exception as e:
            print(f"❌ Erro na migração: {e}")
            return False
        finally:
            sqlite_conn.close()
            mysql_conn.close()
    
    def migrate_chat_tables(self):
        """Migra tabelas do chat MSN"""
        print("💬 Migrando dados do chat...")
        
        sqlite_conn = self.connect_sqlite(self.sqlite_chat_db)
        mysql_conn = self.connect_mysql()
        
        if not sqlite_conn or not mysql_conn:
            return False
        
        try:
            # Migrar salas de chat
            self.migrate_table(
                sqlite_conn, mysql_conn,
                'chat_msn_room',
                ['id', 'name', 'description', 'created_at', 'is_active']
            )
            
            # Migrar mensagens
            self.migrate_table(
                sqlite_conn, mysql_conn,
                'chat_msn_message',
                ['id', 'room_id', 'user_id', 'content', 'message_type', 'created_at']
            )
            
            print("✅ Migração do chat concluída!")
            return True
            
        except Exception as e:
            print(f"❌ Erro na migração do chat: {e}")
            return False
        finally:
            sqlite_conn.close()
            mysql_conn.close()
    
    def migrate_table(self, sqlite_conn, mysql_conn, table_name, columns):
        """Migra uma tabela específica"""
        print(f"📋 Migrando tabela: {table_name}")
        
        # Ler dados do SQLite
        cursor_sqlite = sqlite_conn.cursor()
        cursor_sqlite.execute(f"SELECT * FROM {table_name}")
        rows = cursor_sqlite.fetchall()
        
        if not rows:
            print(f"⚠️  Tabela {table_name} está vazia")
            return
        
        # Inserir no MySQL
        cursor_mysql = mysql_conn.cursor()
        
        # Montar query de inserção
        placeholders = ', '.join(['%s'] * len(columns))
        query = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
        
        # Inserir dados
        data_to_insert = []
        for row in rows:
            # Converter Row para lista
            row_data = [row[col] if col in row.keys() else None for col in columns]
            data_to_insert.append(tuple(row_data))
        
        cursor_mysql.executemany(query, data_to_insert)
        mysql_conn.commit()
        
        print(f"✅ {len(data_to_insert)} registros migrados para {table_name}")
    
    def run_migration(self):
        """Executa a migração completa"""
        print("🚀 INICIANDO MIGRAÇÃO SQLITE → MYSQL")
        print("=" * 50)
        
        # 1. Verificar conexão MySQL
        if not self.check_mysql_connection():
            print("❌ MySQL não está acessível!")
            print("Verifique se:")
            print("- XAMPP está rodando")
            print("- MySQL está iniciado")
            print("- Banco 'chat_empenhos' foi criado")
            return False
        
        # 2. Fazer backup
        self.backup_sqlite_data()
        
        # 3. Migrar dados principais
        if os.path.exists(self.sqlite_db):
            print(f"\n📊 Migrando banco principal: {self.sqlite_db}")
            self.migrate_main_tables()
        else:
            print("⚠️  Banco principal não encontrado")
        
        # 4. Migrar dados do chat
        if os.path.exists(self.sqlite_chat_db):
            print(f"\n💬 Migrando banco chat: {self.sqlite_chat_db}")
            self.migrate_chat_tables()
        else:
            print("⚠️  Banco chat não encontrado")
        
        print("\n🎉 MIGRAÇÃO CONCLUÍDA!")
        print("Agora você pode usar os aplicativos com MySQL:")
        print("- python app_mysql_principal.py")
        print("- python app_mysql_chat.py")
        
        return True

def main():
    migrator = DataMigrator()
    migrator.run_migration()

if __name__ == "__main__":
    main()
