import sqlite3

conn = sqlite3.connect('empenhos.db')
cursor = conn.cursor()

# Verificar comando SQL da tabela users
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
result = cursor.fetchone()
print("SQL da tabela users:")
if result:
    print(result[0])
else:
    print("Tabela não encontrada")

print("\n" + "="*50)

# Verificar colunas da tabela users
cursor.execute('PRAGMA table_info(users)')
cols = cursor.fetchall()
print("Colunas da tabela users:")
for row in cols:
    print(f"{row[1]} {row[2]} (null={row[3]}, default={row[4]})")

conn.close()
