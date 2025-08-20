import sqlite3
import os

def migrar_banco():
    # Verificar se o banco existe e conectar
    db_path = os.path.join('instance', 'database.db')
    
    if not os.path.exists(db_path):
        os.makedirs('instance', exist_ok=True)
        print('❌ Banco de dados não existe - criando diretório instance')
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Verificar se a tabela contratos existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='contratos'")
        tabela_existe = cursor.fetchone()

        if tabela_existe:
            print('✅ Tabela contratos encontrada')
            
            # Verificar estrutura atual
            cursor.execute('PRAGMA table_info(contratos)')
            colunas_existentes = [col[1] for col in cursor.fetchall()]
            
            print(f'📊 Colunas existentes: {len(colunas_existentes)}')
            
            # Verificar se as novas colunas já existem
            campos_para_adicionar = [
                ('responsavel_emails_extras', 'TEXT'),
                ('responsavel_telefones_extras', 'TEXT')
            ]
            
            campos_adicionados = 0
            for campo, tipo in campos_para_adicionar:
                if campo not in colunas_existentes:
                    print(f'➕ Adicionando coluna: {campo}')
                    cursor.execute(f'ALTER TABLE contratos ADD COLUMN {campo} {tipo}')
                    campos_adicionados += 1
                else:
                    print(f'✅ Coluna {campo} já existe')
            
            if campos_adicionados > 0:
                conn.commit()
                print(f'🎉 Migração concluída! {campos_adicionados} coluna(s) adicionada(s)')
            else:
                print('ℹ️ Nenhuma coluna precisou ser adicionada')
                
        else:
            print('❌ Tabela contratos não existe - será criada automaticamente pelo SQLAlchemy')

    except Exception as e:
        print(f'❌ Erro na migração: {e}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrar_banco()
