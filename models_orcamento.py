# models_orcamento.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Numeric, Date, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship

# Usar a instância global do db
from models import db

DEC = Numeric(14,2)

class Orcamento(db.Model):
    __tablename__ = "orcamentos"
    id = Column(Integer, primary_key=True)
    ano = Column(Integer, nullable=False)
    orgao = Column(String(120), nullable=False)           # ex: "Saúde"
    unidade = Column(String(120))
    funcao = Column(String(50))
    subfuncao = Column(String(50))
    programa = Column(String(120))
    acao = Column(String(120))
    fonte = Column(String(50))  # Alterado de fonte_recurso para fonte
    categoria = Column(String(20), nullable=False, default="GERAL")  # "GERAL" | "SAUDE"

    valor_dotado = Column(DEC, nullable=False, default=0)      # Alterado de dotado
    valor_atualizado = Column(DEC, nullable=False, default=0)  # Alterado de atualizado
    empenhado = Column(DEC, nullable=False, default=0)
    liquidado = Column(DEC, nullable=False, default=0)
    pago = Column(DEC, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint('ano','orgao','unidade','funcao','subfuncao','programa','acao','fonte','categoria', name='uq_orcamento_linha'),
        CheckConstraint("categoria in ('GERAL','SAUDE')", name='ck_orc_cat'),
        CheckConstraint('valor_dotado >= 0 AND valor_atualizado >= 0 AND empenhado >= 0 AND liquidado >= 0 AND pago >= 0', name='ck_orc_vals_pos'),
    )

    empenhos = relationship("EmpenhoOrcamentario", back_populates="orcamento")  # Alterado de itens

    @property
    def saldo_a_empenhar(self): return float((self.valor_atualizado or 0) - (self.empenhado or 0))
    @property
    def saldo_a_liquidar(self): return float((self.empenhado or 0) - (self.liquidado or 0))
    @property
    def saldo_a_pagar(self):    return float((self.liquidado or 0) - (self.pago or 0))
    
    # Propriedades para compatibilidade com código existente
    @property
    def dotado(self): return self.valor_dotado
    @property
    def atualizado(self): return self.valor_atualizado

    @property
    def saldo_a_empenhar(self): return float((self.atualizado or 0) - (self.empenhado or 0))
    @property
    def saldo_a_liquidar(self): return float((self.empenhado or 0) - (self.liquidado or 0))
    @property
    def saldo_a_pagar(self):    return float((self.liquidado or 0) - (self.pago or 0))

class EmpenhoOrcamentario(db.Model):
    __tablename__ = "empenhos_orcamentarios"
    id = Column(Integer, primary_key=True)
    data = Column(Date, nullable=False)
    numero = Column(String(50), nullable=False, unique=True)
    fornecedor = Column(String(200), nullable=False)
    descricao = Column(String(500))  # Adicionado campo descrição
    valor_empenhado = Column(DEC, nullable=False)  # Renomeado de valor
    valor_liquidado = Column(DEC, nullable=False, default=0)  # Adicionado
    valor_pago = Column(DEC, nullable=False, default=0)       # Adicionado
    status = Column(String(20), nullable=False, default="EMPENHADO")   # EMPENHADO|LIQUIDADO|PAGO

    orcamento_id = Column(Integer, ForeignKey("orcamentos.id"), nullable=False)
    orcamento = relationship("Orcamento", back_populates="empenhos")
    
    # Propriedade para compatibilidade
    @property
    def valor(self): return self.valor_empenhado

    def __repr__(self):
        return f'<EmpenhoOrcamentario {self.numero}: {self.valor}>'
