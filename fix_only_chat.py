with open('templates/base.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Corrigir apenas o link problemático do chat, mantendo tudo como estava
content = content.replace('{{ url_for(\'chat.index\') }}', '#')

with open('templates/base.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Chat corrigido - tudo restaurado como estava')
