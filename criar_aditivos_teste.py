#!/usr/bin/env python3
"""
Script para criar aditivos contratuais de teste
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from datetime import datetime, timedelta

# Conectar ao banco de dados SQLite
db_path = 'empenhos.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

def criar_aditivos_teste():
    """Criar alguns aditivos contratuais para teste"""
    print("🔧 Criando aditivos contratuais de teste...")
    
    # Verificar se já existem aditivos
    cursor.execute("SELECT COUNT(*) FROM aditivos_contratuais")
    count = cursor.fetchone()[0]
    
    if count > 0:
        print(f"✅ Já existem {count} aditivos contratuais na base")
        return
    
    # Pegar os primeiros contratos para criar aditivos
    cursor.execute("SELECT id, numero_contrato, valor_total FROM contratos LIMIT 5")
    contratos = cursor.fetchall()
    
    if not contratos:
        print("❌ Não há contratos na base para criar aditivos")
        return
    
    aditivos_data = []
    for i, (contrato_id, numero_contrato, valor_original) in enumerate(contratos):
        # Criar 1-3 aditivos por contrato
        num_aditivos = min(i + 1, 3)
        
        for j in range(num_aditivos):
            numero_aditivo = j + 1
            
            # Tipos de aditivo alternados
            tipos = ['prazo', 'valor', 'qualitativo']
            tipo = tipos[j % len(tipos)]
            
            # Calcular valor do aditivo (10-25% do valor original)
            percentual = 0.10 + (j * 0.05)
            valor_aditivo = valor_original * percentual if valor_original else 10000.0
            
            # Data de assinatura (alguns dias após a data atual)
            data_assinatura = datetime.now() + timedelta(days=j * 30)
            
            aditivo = (
                contrato_id,
                numero_aditivo,
                f"INST-{contrato_id:03d}-{numero_aditivo:02d}",  # numero_instrumento
                tipo,
                f"Aditivo {numero_aditivo} do contrato {numero_contrato} - {tipo.title()}",  # finalidade
                valor_aditivo,  # valor_financeiro
                percentual * 100,  # percentual
                30 if tipo == 'prazo' else None,  # prazo_prorrogacao
                None,  # nova_data_fim
                data_assinatura.strftime('%Y-%m-%d'),  # data_assinatura
                None,  # data_publicacao
                None,  # data_inicio_vigencia
                "Lei 8.666/93",  # fundamentacao_legal
                f"Justificativa para o aditivo {numero_aditivo} de {tipo}",  # justificativa
                None,  # observacoes
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # data_criacao
                1  # usuario_id (admin)
            )
            aditivos_data.append(aditivo)
    
    # Inserir os aditivos
    cursor.executemany("""
        INSERT INTO aditivos_contratuais (
            contrato_id, numero_aditivo, numero_instrumento, tipo, finalidade, 
            valor_financeiro, percentual, prazo_prorrogacao, nova_data_fim,
            data_assinatura, data_publicacao, data_inicio_vigencia, 
            fundamentacao_legal, justificativa, observacoes, data_criacao, usuario_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, aditivos_data)
    
    conn.commit()
    print(f"✅ {len(aditivos_data)} aditivos contratuais criados com sucesso!")

def verificar_aditivos():
    """Verificar os aditivos criados"""
    print("\n📋 Verificando aditivos contratuais...")
    
    cursor.execute("""
        SELECT ac.id, c.numero_contrato, ac.numero_aditivo, ac.tipo, ac.valor_financeiro
        FROM aditivos_contratuais ac
        JOIN contratos c ON ac.contrato_id = c.id
        ORDER BY c.id, ac.numero_aditivo
    """)
    
    aditivos = cursor.fetchall()
    
    if aditivos:
        print(f"📊 Total de aditivos: {len(aditivos)}")
        print("\nDetalhes:")
        for ad_id, num_contrato, num_aditivo, tipo, valor in aditivos:
            valor_fmt = f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.') if valor else 'N/A'
            print(f"  • ID {ad_id}: Contrato {num_contrato} - Aditivo #{num_aditivo} ({tipo}) - {valor_fmt}")
    else:
        print("❌ Nenhum aditivo encontrado")

if __name__ == "__main__":
    try:
        criar_aditivos_teste()
        verificar_aditivos()
        print(f"\n🎯 Agora você pode acessar: http://10.0.50.79:5000/contratos/[ID]/aditivos")
        print("   Substitua [ID] pelo ID de um contrato que tenha aditivos")
        
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        conn.close()
