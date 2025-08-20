try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus.flowables import HRFlowable
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from datetime import datetime
import os
import tempfile
from models import Empenho, db

class ExportUtils:
    
    @staticmethod
    def export_to_excel(empenhos, filename=None):
        """Exporta lista de empenhos para Excel"""
        if not PANDAS_AVAILABLE:
            raise ImportError("Pandas não está instalado. Execute: pip install pandas openpyxl")
            
        if filename is None:
            filename = os.path.join(tempfile.gettempdir(), f'empenhos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        
        # Preparar dados
        dados = []
        for empenho in empenhos:
            dados.append({
                'Número Empenho': empenho.numero_empenho,
                'Pregão': empenho.numero_pregao,
                'Contrato': empenho.numero_contrato,
                'Aditivo': empenho.numero_aditivo or '',
                'Objeto': empenho.objeto,
                'Unidade Mensal': empenho.unidade_mensal or '',
                'Valor Unitário': float(empenho.valor_unitario) if empenho.valor_unitario else 0,
                'Data Empenho': empenho.data_empenho.strftime('%d/%m/%Y') if empenho.data_empenho else '',
                'Valor Empenhado': float(empenho.valor_empenhado) if empenho.valor_empenhado else 0,
                'Quantidade': float(empenho.quantidade) if empenho.quantidade else 0,
                'Valor Período': float(empenho.valor_periodo) if empenho.valor_periodo else 0,
                'Percentual Retenção': float(empenho.percentual_retencao) if empenho.percentual_retencao else 0,
                'Valor Retenção': float(empenho.valor_retencao) if empenho.valor_retencao else 0,
                'Valor Líquido': float(empenho.valor_liquido) if empenho.valor_liquido else 0,
                'Data Envio': empenho.data_envio.strftime('%d/%m/%Y') if empenho.data_envio else '',
                'Data Vencimento': empenho.data_vencimento.strftime('%d/%m/%Y') if empenho.data_vencimento else '',
                'Período Referência': empenho.periodo_referencia or '',
                'Status': empenho.status,
                'Nota Fiscal': empenho.nota_fiscal or '',
                'Saldo Remanescente': float(empenho.saldo_remanescente) if empenho.saldo_remanescente else 0,
                'Observações': empenho.observacoes or '',
                'Data Criação': empenho.data_criacao.strftime('%d/%m/%Y %H:%M') if empenho.data_criacao else '',
                'Usuário': empenho.usuario.nome if empenho.usuario else ''
            })
        
        # Criar DataFrame
        df = pd.DataFrame(dados)
        
        # Salvar no Excel com formatação
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Empenhos', index=False)
            
            # Obter a planilha para formatação
            worksheet = writer.sheets['Empenhos']
            
            # Ajustar largura das colunas
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Adicionar planilha de resumo
            resumo_data = {
                'Métrica': [
                    'Total de Empenhos',
                    'Valor Total Empenhado',
                    'Valor Total Líquido',
                    'Valor Total Retenção',
                    'Data do Relatório'
                ],
                'Valor': [
                    len(empenhos),
                    sum([float(e.valor_empenhado) if e.valor_empenhado else 0 for e in empenhos]),
                    sum([float(e.valor_liquido) if e.valor_liquido else 0 for e in empenhos]),
                    sum([float(e.valor_retencao) if e.valor_retencao else 0 for e in empenhos]),
                    datetime.now().strftime('%d/%m/%Y %H:%M')
                ]
            }
            
            if PANDAS_AVAILABLE:
                df_resumo = pd.DataFrame(resumo_data)
                df_resumo.to_excel(writer, sheet_name='Resumo', index=False)
        
        return filename
    
    @staticmethod
    def export_to_pdf(empenhos, filtros=None, filename=None):
        """Exporta lista de empenhos para PDF"""
        if not REPORTLAB_AVAILABLE:
            raise ImportError("ReportLab não está instalado. Execute: pip install reportlab")
            
        if filename is None:
            filename = os.path.join(tempfile.gettempdir(), f'empenhos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf')
        
        doc = SimpleDocTemplate(filename, pagesize=A4, 
                              rightMargin=72, leftMargin=72, 
                              topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        story = []
        
        # Cabeçalho com logo e nome do sistema
        logo_added = False
        try:
            # Tentar carregar a logo PNG se existir
            logo_png_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'img', 'logo_guarapuava.png')
            if os.path.exists(logo_png_path):
                logo_img = Image(logo_png_path, width=60, height=60)
                # Criar uma tabela para colocar logo e texto lado a lado
                logo_data = [
                    [logo_img, Paragraph("🏛️ PREFEITURA MUNICIPAL DE GUARAPUAVA<br/>SISTEMA DE GESTÃO DE EMPENHOS E CONTRATOS", 
                                        ParagraphStyle('LogoHeader', parent=styles['Heading1'], fontSize=14, 
                                                     alignment=0, textColor=colors.HexColor('#2C5530'), 
                                                     fontName='Helvetica-Bold'))]
                ]
                logo_table = Table(logo_data, colWidths=[80, 4*inch])
                logo_table.setStyle(TableStyle([
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('ALIGN', (1, 0), (1, 0), 'LEFT'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 0),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ]))
                story.append(logo_table)
                logo_added = True
        except Exception as e:
            print(f"Erro ao carregar logo: {e}")
            pass
        
        if not logo_added:
            # Cabeçalho textual com elementos visuais representando o brasão municipal
            # Criar um cabeçalho visual com símbolos municipais
            brasao_data = [
                ["🏛️", "PREFEITURA MUNICIPAL DE GUARAPUAVA"],
                ["👑", "SISTEMA DE GESTÃO DE EMPENHOS E CONTRATOS"]
            ]
            
            brasao_table = Table(brasao_data, colWidths=[0.5*inch, 5*inch])
            brasao_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (0, -1), 20),  # Emojis grandes
                ('FONTSIZE', (1, 0), (1, 0), 16),   # Título principal
                ('FONTSIZE', (1, 1), (1, 1), 12),   # Subtítulo
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#2C5530')),  # Verde municipal
                ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#FF6B35')),  # Laranja municipal
                ('ALIGN', (0, 0), (0, -1), 'CENTER'),
                ('ALIGN', (1, 0), (1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            story.append(brasao_table)
        
        # Linha separadora
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2C5530')))
        story.append(Spacer(1, 20))
        
        # Título do relatório
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=20,
            alignment=1,
            textColor=colors.HexColor('#FF6B35'),
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("RELATÓRIO DE EMPENHOS", title_style))
        
        # Informações do relatório em formato de tabela
        info_style = ParagraphStyle(
            'Info',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            textColor=colors.HexColor('#333333')
        )
        
        # Criar tabela de informações
        info_data = [
            ['Data do Relatório:', datetime.now().strftime('%d/%m/%Y %H:%M')],
            ['Total de Empenhos:', str(len(empenhos))],
        ]
        
        if filtros:
            info_data.append(['Filtros Aplicados:', ''])
            for key, value in filtros.items():
                if value:
                    info_data.append(['', f"• {key.replace('_', ' ').title()}: {value}"])
        
        info_table = Table(info_data, colWidths=[3*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#2C5530')),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(info_table)
        
        story.append(Spacer(1, 20))
        
        # Resumo financeiro
        valor_total_empenhado = sum([float(e.valor_empenhado) if e.valor_empenhado else 0 for e in empenhos])
        valor_total_liquido = sum([float(e.valor_liquido) if e.valor_liquido else 0 for e in empenhos])
        valor_total_retencao = sum([float(e.valor_retencao) if e.valor_retencao else 0 for e in empenhos])
        
        # Título da seção financeira
        financial_title = ParagraphStyle(
            'FinancialTitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.HexColor('#2C5530'),
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("RESUMO FINANCEIRO", financial_title))
        
        resumo_data = [
            ['Métrica', 'Valor'],
            ['Valor Total Empenhado', f'R$ {valor_total_empenhado:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
            ['Valor Total Líquido', f'R$ {valor_total_liquido:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')],
            ['Valor Total Retenção', f'R$ {valor_total_retencao:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[3*inch, 2*inch])
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5530')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F5F5F5')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2C5530')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        story.append(resumo_table)
        story.append(Spacer(1, 30))
        
        # Tabela de empenhos (apenas os principais campos para caber na página)
        # Título da seção de detalhes
        details_title = ParagraphStyle(
            'DetailsTitle',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.HexColor('#2C5530'),
            fontName='Helvetica-Bold'
        )
        story.append(Paragraph("DETALHES DOS EMPENHOS:", details_title))
        
        if empenhos:
            data = [['Empenho', 'Pregão', 'Contrato', 'Data', 'Valor Empenhado', 'Status']]
            
            for empenho in empenhos[:50]:  # Limitar a 50 para não ficar muito grande
                data.append([
                    empenho.numero_empenho[:15] + '...' if len(empenho.numero_empenho) > 15 else empenho.numero_empenho,
                    empenho.numero_pregao[:10] + '...' if len(empenho.numero_pregao) > 10 else empenho.numero_pregao,
                    empenho.numero_contrato[:10] + '...' if len(empenho.numero_contrato) > 10 else empenho.numero_contrato,
                    empenho.data_empenho.strftime('%d/%m/%Y') if empenho.data_empenho else '',
                    f'R$ {float(empenho.valor_empenhado):,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if empenho.valor_empenhado else 'R$ 0,00',
                    empenho.status
                ])
            
            table = Table(data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1.2*inch, 0.8*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2C5530')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('TOPPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F9F9F9')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#2C5530')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 1), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ]))
            
            story.append(table)
            
            if len(empenhos) > 50:
                story.append(Spacer(1, 12))
                note_style = ParagraphStyle(
                    'Note',
                    parent=styles['Normal'],
                    fontSize=9,
                    textColor=colors.HexColor('#666666'),
                    fontName='Helvetica-Oblique',
                    alignment=1
                )
                story.append(Paragraph(f"Mostrando apenas os primeiros 50 empenhos de {len(empenhos)} total.", note_style))
        
        # Rodapé
        story.append(Spacer(1, 30))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#2C5530')))
        
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#666666'),
            alignment=1
        )
        story.append(Paragraph("Sistema de Gestão de Empenhos e Contratos - Prefeitura Municipal de Guarapuava", footer_style))
        story.append(Paragraph(f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')}", footer_style))
        
        doc.build(story)
        return filename
    
    @staticmethod
    def create_backup():
        """Cria backup completo do sistema"""
        if not PANDAS_AVAILABLE:
            # Backup alternativo usando CSV se pandas não estiver disponível
            return ExportUtils.create_backup_csv()
            
        filename = os.path.join(tempfile.gettempdir(), f'backup_completo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx')
        
        # Obter todos os empenhos
        empenhos = Empenho.query.all()
        
        # Usar a função de exportação para Excel
        return ExportUtils.export_to_excel(empenhos, filename)
    
    @staticmethod
    def create_backup_csv():
        """Cria backup em formato CSV (alternativa sem pandas)"""
        import csv
        
        filename = os.path.join(tempfile.gettempdir(), f'backup_completo_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
        
        # Obter todos os empenhos
        empenhos = Empenho.query.all()
        
        # Escrever CSV
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            if empenhos:
                fieldnames = [
                    'ID', 'Número Pregão', 'Número CTR', 'Número Contrato', 'Número Empenho',
                    'Objeto', 'Fornecedor', 'CNPJ', 'Valor Unitário', 'Data Empenho',
                    'Valor Empenhado', 'Quantidade', 'Valor Período', 'Percentual Retenção',
                    'Valor Retenção', 'Valor Líquido', 'Data Envio', 'Data Vencimento',
                    'Período Referência', 'Status', 'Nota Fiscal', 'Saldo Remanescente',
                    'Observações', 'Data Criação', 'Usuário'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for empenho in empenhos:
                    writer.writerow({
                        'ID': empenho.id,
                        'Número Pregão': empenho.numero_pregao,
                        'Número CTR': empenho.numero_ctr or '',
                        'Número Contrato': empenho.numero_contrato or '',
                        'Número Empenho': empenho.numero_empenho,
                        'Objeto': empenho.objeto,
                        'Fornecedor': empenho.fornecedor,
                        'CNPJ': empenho.cnpj or '',
                        'Valor Unitário': float(empenho.valor_unitario) if empenho.valor_unitario else 0,
                        'Data Empenho': empenho.data_empenho.strftime('%d/%m/%Y') if empenho.data_empenho else '',
                        'Valor Empenhado': float(empenho.valor_empenhado) if empenho.valor_empenhado else 0,
                        'Quantidade': float(empenho.quantidade) if empenho.quantidade else 0,
                        'Valor Período': float(empenho.valor_periodo) if empenho.valor_periodo else 0,
                        'Percentual Retenção': float(empenho.percentual_retencao) if empenho.percentual_retencao else 0,
                        'Valor Retenção': float(empenho.valor_retencao) if empenho.valor_retencao else 0,
                        'Valor Líquido': float(empenho.valor_liquido) if empenho.valor_liquido else 0,
                        'Data Envio': empenho.data_envio.strftime('%d/%m/%Y') if empenho.data_envio else '',
                        'Data Vencimento': empenho.data_vencimento.strftime('%d/%m/%Y') if empenho.data_vencimento else '',
                        'Período Referência': empenho.periodo_referencia or '',
                        'Status': empenho.status,
                        'Nota Fiscal': empenho.nota_fiscal or '',
                        'Saldo Remanescente': float(empenho.saldo_remanescente) if empenho.saldo_remanescente else 0,
                        'Observações': empenho.observacoes or '',
                        'Data Criação': empenho.data_criacao.strftime('%d/%m/%Y %H:%M') if empenho.data_criacao else '',
                        'Usuário': empenho.usuario.nome if empenho.usuario else ''
                    })
        
        return filename
