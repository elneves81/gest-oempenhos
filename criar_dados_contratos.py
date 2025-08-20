#!/usr/bin/env python3
"""
Script para criar dados de exemplo de contratos
"""

import os
import sys
from datetime import date, timedelta
from decimal import Decimal
import random

# Adiciona o diretório atual ao Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, Contrato

def criar_dados_contratos():
    """Cria dados de exemplo para contratos"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Criando dados de exemplo para contratos...")
        
        # Definir fornecedores exemplo
        fornecedores = [
            "Empresa ABC Ltda",
            "Construções XYZ S.A.",
            "Tech Solutions Ltda",
            "Serviços Gerais ME",
            "Materiais e Equipamentos S.A.",
            "Consultoria Especializada Ltda",
            "Obras e Reformas Ltda",
            "Fornecedora Municipal S.A."
        ]
        
        # Tipos de contrato
        tipos = [
            "Prestação de Serviços",
            "Fornecimento de Materiais", 
            "Obras e Reformas",
            "Consultoria",
            "Manutenção",
            "Locação",
            "Software/TI"
        ]
        
        objetos = [
            "Fornecimento de material de escritório",
            "Reforma da escola municipal",
            "Consultoria em gestão pública",
            "Manutenção de equipamentos",
            "Locação de veículos",
            "Sistema de gestão integrada",
            "Construção de posto de saúde",
            "Serviços de limpeza pública",
            "Fornecimento de uniformes",
            "Manutenção de software"
        ]
        
        hoje = date.today()
        
        # Criar 15 contratos de exemplo
        contratos_exemplo = []
        
        for i in range(1, 16):
            # Definir datas aleatórias
            inicio_days = random.randint(-365, 0)  # até 1 ano atrás
            duracao_days = random.randint(90, 720)  # entre 3 meses e 2 anos
            
            data_inicio = hoje + timedelta(days=inicio_days)
            data_fim = data_inicio + timedelta(days=duracao_days)
            
            # Definir status baseado na data
            if data_fim < hoje:
                status = "Vencido"
            elif data_fim <= hoje + timedelta(days=30):
                status = "Vencendo"
            else:
                status = "Ativo"
            
            # Valores aleatórios
            valor_base = random.uniform(5000, 500000)
            valor_total = Decimal(str(round(valor_base, 2)))
            
            contrato = {
                'numero': f"CT-{2024}-{i:03d}",
                'objeto': random.choice(objetos),
                'fornecedor': random.choice(fornecedores),
                'cnpj': f"{random.randint(10, 99)}.{random.randint(100, 999)}.{random.randint(100, 999)}/0001-{random.randint(10, 99)}",
                'tipo': random.choice(tipos),
                'data_inicio': data_inicio,
                'data_fim': data_fim,
                'valor_total': valor_total,
                'status': status,
                'modalidade': random.choice(['Pregão Eletrônico', 'Convite', 'Tomada de Preços', 'Concorrência']),
                'observacoes': f"Contrato {status.lower()} para {random.choice(objetos).lower()}"
            }
            
            contratos_exemplo.append(contrato)
        
        # Verificar se já existem contratos
        contratos_existentes = Contrato.query.count()
        
        if contratos_existentes > 0:
            print(f"⚠️  Já existem {contratos_existentes} contratos no banco. Removendo...")
            Contrato.query.delete()
            db.session.commit()
        
        # Inserir novos contratos
        for dados in contratos_exemplo:
            try:
                contrato = Contrato(**dados)
                db.session.add(contrato)
            except Exception as e:
                print(f"❌ Erro ao criar contrato {dados['numero']}: {e}")
                continue
        
        try:
            db.session.commit()
            total_criados = Contrato.query.count()
            print(f"✅ {total_criados} contratos criados com sucesso!")
            
            # Estatísticas resumo
            ativos = Contrato.query.filter_by(status='Ativo').count()
            vencendo = Contrato.query.filter_by(status='Vencendo').count()
            vencidos = Contrato.query.filter_by(status='Vencido').count()
            
            print(f"📊 Resumo:")
            print(f"   • Ativos: {ativos}")
            print(f"   • Vencendo (30 dias): {vencendo}")
            print(f"   • Vencidos: {vencidos}")
            
            # Valor total
            valor_total = db.session.query(db.func.sum(Contrato.valor_total)).scalar() or 0
            print(f"   • Valor Total: R$ {valor_total:,.2f}")
            
        except Exception as e:
            print(f"❌ Erro ao salvar contratos: {e}")
            db.session.rollback()

if __name__ == "__main__":
    criar_dados_contratos()
