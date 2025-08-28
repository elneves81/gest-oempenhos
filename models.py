from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from decimal import Decimal

# Inicializar SQLAlchemy diretamente
db = SQLAlchemy()

def create_models(database_instance):
    """Cria e retorna todas as classes de modelo com a instância db fornecida"""
    global db
    db = database_instance

class User(UserMixin, db.Model):
    """Modelo para usuários do sistema"""
    __tablename__ = 'users'
    __table_args__ = {'extend_existing': True}  # Para evitar conflito com tabela existente
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime)
    # Não incluir last_seen e presence no modelo para evitar conflitos
    
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
    data_pregao = db.Column(db.Date)  # Data do pregão
    numero_contrato = db.Column(db.String(50), nullable=False, unique=True)
    data_contrato = db.Column(db.Date)  # Data do contrato
    numero_ctr = db.Column(db.String(50))  # Número CTR
    numero_processo = db.Column(db.String(100))
    data_processo = db.Column(db.Date)  # Data do processo
    digito_verificador = db.Column(db.String(10))  # Dígito verificador
    tipo_contratacao = db.Column(db.String(50))  # SERVICO, COMPRA, LOCACAO, etc.
    
    # Objeto e fornecedor
    objeto = db.Column(db.Text, nullable=False)
    resumo_objeto = db.Column(db.Text)  # Mantido para compatibilidade
    fornecedor = db.Column(db.String(200), nullable=False)
    cnpj_fornecedor = db.Column(db.String(18))  # 00.000.000/0000-00
    
    # Responsável pelo contrato
    responsavel_nome = db.Column(db.String(200))
    responsavel_email = db.Column(db.String(200))
    responsavel_telefone = db.Column(db.String(20))
    responsavel_cargo = db.Column(db.String(100))
    responsavel_emails_extras = db.Column(db.Text)  # JSON com emails extras
    responsavel_telefones_extras = db.Column(db.Text)  # JSON com telefones extras
    
    # Arquivo do contrato
    arquivo_contrato = db.Column(db.String(255))  # Nome do arquivo
    
    # Valores financeiros
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)
    valor_inicial = db.Column(db.Numeric(15, 2))  # Valor original antes dos aditivos
    
    # Datas do contrato
    data_assinatura = db.Column(db.Date, nullable=False)
    data_inicio = db.Column(db.Date, nullable=False)
    data_fim = db.Column(db.Date, nullable=False)
    data_fim_original = db.Column(db.Date)  # Data original antes das prorrogações
    
    # Gestão e controle
    gestor = db.Column(db.String(200))  # Gestor principal
    gestor_suplente = db.Column(db.String(200))  # Gestor suplente
    fiscal = db.Column(db.String(200))  # Fiscal do contrato
    fiscal_suplente = db.Column(db.String(200))  # Fiscal suplente
    gestor_fiscal = db.Column(db.String(200))  # Campo legado - compatibilidade
    gestor_superior = db.Column(db.String(200))  # Campo legado - compatibilidade
    status = db.Column(db.String(20), default='ATIVO')
    
    # Informações adicionais de contratos municipais
    modalidade_licitacao = db.Column(db.String(50))  # Pregão, Tomada de Preços, etc.
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
    aditivos = db.relationship('AditivoContratual', backref='contrato', lazy=True, order_by='AditivoContratual.numero_aditivo', cascade='all, delete-orphan')
    
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


class NotaFiscal(db.Model):
    """Modelo para gerenciar notas fiscais"""
    __tablename__ = 'notas_fiscais'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Identificação
    numero_nota = db.Column(db.String(50), nullable=False, unique=True)
    serie = db.Column(db.String(10))
    chave_acesso = db.Column(db.String(44))
    
    # Relação com empenho
    empenho_id = db.Column(db.Integer, db.ForeignKey('empenhos.id'), nullable=False)
    empenho = db.relationship('Empenho', backref=db.backref('notas_fiscais', lazy=True))
    
    # Dados do fornecedor
    fornecedor_nome = db.Column(db.String(200), nullable=False)
    fornecedor_cnpj = db.Column(db.String(18), nullable=False)
    
    # Datas
    data_emissao = db.Column(db.Date, nullable=False)
    data_vencimento = db.Column(db.Date)
    data_recebimento = db.Column(db.Date)
    data_pagamento = db.Column(db.Date)
    
    # Valores
    valor_bruto = db.Column(db.Numeric(15, 2), nullable=False)
    valor_desconto = db.Column(db.Numeric(15, 2), default=0)
    valor_ir = db.Column(db.Numeric(15, 2), default=0)  # Imposto de Renda
    valor_inss = db.Column(db.Numeric(15, 2), default=0)  # INSS
    valor_iss = db.Column(db.Numeric(15, 2), default=0)  # ISS
    valor_outros_impostos = db.Column(db.Numeric(15, 2), default=0)
    valor_liquido = db.Column(db.Numeric(15, 2), nullable=False)
    
    # Status e controle
    status = db.Column(db.String(20), nullable=False, default='EM_ABERTO')
    # Status possíveis: EM_ABERTO, PROCESSANDO, PAGO, CANCELADO, VENCIDO
    
    # Informações de pagamento
    forma_pagamento = db.Column(db.String(50))  # PIX, TED, CHEQUE, etc.
    banco_pagamento = db.Column(db.String(100))
    agencia_pagamento = db.Column(db.String(20))
    conta_pagamento = db.Column(db.String(30))
    documento_pagamento = db.Column(db.String(100))  # Número do comprovante
    
    # Observações e anexos
    observacoes = db.Column(db.Text)
    arquivo_anexo = db.Column(db.String(255))  # Path para arquivo da nota
    
    # Metadados
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    usuario = db.relationship('User', backref=db.backref('notas_fiscais', lazy=True))
    
    def __repr__(self):
        return f'<NotaFiscal {self.numero_nota} - {self.status}>'
    
    def calcular_valores(self):
        """Calcula automaticamente o valor líquido"""
        total_descontos = (self.valor_desconto or 0)
        total_impostos = (
            (self.valor_ir or 0) + 
            (self.valor_inss or 0) + 
            (self.valor_iss or 0) + 
            (self.valor_outros_impostos or 0)
        )
        self.valor_liquido = (self.valor_bruto or 0) - total_descontos - total_impostos
        
    def get_status_color(self):
        """Retorna a cor do badge do status"""
        colors = {
            'EM_ABERTO': 'warning',
            'PROCESSANDO': 'info', 
            'PAGO': 'success',
            'CANCELADO': 'secondary',
            'VENCIDO': 'danger'
        }
        return colors.get(self.status, 'secondary')
    
    def get_status_display(self):
        """Retorna o nome amigável do status"""
        displays = {
            'EM_ABERTO': 'Em Aberto',
            'PROCESSANDO': 'Processando',
            'PAGO': 'Pago',
            'CANCELADO': 'Cancelado',
            'VENCIDO': 'Vencido'
        }
        return displays.get(self.status, self.status)
    
    def is_vencida(self):
        """Verifica se a nota está vencida"""
        if self.data_vencimento and self.status == 'EM_ABERTO':
            return datetime.now().date() > self.data_vencimento
        return False
    
    def dias_para_vencimento(self):
        """Calcula dias para vencimento (negativo se vencida)"""
        if self.data_vencimento:
            delta = self.data_vencimento - datetime.now().date()
            return delta.days
        return None
    
    @classmethod
    def create_from_data(cls, data):
        """Cria uma nova nota fiscal a partir dos dados"""
        nota = cls(
            numero_nota=data['numero_nota'],
            serie=data.get('serie'),
            chave_acesso=data.get('chave_acesso'),
            empenho_id=data['empenho_id'],
            fornecedor_nome=data['fornecedor_nome'],
            fornecedor_cnpj=data['fornecedor_cnpj'],
            data_emissao=data['data_emissao'],
            data_vencimento=data.get('data_vencimento'),
            data_recebimento=data.get('data_recebimento'),
            valor_bruto=data['valor_bruto'],
            valor_desconto=data.get('valor_desconto', 0),
            valor_ir=data.get('valor_ir', 0),
            valor_inss=data.get('valor_inss', 0),
            valor_iss=data.get('valor_iss', 0),
            valor_outros_impostos=data.get('valor_outros_impostos', 0),
            status=data.get('status', 'EM_ABERTO'),
            observacoes=data.get('observacoes'),
            usuario_id=data['usuario_id']
        )
        
        # Calcular valores automaticamente
        nota.calcular_valores()
        return nota


class ItemContrato(db.Model):
    """Modelo para itens/mercadorias do contrato"""
    __tablename__ = 'itens_contrato'
    
    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'), nullable=False)
    
    # Identificação do item
    lote = db.Column(db.String(20))  # Número do lote
    item = db.Column(db.String(50), nullable=False)  # Número/código do item
    
    # Descrição do produto
    descricao = db.Column(db.Text, nullable=False)  # Descrição completa
    marca = db.Column(db.String(100))  # Marca do produto
    
    # Quantidades e medidas
    quantidade = db.Column(db.Numeric(10, 3), nullable=False)  # Quantidade
    unidade = db.Column(db.String(20), nullable=False)  # UN, KG, L, M, etc.
    
    # Valores financeiros
    valor_unitario = db.Column(db.Numeric(10, 4), nullable=False)  # Preço unitário
    valor_total = db.Column(db.Numeric(15, 2), nullable=False)  # Total do item (calculado)
    
    # Metadados
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento
    contrato = db.relationship('Contrato', backref=db.backref('itens', lazy=True, cascade='all, delete-orphan'))
    
    def calcular_valor_total(self):
        """Calcula o valor total do item (quantidade * valor_unitario)"""
        if self.quantidade and self.valor_unitario:
            self.valor_total = Decimal(str(self.quantidade)) * Decimal(str(self.valor_unitario))
        else:
            self.valor_total = Decimal('0.00')
    
    def to_dict(self):
        """Converte o item para dicionário"""
        return {
            'id': self.id,
            'lote': self.lote,
            'item': self.item,
            'descricao': self.descricao,
            'marca': self.marca,
            'quantidade': float(self.quantidade) if self.quantidade else 0,
            'unidade': self.unidade,
            'valor_unitario': float(self.valor_unitario) if self.valor_unitario else 0,
            'valor_total': float(self.valor_total) if self.valor_total else 0
        }
    
    def __repr__(self):
        return f'<ItemContrato {self.item}: {self.descricao[:50]}>'

class AnotacaoContrato(db.Model):
    """Modelo para anotações de contratos"""
    __tablename__ = 'anotacoes_contratos'
    
    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id'), nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dados da anotação
    texto = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Arquivo anexado (opcional)
    nome_arquivo = db.Column(db.String(255))
    caminho_arquivo = db.Column(db.String(500))
    tipo_arquivo = db.Column(db.String(50))
    tamanho_arquivo = db.Column(db.Integer)
    
    # Relacionamentos
    contrato = db.relationship('Contrato', backref=db.backref('anotacoes', lazy=True, cascade='all, delete-orphan'))
    usuario = db.relationship('User', backref=db.backref('anotacoes', lazy=True))
    
    def to_dict(self):
        """Converte a anotação para dicionário"""
        return {
            'id': self.id,
            'texto': self.texto,
            'data_criacao': self.data_criacao.strftime('%d/%m/%Y %H:%M') if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.strftime('%d/%m/%Y %H:%M') if self.data_atualizacao else None,
            'usuario': self.usuario.nome if self.usuario else 'Usuário desconhecido',
            'nome_arquivo': self.nome_arquivo,
            'tipo_arquivo': self.tipo_arquivo,
            'tamanho_arquivo': self.tamanho_arquivo
        }
    
    def __repr__(self):
        return f'<AnotacaoContrato {self.id}: {self.texto[:50]}>'


class AnexoAnotacao(db.Model):
    """Modelo para anexos de anotações"""
    __tablename__ = 'anexos_anotacao'
    
    id = db.Column(db.Integer, primary_key=True)
    anotacao_id = db.Column(db.Integer, db.ForeignKey('anotacoes_contratos.id'), nullable=False)
    nome = db.Column(db.String(255), nullable=False)       # nome original
    caminho = db.Column(db.String(1024), nullable=False)   # caminho relativo no disco
    tamanho = db.Column(db.Integer, default=0)
    tipo = db.Column(db.String(50))                        # mime type
    data_upload = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    anotacao = db.relationship('AnotacaoContrato', 
                              backref=db.backref('anexos', lazy=True, cascade='all, delete-orphan'))
    
    def to_dict(self):
        """Converte o anexo para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'tamanho': self.tamanho,
            'tipo': self.tipo,
            'data_upload': self.data_upload.strftime('%d/%m/%Y %H:%M') if self.data_upload else None
        }
    
    def __repr__(self):
        return f'<AnexoAnotacao {self.id}: {self.nome}>'


class Comunicacao(db.Model):
    """Modelo para comunicações de workflow"""
    __tablename__ = 'comunicacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    contrato_id = db.Column(db.Integer, db.ForeignKey('contratos.id', ondelete='CASCADE'), 
                           nullable=False, index=True)
    titulo = db.Column(db.String(200), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    remetente = db.Column(db.String(120), nullable=False, default='Sistema')
    criado_em = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, 
                             onupdate=datetime.utcnow, nullable=False)
    
    # Relacionamento
    contrato = db.relationship('Contrato', 
                             backref=db.backref('comunicacoes', lazy='dynamic', 
                                               cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<Comunicacao {self.id}: {self.titulo}>'
