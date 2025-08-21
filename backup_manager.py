#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de Backup do Banco de Dados
Gestão de Empenhos - Prefeitura de Guarapuava
"""

import os
import shutil
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
import json

class BackupManager:
    def __init__(self, db_path='empenhos.db', backup_dir='backups'):
        """
        Inicializa o gerenciador de backups
        
        Args:
            db_path (str): Caminho para o banco de dados
            backup_dir (str): Diretório onde salvar os backups
        """
        self.db_path = db_path
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        
    def create_backup(self, include_logs=True):
        """
        Cria um backup completo do sistema
        
        Args:
            include_logs (bool): Se deve incluir logs no backup
            
        Returns:
            dict: Resultado da operação com status e detalhes
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = f"backup_empenhos_{timestamp}"
            backup_path = self.backup_dir / f"{backup_name}.zip"
            
            # Informações do backup
            backup_info = {
                'timestamp': timestamp,
                'datetime': datetime.now().isoformat(),
                'database_size': 0,
                'tables_count': 0,
                'records_count': {},
                'backup_size': 0,
                'success': False
            }
            
            # Verifica se o banco existe
            if not os.path.exists(self.db_path):
                return {
                    'success': False,
                    'error': f'Banco de dados não encontrado: {self.db_path}',
                    'backup_path': None
                }
            
            # Obter informações do banco
            backup_info['database_size'] = os.path.getsize(self.db_path)
            
            # Conectar ao banco para obter estatísticas
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Contar tabelas
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                backup_info['tables_count'] = len(tables)
                
                # Contar registros por tabela
                for table in tables:
                    table_name = table[0]
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        backup_info['records_count'][table_name] = count
                    except Exception as e:
                        backup_info['records_count'][table_name] = f"Erro: {str(e)}"
                
                conn.close()
                
            except Exception as e:
                print(f"Aviso: Erro ao obter estatísticas do banco: {e}")
            
            # Criar backup compactado
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                # Adicionar banco de dados principal
                zipf.write(self.db_path, f'database/{os.path.basename(self.db_path)}')
                
                # Adicionar arquivos de configuração se existirem
                config_files = ['config.py', 'requirements.txt', '.env']
                for config_file in config_files:
                    if os.path.exists(config_file):
                        zipf.write(config_file, f'config/{config_file}')
                
                # Adicionar logs se solicitado
                if include_logs:
                    log_files = ['app.log', 'error.log', 'access.log']
                    for log_file in log_files:
                        if os.path.exists(log_file):
                            zipf.write(log_file, f'logs/{log_file}')
                
                # Adicionar informações do backup
                backup_info_json = json.dumps(backup_info, indent=2, ensure_ascii=False)
                zipf.writestr('backup_info.json', backup_info_json)
                
                # Adicionar schema do banco
                try:
                    schema = self._export_schema()
                    zipf.writestr('database/schema.sql', schema)
                except Exception as e:
                    print(f"Aviso: Erro ao exportar schema: {e}")
            
            # Atualizar informações finais
            backup_info['backup_size'] = os.path.getsize(backup_path)
            backup_info['success'] = True
            
            # Limpar backups antigos (manter apenas os 10 mais recentes)
            self._cleanup_old_backups(keep_count=10)
            
            return {
                'success': True,
                'backup_path': str(backup_path),
                'backup_info': backup_info,
                'message': f'Backup criado com sucesso: {backup_name}.zip'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'backup_path': None
            }
    
    def _export_schema(self):
        """
        Exporta o schema do banco de dados
        
        Returns:
            str: Schema SQL do banco
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Obter todas as instruções de criação
            cursor = conn.cursor()
            cursor.execute("SELECT sql FROM sqlite_master WHERE sql IS NOT NULL")
            schema_statements = cursor.fetchall()
            
            schema = "-- Schema do Banco de Dados - Gestão de Empenhos\n"
            schema += f"-- Exportado em: {datetime.now().isoformat()}\n\n"
            
            for statement in schema_statements:
                schema += statement[0] + ";\n\n"
            
            conn.close()
            return schema
            
        except Exception as e:
            return f"-- Erro ao exportar schema: {str(e)}\n"
    
    def _cleanup_old_backups(self, keep_count=10):
        """
        Remove backups antigos, mantendo apenas os mais recentes
        
        Args:
            keep_count (int): Número de backups a manter
        """
        try:
            # Listar todos os arquivos de backup
            backup_files = list(self.backup_dir.glob('backup_empenhos_*.zip'))
            
            # Ordenar por data de modificação (mais recente primeiro)
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Remover backups excedentes
            for old_backup in backup_files[keep_count:]:
                try:
                    old_backup.unlink()
                    print(f"Backup antigo removido: {old_backup.name}")
                except Exception as e:
                    print(f"Erro ao remover backup antigo {old_backup.name}: {e}")
                    
        except Exception as e:
            print(f"Erro na limpeza de backups antigos: {e}")
    
    def list_backups(self):
        """
        Lista todos os backups disponíveis
        
        Returns:
            list: Lista de backups com informações
        """
        try:
            backup_files = list(self.backup_dir.glob('backup_empenhos_*.zip'))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            backups = []
            for backup_file in backup_files:
                stat = backup_file.stat()
                
                # Tentar extrair informações do backup
                backup_info = {}
                try:
                    with zipfile.ZipFile(backup_file, 'r') as zipf:
                        if 'backup_info.json' in zipf.namelist():
                            info_data = zipf.read('backup_info.json').decode('utf-8')
                            backup_info = json.loads(info_data)
                except Exception:
                    pass
                
                backups.append({
                    'filename': backup_file.name,
                    'path': str(backup_file),
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'created': datetime.fromtimestamp(stat.st_mtime),
                    'created_str': datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M:%S'),
                    'info': backup_info
                })
            
            return backups
            
        except Exception as e:
            print(f"Erro ao listar backups: {e}")
            return []
    
    def restore_backup(self, backup_filename, target_dir='.'):
        """
        Restaura um backup
        
        Args:
            backup_filename (str): Nome do arquivo de backup
            target_dir (str): Diretório de destino para restauração
            
        Returns:
            dict: Resultado da operação
        """
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f'Backup não encontrado: {backup_filename}'
                }
            
            target_path = Path(target_dir)
            
            # Criar backup do banco atual antes de restaurar
            if os.path.exists(self.db_path):
                current_backup = f"{self.db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(self.db_path, current_backup)
            
            # Extrair backup
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Extrair banco de dados
                for member in zipf.namelist():
                    if member.startswith('database/') and member.endswith('.db'):
                        zipf.extract(member, target_path)
                        
                        # Mover para o local correto
                        extracted_db = target_path / member
                        final_db = target_path / self.db_path
                        
                        if extracted_db.exists():
                            if final_db.exists():
                                final_db.unlink()
                            shutil.move(str(extracted_db), str(final_db))
                            
                            # Remover diretório temporário
                            temp_dir = target_path / 'database'
                            if temp_dir.exists() and not any(temp_dir.iterdir()):
                                temp_dir.rmdir()
            
            return {
                'success': True,
                'message': f'Backup {backup_filename} restaurado com sucesso'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Erro ao restaurar backup: {str(e)}'
            }

def main():
    """Função principal para teste do sistema de backup"""
    backup_manager = BackupManager()
    
    print("=== Sistema de Backup - Gestão de Empenhos ===\n")
    
    # Criar backup
    print("Criando backup...")
    result = backup_manager.create_backup()
    
    if result['success']:
        print(f"✅ {result['message']}")
        print(f"📁 Arquivo: {result['backup_path']}")
        
        if 'backup_info' in result:
            info = result['backup_info']
            print(f"📊 Tamanho do banco: {info['database_size']:,} bytes")
            print(f"📋 Tabelas: {info['tables_count']}")
            print(f"📦 Tamanho do backup: {info['backup_size']:,} bytes")
    else:
        print(f"❌ Erro: {result['error']}")
    
    # Listar backups
    print("\n--- Backups Disponíveis ---")
    backups = backup_manager.list_backups()
    
    for backup in backups:
        print(f"📁 {backup['filename']}")
        print(f"   📅 Criado: {backup['created_str']}")
        print(f"   📊 Tamanho: {backup['size_mb']} MB")
        if backup['info'] and 'tables_count' in backup['info']:
            print(f"   📋 Tabelas: {backup['info']['tables_count']}")
        print()

if __name__ == '__main__':
    main()
