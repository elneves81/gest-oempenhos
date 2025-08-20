# 📱 Implementação de Campos Múltiplos para Email e Telefone do Responsável

## ✅ Funcionalidade Implementada

### 🎯 Objetivo
Adicionar botões [+] nos campos de email e telefone do responsável para permitir a inclusão de múltiplos contatos.

### 🔧 Modificações Realizadas

#### 1. **Frontend - Template HTML** (`templates/contratos/form_wtf.html`)

**Antes:**
```html
<div class="col-xl-3 col-lg-4">
    {{ render_field(form.responsavel_email, type="email", autocomplete="email") }}
</div>
<div class="col-xl-3 col-lg-4">
    {{ render_field(form.responsavel_telefone, autocomplete="tel", placeholder="(00) 00000-0000") }}
</div>
```

**Depois:**
```html
<div class="col-xl-3 col-lg-4">
    <label for="{{ form.responsavel_email.id }}" class="form-label">
        {{ form.responsavel_email.label.text }}
        <button type="button" class="btn btn-sm btn-outline-primary ms-2" 
                onclick="adicionarCampoEmail()" title="Adicionar mais um email">
            <i class="bi bi-plus"></i>
        </button>
    </label>
    <div id="emails-container">
        {{ form.responsavel_email(class="form-control", type="email", autocomplete="email") }}
    </div>
</div>
<div class="col-xl-3 col-lg-4">
    <label for="{{ form.responsavel_telefone.id }}" class="form-label">
        {{ form.responsavel_telefone.label.text }}
        <button type="button" class="btn btn-sm btn-outline-primary ms-2" 
                onclick="adicionarCampoTelefone()" title="Adicionar mais um telefone">
            <i class="bi bi-plus"></i>
        </button>
    </label>
    <div id="telefones-container">
        {{ form.responsavel_telefone(class="form-control", autocomplete="tel", placeholder="(00) 00000-0000") }}
    </div>
</div>
```

#### 2. **JavaScript - Funções Dinâmicas**

**Funções Adicionadas:**
- `adicionarCampoEmail()` - Adiciona novo campo de email
- `removerCampoEmail(button)` - Remove campo de email específico
- `adicionarCampoTelefone()` - Adiciona novo campo de telefone
- `removerCampoTelefone(button)` - Remove campo de telefone específico
- `aplicarMascaraTelefone(input)` - Aplica máscara automática nos telefones

**Características:**
- ✅ Contadores globais (`emailCounter`, `telefoneCounter`)
- ✅ Máscaras automáticas para telefones novos
- ✅ Botões de remoção individuais
- ✅ Nomes de campos corretos para o backend

#### 3. **Backend - Modelo de Dados** (`models.py`)

**Campos Adicionados:**
```python
responsavel_emails_extras = db.Column(db.Text)  # JSON com emails extras
responsavel_telefones_extras = db.Column(db.Text)  # JSON com telefones extras
```

#### 4. **Backend - Processamento** (`routes/contratos_wtf.py`)

**Função Nova:**
```python
def processar_campos_extras_responsavel(form_data):
    """Processa campos extras de email e telefone do responsável"""
    emails_extras = []
    telefones_extras = []
    
    # Processar emails extras
    if 'responsavel_emails_extras[]' in form_data:
        emails_raw = form_data.getlist('responsavel_emails_extras[]')
        emails_extras = [email.strip() for email in emails_raw if email.strip()]
    
    # Processar telefones extras
    if 'responsavel_telefones_extras[]' in form_data:
        telefones_raw = form_data.getlist('responsavel_telefones_extras[]')
        telefones_extras = [tel.strip() for tel in telefones_raw if tel.strip()]
    
    return emails_extras, telefones_extras
```

**Integração nas Funções de Criação e Edição:**
```python
# Processar campos extras de email e telefone
emails_extras, telefones_extras = processar_campos_extras_responsavel(request.form)
c.responsavel_emails_extras = json.dumps(emails_extras) if emails_extras else None
c.responsavel_telefones_extras = json.dumps(telefones_extras) if telefones_extras else None
```

### 🎨 Características da Interface

#### **Botões [+]**
- **Aparência:** Pequenos botões azuis ao lado dos labels
- **Ícone:** Bootstrap Icons `bi-plus`
- **Posição:** À direita do label do campo
- **Tooltip:** "Adicionar mais um email/telefone"

#### **Campos Dinâmicos**
- **Layout:** Input group com botão de remoção
- **Botão de Remoção:** Vermelho com ícone de lixeira
- **Máscaras:** Aplicadas automaticamente nos telefones
- **Validação:** Email validation automática

#### **Experiência do Usuário**
- ✅ Campos são adicionados dinamicamente
- ✅ Cada campo pode ser removido individualmente
- ✅ Máscaras aplicadas automaticamente
- ✅ Contadores para nomes únicos dos campos
- ✅ Visual consistente com o resto do formulário

### 🗃️ Armazenamento dos Dados

**Formato no Banco:**
- **Campo Principal:** `responsavel_email` / `responsavel_telefone` (string)
- **Campos Extras:** `responsavel_emails_extras` / `responsavel_telefones_extras` (JSON)

**Exemplo de Dados Salvos:**
```json
// responsavel_emails_extras
["contato2@empresa.com", "administrativo@empresa.com"]

// responsavel_telefones_extras  
["(11) 99999-8888", "(11) 3333-4444"]
```

### 🔄 Fluxo de Funcionamento

1. **Carregamento da Página:**
   - Campos principais são exibidos normalmente
   - Botões [+] são visíveis ao lado dos labels
   - Se for edição, campos extras são carregados automaticamente

2. **Adição de Campos:**
   - Usuário clica no botão [+]
   - Novo campo é criado dinamicamente
   - Contador é incrementado
   - Máscara é aplicada (telefones)

3. **Remoção de Campos:**
   - Usuário clica no botão de lixeira
   - Campo específico é removido
   - Outros campos permanecem intactos

4. **Salvamento:**
   - Campos principais salvos nos campos originais
   - Campos extras coletados em arrays
   - Arrays convertidos para JSON e salvos

### 🚀 Para Testar

**URL:** http://10.0.50.79:5000/contratos-wtf/novo

**Cenários de Teste:**
1. **Adicionar Email Extra:**
   - Preencher email principal
   - Clicar no [+] ao lado de "Email"
   - Preencher segundo email
   - Verificar se ambos são salvos

2. **Adicionar Telefone Extra:**
   - Preencher telefone principal
   - Clicar no [+] ao lado de "Telefone"
   - Verificar aplicação da máscara automática
   - Preencher segundo telefone

3. **Remover Campos:**
   - Adicionar múltiplos campos
   - Remover campos específicos usando lixeira
   - Verificar que outros permanecem

4. **Edição de Contrato:**
   - Criar contrato com campos extras
   - Editar o contrato
   - Verificar se campos extras são carregados
   - Adicionar/remover campos na edição

### 📊 Benefícios Implementados

1. **Flexibilidade:** Múltiplos contatos por responsável
2. **Usabilidade:** Interface intuitiva com botões [+]
3. **Consistência:** Visual integrado ao sistema existente
4. **Robustez:** Validação e máscaras automáticas
5. **Manutenibilidade:** Código organizado e documentado

### 🔧 Arquivos Modificados

- ✅ `templates/contratos/form_wtf.html` - Interface e JavaScript
- ✅ `models.py` - Novos campos no banco
- ✅ `routes/contratos_wtf.py` - Processamento backend
- ✅ Documentação criada

---
*Implementação concluída em: 18/08/2025*
*Status: ✅ Funcionalidade Completa e Operacional*
