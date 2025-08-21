#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuração de Backup Automático
Sistema de Gestão de Empenhos - Prefeitura de Guarapuava
"""

import schedule
import time
import os
from datetime import datetime
from backup_manager import BackupManager

class BackupScheduler:
    def __init__(self, db_path='empenhos.db', backup_dir='backups'):
        """
        Inicializa o agendador de backups
        
        Args:
            db_path (str): Caminho para o banco de dados
            backup_dir (str): Diretório onde salvar os backups
        """
        self.backup_manager = BackupManager(db_path, backup_dir)
        self.log_file = 'backup_scheduler.log'
    
    def log_message(self, message):
        """
        Registra mensagem no log
        
        Args:
            message (str): Mensagem para registrar
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        print(log_entry.strip())
        
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Erro ao escrever no log: {e}")
    
    def backup_job(self):
        """
        Executa backup automático
        """
        self.log_message("🔄 Iniciando backup automático...")
        
        try:
            result = self.backup_manager.create_backup(include_logs=True)
            
            if result['success']:
                info = result.get('backup_info', {})
                message = f"✅ Backup automático concluído: {os.path.basename(result['backup_path'])}"
                message += f" | Tamanho: {info.get('backup_size', 0):,} bytes"
                message += f" | Tabelas: {info.get('tables_count', 0)}"
                self.log_message(message)
            else:
                self.log_message(f"❌ Erro no backup automático: {result['error']}")
                
        except Exception as e:
            self.log_message(f"❌ Exceção no backup automático: {str(e)}")
    
    def start_daily_backup(self, time_str="02:00"):
        """
        Inicia backup diário
        
        Args:
            time_str (str): Horário para backup (formato HH:MM)
        """
        schedule.every().day.at(time_str).do(self.backup_job)
        self.log_message(f"📅 Backup diário agendado para {time_str}")
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Verifica a cada minuto
    
    def start_weekly_backup(self, day="monday", time_str="01:00"):
        """
        Inicia backup semanal
        
        Args:
            day (str): Dia da semana
            time_str (str): Horário para backup
        """
        getattr(schedule.every(), day.lower()).at(time_str).do(self.backup_job)
        self.log_message(f"📅 Backup semanal agendado para {day} às {time_str}")
        
        while True:
            schedule.run_pending()
            time.sleep(60)

def main():
    """
    Função principal para configurar backup automático
    """
    print("=== Configurador de Backup Automático ===\n")
    
    scheduler = BackupScheduler()
    
    print("Opções de backup automático:")
    print("1. Backup diário (02:00)")
    print("2. Backup semanal (Segunda-feira 01:00)")
    print("3. Backup manual agora")
    print("4. Sair")
    
    try:
        choice = input("\nEscolha uma opção (1-4): ").strip()
        
        if choice == "1":
            time_input = input("Horário para backup diário (HH:MM) [02:00]: ").strip()
            time_str = time_input if time_input else "02:00"
            print(f"\n🚀 Iniciando backup diário às {time_str}...")
            print("Pressione Ctrl+C para parar")
            scheduler.start_daily_backup(time_str)
            
        elif choice == "2":
            day_input = input("Dia da semana [monday]: ").strip().lower()
            day = day_input if day_input else "monday"
            time_input = input("Horário (HH:MM) [01:00]: ").strip()
            time_str = time_input if time_input else "01:00"
            print(f"\n🚀 Iniciando backup semanal ({day} às {time_str})...")
            print("Pressione Ctrl+C para parar")
            scheduler.start_weekly_backup(day, time_str)
            
        elif choice == "3":
            print("\n🔄 Executando backup manual...")
            scheduler.backup_job()
            print("✅ Backup manual concluído!")
            
        elif choice == "4":
            print("👋 Saindo...")
            
        else:
            print("❌ Opção inválida!")
            
    except KeyboardInterrupt:
        print("\n\n🛑 Backup automático interrompido pelo usuário")
        scheduler.log_message("🛑 Backup automático interrompido")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        scheduler.log_message(f"❌ Erro no configurador: {e}")

if __name__ == '__main__':
    main()
