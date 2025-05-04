# ZipFileSender - Enviador de Arquivos para Telegram

## Descrição
ZipFileSender é uma ferramenta para automatizar o envio de arquivos para canais do Telegram. O programa divide automaticamente os arquivos em partes de tamanho adequado para o Telegram (por padrão, até 1900 MB), compacta-os e envia sequencialmente para o canal configurado.

## Créditos á parte
Existe um repositório aonde o mantenedor diz ter parte do seu código copiado por mim, sem problemas aqui está uma menção pelos nomes iguais: https://github.com/viniped/Zip-File-Sender

## Características
- Autenticação via API do Telegram (api_id e api_hash)
- Divisão automática de arquivos em partes
- Compressão paralela usando múltiplas threads
- Barra de progresso para acompanhamento em tempo real
- Configuração flexível via arquivo config.json
- Suporte a legendas personalizadas
- Tratamento de erros e reconexão automática

## Requisitos
- Python 3.7 ou superior
- Bibliotecas listadas em requirements.txt
- API ID e API Hash do Telegram (obtenha em https://my.telegram.org)

## Instalação

### Windows
1. Clone ou baixe este repositório
2. Execute o arquivo `main.bat` para iniciar o programa

### Linux/macOS
1. Clone ou baixe este repositório
2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
3. Execute o programa:
   ```
   python main.py
   ```

## Como Usar

1. Obtenha seu API ID e API Hash em https://my.telegram.org
2. Execute o programa pela primeira vez para autenticar com suas credenciais
3. Configure o ID do canal no arquivo `config.json`
4. Coloque as pastas que deseja enviar na pasta `input/`
5. Execute o programa novamente para iniciar o processamento e envio

### Como obter o ID do canal corretamente

O ID do canal deve estar no formato correto para que o programa funcione. Existem várias maneiras de obter o ID do canal:

1. **Para canais públicos**: Use o nome de usuário do canal com @ (exemplo: `@meucanal`). 

2. **Para canais privados**: Você precisará do ID numérico do canal, que geralmente começa com `-100` seguido de números. Para obter este ID:
   - Envie uma mensagem para o canal
   - Encaminhe esta mensagem para @userinfobot
   - O bot responderá com informações incluindo o ID do chat/canal

3. **Formatos aceitos no config.json**:
   - Nome de usuário: `@meucanal`
   - ID numérico completo: `-1001234567890`
   - ID numérico simples: `-1234567890` (o programa tentará adicionar o prefixo correto)

**IMPORTANTE**: Você deve ser membro do canal e ter permissões para enviar mensagens nele.

### Estrutura de Pastas
- `input/`: Coloque aqui as pastas com arquivos a serem enviados
- `output/`: Arquivos processados e compactados
- `config.json`: Configurações do programa
- `caption.txt`: Texto que será usado como legenda para imagens

### Arquivo config.json
```json
{
    "channel_id": "seu_canal_id",
    "max_size_mb": 1900,
    "threads": 4,
    "compression_level": 0,
    "delete_after_upload": true,
    "max_concurrent_transmissions": 2
}
```

- `channel_id`: ID do canal para envio dos arquivos
- `max_size_mb`: Tamanho máximo de cada parte em MB
- `threads`: Número de threads para compactação paralela
- `compression_level`: Nível de compressão (0 = sem compressão, 9 = máxima)
- `delete_after_upload`: Se true, remove os arquivos originais após o envio
- `max_concurrent_transmissions`: Número máximo de transmissões simultâneas (uploads). Aumentar este valor pode melhorar a velocidade de envio, mas valores muito altos podem causar bloqueios temporários.

## Solução de Problemas

### Problemas na Busca de Canais

Se o script ficar travado ao buscar seus canais ou não mostrar nenhum canal quando você sabe que tem acesso a pelo menos um, tente estas soluções:

1. **Verifique sua sessão do Telegram**: 
   - Remova o arquivo `user.session` e reinicie o programa para criar uma nova sessão

2. **Problemas de rede**:
   - Se estiver usando VPN, tente desativar temporariamente
   - Verifique sua conexão com a internet

3. **Inserção manual do ID do canal**:
   - O script agora oferece a opção de inserir o ID do canal manualmente quando a busca automática falhar
   - Para canais públicos, use o formato `@nome_do_canal`
   - Para canais privados, use o ID numérico (geralmente começa com `-100`)
   - Você pode obter o ID numérico usando bots como `@username_to_id_bot` no Telegram

4. **Permissões**:
   - Certifique-se de que sua conta é membro do canal
   - Você deve ter permissões para enviar mensagens no canal

### Erro PEER_ID_INVALID

Este erro geralmente ocorre quando:
- O ID do canal está em formato incorreto
- Você não é membro do canal
- O canal não existe

A nova funcionalidade de listagem e seleção de canais resolve este problema automaticamente ao mostrar apenas canais válidos aos quais você tem acesso.

### Outros erros comuns

- **FloodWait**: O programa irá esperar automaticamente o tempo necessário e tentar novamente
- **Erros de conexão**: Verifique sua conexão com a internet e tente novamente
- **Falha na autenticação**: Se a sessão estiver corrompida, o programa irá removê-la. Execute novamente e faça login.
- **Timeout**: Se o programa parecer travar durante a comunicação com o Telegram, reinicie-o e tente novamente

## Notas
- Para arquivos de imagem (jpg, png), será usada a legenda do arquivo caption.txt
- Você pode colocar um arquivo "cover.jpg" ou "cover.png" em cada pasta para ser enviado como capa
- O programa mantém a sessão do Telegram, então você só precisa autenticar uma vez

## Contribuições
Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.

## Licença
Este projeto está licenciado sob a Licença MIT - veja o arquivo LICENSE para detalhes.

## Créditos
Desenvolvido e mantido por [Bypass](https://github.com/z5ta9b5tbMC5Jr).

## Otimização de Velocidade de Upload

Para melhorar a velocidade de envio dos arquivos, você pode ajustar as seguintes configurações:

1. **Aumente o valor de `max_concurrent_transmissions`**: 
   - Valores entre 2 e 4 geralmente funcionam bem
   - Valores muito altos podem fazer com que o Telegram bloqueie temporariamente sua conta (FloodWait)

2. **Ajuste o nível de compressão**:
   - Para arquivos que já estão comprimidos (como vídeos MP4, MP3, etc.), use `compression_level: 0`
   - Para arquivos não comprimidos, um valor de 1-3 oferece bom equilíbrio entre velocidade e tamanho

3. **Requisitos de Rede**:
   - Uma conexão estável é mais importante que uma conexão rápida
   - Evite usar VPNs durante o upload, pois podem reduzir a velocidade

4. **Horário de Upload**:
   - Os servidores do Telegram podem estar mais lentos em horários de pico
   - Tente fazer uploads em horários menos movimentados

5. **Tamanho dos Arquivos**:
   - Arquivos menores tendem a fazer upload mais rápido
   - O valor padrão de 1900 MB é o máximo recomendado para cada parte

Nota: O programa já implementa tamanhos de chunk otimizados baseados no tamanho do arquivo e utiliza múltiplas transmissões concorrentes para maximizar a velocidade.
