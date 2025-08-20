with open('templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir a linha problemática do chat
content = content.replace('{{ url_for(\'chat.index\') }}', '#')
content = content.replace('url_for(\'chat.index\')', '\'#\'')

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Chat link desabilitado com sucesso')
