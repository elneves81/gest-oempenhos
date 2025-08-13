from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from decimal import Decimal

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modelo para usuários do sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        """Define a senha do usuário com hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """Atualiza o último login do usuário"""
        self.ultimo_login = datetime.utcnow()
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'

class Contrato(db.Model):
    """Modelo para contratos"""
    __tablename__ = 'contratos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação do contrato
    numero_pregao = db.Column(db.String(50), nullable=False)
    numero_contrato = db.Column(db.String(50), nullable=False, unique=True)
    numero_ctr = db.Column(db.String(50))  # Número CTR
    
    # Objeto e fornecedor
    objeto = db.Column(db.Text, nullable=False)
    resumo_objeto = db.Column(db.Text)
    fornecedor = db.Column(db.String(200), nullable=False)
    
    # Valores financeiros
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)
    valor_inicial = db.Column(db.Numeric(15, 2))  # Valor original antes dos aditivos
    
    # Datas do contrato
    data_assinatura = db.Column(db.Date, nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    data_fim_original = db.Column(db.Date)  # Data original antes das prorrogações
    
    # Gestão e controle
    gestor_fiscal = db.Column(db.String(200))
    gestor_superior = db.Column(db.String(200))
    status = db.Column(db.String(20), default='ATIVO')
    
    # Informações adicionais de contratos municipais
    modalidade_licitacao = db.Column(db.String(50))  # Pregão, Tomada de Preços, etc.
    numero_processo = db.Column(db.String(100))
    lei_base = db.Column(db.String(200))  # Lei 14.133/2021, 8.666/93, etc.
    orgao_contratante = db.Column(db.String(200))
    secretaria = db.Column(db.String(200))
    
    # Garantias e seguros
    tipo_garantia = db.Column(db.String(100))  # Caução, Seguro-garantia, etc.
    valor_garantia = db.Column(db.Numeric(15, 2))
    validade_garantia = db.Column(db.Date)
    
    # Observações e notas
    observacoes = db.Column(db.Text)
    
    # Metadados
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    empenhos = db.relationship('Empenho', backref='contrato', lazy=True)
    aditivos = db.relationship('AditivoContratual', backref='contrato', lazy=True, order_by='AditivoContratual.numero_aditivo')
    
    @property
    def dias_para_vencimento(self):
        """Calcula quantos dias faltam para o vencimento"""
        if self.data_fim:
            delta = self.data_fim - datetime.now().date()
            return delta.days
        return None
    
    def valor_total_com_aditivos(self):
        """Calcula o valor total incluindo aditivos"""
        valor_aditivos = sum([a.valor_financeiro or 0 for a in self.aditivos if a.tipo in ['REAJUSTE', 'ACRESCIMO']])
        return float(self.valor_total) + float(valor_aditivos)
    
    def prazo_total_com_aditivos(self):
        """Calcula o prazo total incluindo prorrogações"""
        return self.data_fim  # Já inclui as prorrogações
    
    def __repr__(self):
        return f'<Contrato {self.numero_contrato}>'


class AditivoContratual(db.Model):
    """Modelo para aditivos contratuais"""
    __tablename__ = 'aditivos_contratuais'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação do aditivo
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'), nullable=False)
    numero_aditivo = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    numero_instrumento = db.Column(db.String(100))  # Número do termo/apostila
    
    # Tipo e finalidade
    tipo = db.Column(db.String(50), nullable=False)  # PRORROGACAO, REAJUSTE, APOSTILAMENTO, ACRESCIMO, SUPRESSAO
    finalidade = db.Column(db.Text)  # Descrição da finalidade do aditivo
    
    # Aspectos financeiros
    valor_financeiro = db.Column(db.Numeric(15, 2))  # Valor do reajuste/acréscimo
    percentual = db.Column(db.Numeric(5, 2))  # Percentual de reajuste
    
    # Aspectos temporais
    prazo_prorrogacao = db.Column(db.Integer)  # Dias de prorrogação
    nova_data_fim = db.Column(db.Date)  # Nova data de término
    
    # Datas do aditivo
    data_assinatura = db.Column(db.Date, nullable=False)
    data_publicacao = db.Column(db.Date)
    data_inicio_vigencia = db.Column(db.Date)
    
    # Justificativas legais
    fundamentacao_legal = db.Column(db.Text)  # Art. 65 da Lei 8.666/93, etc.
    justificativa = db.Column(db.Text)
    
    # Observações
    observacoes = db.Column(db.Text)
    
    # Metadados
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<Aditivo {self.numero_aditivo}º - {self.tipo}>'

class Empenho(db.Model):
    """Modelo para empenhos"""
    __tablename__ = 'empenhos'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificadores básicos
    numero_pregao = db.Column(db.String(50), nullable=False)
    numero_ctr = db.Column(db.String(50))  # N°
    resumo_objeto = db.Column(db.Text, nullable=False)  # RESUMO DO OBJETO
    fornecedores = db.Column(db.String(200))  # FORNECEDORES
    
    # Informações gerais
    objeto = db.Column(db.Text, nullable=False)  # Mantido para compatibilidade
    numero_contrato = db.Column(db.String(50), nullable=False)
    numero_aditivo = db.Column(db.String(50))  # Referência a qual aditivo se aplica
    
    # Gestão fiscal e superior
    gestor_fiscal_e_superior = db.Column(db.String(100))
    
    # Campos originais mantidos
    numero_empenho = db.Column(db.String(50), nullable=False, unique=True)
    data_empenho = db.Column(db.Date, nullable=False)
    valor_empenhado = db.Column(db.Numeric(15, 2), nullable=False)
    quantidade = db.Column(db.Numeric(10, 2))
    
    # Dados financeiros
    valor_periodo = db.Column(db.Numeric(15, 2))
    percentual_retencao = db.Column(db.Numeric(5, 2), default=0)
    valor_retencao = db.Column(db.Numeric(15, 2), default=0)
    valor_liquido = db.Column(db.Numeric(15, 2))
    
    # Outras datas
    data_envio = db.Column(db.Date)
    data_vencimento = db.Column(db.Date)
    periodo_referencia = db.Column(db.String(20))
    
    # Status e observações
    status = db.Column(db.String(20), default='PENDENTE')
    nota_fiscal = db.Column(db.String(50))
    observacoes = db.Column(db.Text)
    saldo_remanescente = db.Column(db.Numeric(15, 2), default=0)
    
    # Campos auxiliares
    unidade_mensal = db.Column(db.String(50))
    valor_unitario = db.Column(db.Numeric(15, 2))
    
    # Informações Orçamentárias e Fiscais
    dotacao_orcamentaria = db.Column(db.String(100))  # Código da dotação orçamentária
    fonte_recursos = db.Column(db.String(10))  # Código da fonte de recursos
    modalidade_aplicacao = db.Column(db.String(10))  # Modalidade de aplicação
    elemento_despesa = db.Column(db.String(20))  # Elemento de despesa
    processo_administrativo = db.Column(db.String(50))  # Número do processo
    cpf_cnpj_credor = db.Column(db.String(20))  # CPF/CNPJ do credor
    
    # Metadados
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'))
    
    # Relacionamentos
    usuario = db.relationship('User', backref='empenhos')
    
    def __repr__(self):
        return f'<Empenho {self.numero_empenho}>'
    
    def calcular_valores(self):
        """Calcula automaticamente os valores derivados"""
        if self.valor_empenhado and self.percentual_retencao:
            self.valor_retencao = float(self.valor_empenhado) * (float(self.percentual_retencao) / 100)
            self.valor_liquido = float(self.valor_empenhado) - float(self.valor_retencao)
        elif self.valor_empenhado:
            self.valor_liquido = self.valor_empenhado
            
        # Calcular saldo remanescente se necessário
        if self.valor_liquido and self.valor_periodo:
            self.saldo_remanescente = float(self.valor_liquido) - float(self.valor_periodo)
    
    @staticmethod
    def from_dict(data, usuario_id):
        """Cria um objeto Empenho a partir de um dicionário"""
        empenho = Empenho(
            # Identificadores básicos
            numero_pregao=data.get('numero_pregao', ''),
            numero_ctr=data.get('numero_ctr', ''),
            resumo_objeto=data.get('resumo_objeto', ''),
            fornecedores=data.get('fornecedores', ''),
            
            # Compatibilidade com campos antigos
            numero_contrato=data.get('numero_contrato', ''),
            numero_aditivo=data.get('numero_aditivo'),
            objeto=data.get('objeto', ''),
            
            # Gestão fiscal
            gestor_fiscal_e_superior=data.get('gestor_fiscal_e_superior', ''),
            
            # Campos originais
            numero_empenho=data.get('numero_empenho', ''),
            data_empenho=datetime.strptime(data.get('data_empenho'), '%Y-%m-%d').date() if data.get('data_empenho') else None,
            valor_empenhado=data.get('valor_empenhado', 0),
            quantidade=data.get('quantidade'),
            valor_periodo=data.get('valor_periodo'),
            percentual_retencao=data.get('percentual_retencao', 0),
            data_envio=datetime.strptime(data.get('data_envio'), '%Y-%m-%d').date() if data.get('data_envio') else None,
            data_vencimento=datetime.strptime(data.get('data_vencimento'), '%Y-%m-%d').date() if data.get('data_vencimento') else None,
            periodo_referencia=data.get('periodo_referencia'),
            status=data.get('status', 'PENDENTE'),
            nota_fiscal=data.get('nota_fiscal'),
            observacoes=data.get('observacoes'),
            unidade_mensal=data.get('unidade_mensal'),
            valor_unitario=data.get('valor_unitario'),
            usuario_id=usuario_id
        )
        
        # Calcular valores automaticamente
        empenho.calcular_valores()
        return empenho
