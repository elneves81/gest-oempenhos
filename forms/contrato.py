# forms/contrato.py
from decimal import Decimal, InvalidOperation
from datetime import datetime
from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, DateField, DecimalField,
    IntegerField, FileField, TelField, EmailField, SubmitField
)
from wtforms.validators import DataRequired, Optional, Length, NumberRange, Email, ValidationError
import re

ALLOWED_EXTS = {"pdf", "doc", "docx"}
MAX_UPLOAD_MB = 10

# --------- Utilitários ---------
def _only_digits(s: str) -> str:
    return re.sub(r"\D", "", s or "")

def is_valid_cnpj(cnpj: str) -> bool:
    c = _only_digits(cnpj)
    if len(c) != 14 or c == c[0] * 14:
        return False

    def calc_digit(nums, weights):
        s = sum(int(n)*w for n, w in zip(nums, weights))
        r = s % 11
        return "0" if r < 2 else str(11 - r)

    d1 = calc_digit(c[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
    d2 = calc_digit(c[:12] + d1, [6,5,4,3,2,9,8,7,6,5,4,3,2])
    return c[-2:] == d1 + d2

class BRLDecimalField(DecimalField):
    """
    Aceita '1.234,56' e converte para Decimal('1234.56').
    """
    def process_formdata(self, valuelist):
        if not valuelist:
            return
        s = (valuelist[0] or "").strip()
        if s == "":
            self.data = None
            return
        # remove separador de milhar . e troca vírgula por ponto
        norm = s.replace(".", "").replace(",", ".")
        try:
            self.data = Decimal(norm)
        except InvalidOperation:
            raise ValueError("Valor monetário inválido")

# --------- Validadores custom ---------
def CNPJ(optional=False):
    def _v(form, field):
        v = (field.data or "").strip()
        if optional and not v:
            return
        if not is_valid_cnpj(v):
            raise ValidationError("CNPJ inválido")
    return _v

def FileAllowedExts():
    def _v(form, field):
        f = field.data
        if not f or not getattr(f, "filename", ""):
            return
        ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
        if ext not in ALLOWED_EXTS:
            raise ValidationError("Arquivo inválido. Envie PDF, DOC ou DOCX.")
    return _v

def FileMaxSize():
    def _v(form, field):
        f = field.data
        if not f or not getattr(f, "stream", None):
            return
        # move cursor, mede, volta
        pos = f.stream.tell()
        f.stream.seek(0, 2)
        size = f.stream.tell()
        f.stream.seek(pos, 0)
        if size > MAX_UPLOAD_MB * 1024 * 1024:
            raise ValidationError(f"Arquivo excede {MAX_UPLOAD_MB} MB.")
    return _v

# --------- Form ---------
class ContratoForm(FlaskForm):
    # Identificação
    numero_pregao   = StringField("Número da Modalidade", validators=[Optional(), Length(max=100)])
    numero_contrato = StringField("Número do Contrato", validators=[DataRequired(), Length(max=100)])
    numero_processo = StringField("Número do Processo", validators=[Optional(), Length(max=100)])

    ano_pregao   = IntegerField("Ano da Modalidade", validators=[Optional(), NumberRange(min=2000, max=2100)])
    ano_contrato = IntegerField("Ano do Contrato", validators=[Optional(), NumberRange(min=2000, max=2100)])
    ano_processo = IntegerField("Ano do Processo", validators=[Optional(), NumberRange(min=2000, max=2100)])
    digito_verificador = StringField("Dígito Verificador", validators=[Optional(), Length(max=10)])

    # Tipo do contrato
    tipo_contratacao = SelectField(
        "Tipo",
        choices=[
            ("", "Selecione..."),
            ("SERVICO", "Serviço"),
            ("COMPRA", "Compra"),
            ("LOCACAO", "Locação"),
        ],
        validators=[Optional()]
    )

    objeto  = TextAreaField("Objeto do Contrato", validators=[DataRequired(), Length(max=10000)])
    lei_base = TextAreaField("Fundamentação Legal", validators=[Optional(), Length(max=5000)])

    modalidade_licitacao = SelectField(
        "Modalidade de Licitação",
        choices=[
            ("", "Selecione..."),
            ("PREGAO", "Pregão"),
            ("TOMADA_PRECOS", "Tomada de Preços"),
            ("CONCORRENCIA", "Concorrência"),
            ("CONVITE", "Convite"),
            ("DISPENSA", "Dispensa"),
            ("INEXIGIBILIDADE", "Inexigibilidade"),
        ],
        validators=[Optional()]
    )
    orgao_contratante = StringField("Órgão Contratante", validators=[Optional(), Length(max=200)])
    secretaria        = StringField("Secretaria", validators=[Optional(), Length(max=200)])

    # Fornecedor
    fornecedor      = StringField("Nome do Fornecedor", validators=[DataRequired(), Length(max=255)])
    cnpj_fornecedor = StringField("CNPJ do Fornecedor", validators=[Optional(), CNPJ(optional=True)])

    # Responsável
    responsavel_nome  = StringField("Nome do Responsável", validators=[Optional(), Length(max=200)])
    responsavel_cargo = StringField("Cargo do Responsável", validators=[Optional(), Length(max=200)])
    responsavel_email = EmailField("Email do Responsável", validators=[Optional(), Email()])
    responsavel_telefone = TelField("Telefone do Responsável", validators=[Optional(), Length(max=30)])

    # Financeiro
    valor_total   = BRLDecimalField("Valor Total do Contrato", places=2, validators=[DataRequired()])
    valor_inicial = BRLDecimalField("Valor Inicial", places=2, validators=[Optional()])

    # Prazos
    data_assinatura   = DateField("Data de Assinatura", format="%Y-%m-%d", validators=[DataRequired()])
    data_inicio       = DateField("Data de Início", format="%Y-%m-%d", validators=[DataRequired()])
    data_fim          = DateField("Data de Fim", format="%Y-%m-%d", validators=[DataRequired()])
    # data_fim_original removido conforme solicitado

    # Gestão do Contrato
    gestor          = StringField("Gestor", validators=[Optional(), Length(max=200)])
    gestor_suplente = StringField("Gestor Suplente", validators=[Optional(), Length(max=200)])
    fiscal          = StringField("Fiscal", validators=[Optional(), Length(max=200)])
    fiscal_suplente = StringField("Fiscal Suplente", validators=[Optional(), Length(max=200)])

    # Campos legados (compatibilidade)
    gestor_fiscal   = StringField("Gestor Fiscal", validators=[Optional(), Length(max=200)])
    gestor_superior = StringField("Gestor Superior", validators=[Optional(), Length(max=200)])

    # Status
    status = SelectField(
        "Status do Contrato",
        choices=[
            ("ATIVO", "Ativo"),
            ("ENCERRADO", "Encerrado"),
            ("SUSPENSO", "Suspenso"),
            ("RESCINDIDO", "Rescindido"),
        ],
        default="ATIVO",
        validators=[Optional()]
    )

    # Garantias
    tipo_garantia = SelectField(
        "Tipo de Garantia",
        choices=[
            ("", "Sem Garantia"),
            ("CAUCAO", "Caução em Dinheiro"),
            ("SEGURO_GARANTIA", "Seguro-Garantia"),
            ("FIANCA_BANCARIA", "Fiança Bancária"),
        ],
        validators=[Optional()]
    )
    valor_garantia = BRLDecimalField("Valor da Garantia", places=2, validators=[Optional()])
    validade_garantia = DateField("Validade da Garantia", format="%Y-%m-%d", validators=[Optional()])

    # Anexos / Observações
    arquivo_contrato = FileField("Arquivo do Contrato", validators=[Optional(), FileAllowedExts(), FileMaxSize()])
    observacoes = TextAreaField("Observações", validators=[Optional(), Length(max=10000)])

    submit = SubmitField("Salvar")

    # Coerência de datas
    def validate_data_fim(self, field):
        di = self.data_inicio.data
        df = field.data
        if di and df and df <= di:
            raise ValidationError("A data de fim deve ser posterior à data de início.")
