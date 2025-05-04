#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import sys
from pyrogram import Client, errors, filters
from pyrogram.types import Chat
from auto_zip import process_folder
from tqdm import tqdm
from utils import *
import logging
import time
from datetime import datetime
from colorama import Fore, Back, Style
import re

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("zipfilesender.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ZipFileSender")

def clear_screen():
    """Limpa a tela do terminal."""
    os.system('clear || cls')

def read_caption():
    """Lê a legenda do arquivo caption.txt."""
    try:
        with open('caption.txt', 'r', encoding='utf-8') as file:
            caption = file.read().strip()
            logger.info(f"Legenda carregada: {caption[:30]}...")
            return caption
    except FileNotFoundError:
        logger.warning("Arquivo caption.txt não encontrado. Enviando sem legenda.")
        return None
    except Exception as e:
        logger.error(f"Erro ao ler caption.txt: {str(e)}")
        return None

def list_available_channels(app):
    """
    Lista os canais disponíveis na conta do usuário.
    
    Args:
        app: Cliente Pyrogram
        
    Returns:
        dict: Dicionário com índices como chaves e informações do canal como valores
    """
    channels = {}
    index = 1
    
    try:
        print(f"{Fore.CYAN}{Style.BRIGHT}🔍 Buscando seus canais do Telegram...{Style.RESET_ALL}")
        
        # Buscar diálogos com limite e timeout
        try:
            # Usar limite para evitar busca excessiva e timeout para evitar travamento
            dialogs = list(app.get_dialogs(limit=100))
            
            # Contadores para diagnóstico
            total_dialogs = len(dialogs)
            total_channels = 0
            total_supergroups = 0
            total_groups = 0
            
            # Log para debug
            print(f"{Fore.CYAN}ℹ️ Diálogos recuperados: {total_dialogs}{Style.RESET_ALL}")
            
            # Filtrar apenas canais e supergrupos
            found_channels = []
            for dialog in dialogs:
                chat = dialog.chat
                if chat.type == "channel":
                    found_channels.append(chat)
                    total_channels += 1
                elif chat.type == "supergroup":
                    found_channels.append(chat)
                    total_supergroups += 1
                elif chat.type == "group":
                    total_groups += 1
            
            # Informações mais detalhadas para diagnóstico
            print(f"{Fore.CYAN}ℹ️ Estatísticas encontradas: {total_channels} canais, {total_supergroups} supergrupos, {total_groups} grupos comuns{Style.RESET_ALL}")
            
            if not found_channels:
                print(f"{Fore.YELLOW}⚠️ Nenhum canal ou supergrupo encontrado na sua conta.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}ℹ️ Certifique-se de que sua conta está inscrita em algum canal ou grupo.{Style.RESET_ALL}")
                return {}
            
            # Ordenar canais por data de acesso (mais recentes primeiro)
            # Como não temos a data diretamente, usamos o ID como aproximação
            found_channels.sort(key=lambda x: abs(x.id), reverse=True)
            
            # Limitar a 10 canais mais recentes
            found_channels = found_channels[:10]
            
            print(f"{Fore.GREEN}✅ Encontrados {len(found_channels)} canais/grupos:{Style.RESET_ALL}\n")
            
            for chat in found_channels:
                chat_id = chat.id
                chat_title = chat.title
                chat_username = getattr(chat, "username", "Privado")
                chat_type = "Canal" if chat.type == "channel" else "Grupo"
                
                # Armazenar informações do canal
                channels[index] = {
                    "id": chat_id,
                    "title": chat_title,
                    "username": chat_username,
                    "type": chat_type
                }
                
                # Mostrar informações do canal
                print(f"{Fore.CYAN}[{index}] {Fore.WHITE}{chat_title} {Fore.YELLOW}({chat_type}){Style.RESET_ALL}")
                print(f"    ID: {chat_id}")
                if chat_username != "Privado":
                    print(f"    Username: @{chat_username}")
                print("")
                
                index += 1
            
            return channels
        except errors.FloodWait as e:
            print(f"{Fore.YELLOW}⚠️ Limite de requisições atingido. Aguarde {e.x} segundos e tente novamente.{Style.RESET_ALL}")
            logger.warning(f"Limite de requisições atingido: {str(e)}")
            return {}
        except errors.Unauthorized as e:
            print(f"{Fore.RED}❌ Erro de autorização. Verifique se sua sessão é válida: {str(e)}{Style.RESET_ALL}")
            logger.error(f"Erro de autorização: {str(e)}")
            return {}
        except TimeoutError:
            print(f"{Fore.RED}❌ Tempo esgotado ao buscar diálogos. Verifique sua conexão com a internet.{Style.RESET_ALL}")
            logger.error("Timeout ao buscar diálogos")
            return {}
    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao listar canais: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Erro ao listar canais: {str(e)}")
        return {}

def show_troubleshooting_help():
    """Exibe instruções de solução de problemas para o usuário."""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}📋 Guia de solução de problemas:{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Se você está enfrentando problemas para listar seus canais:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}1. Verifique se sua conta do Telegram tem canais/grupos que você administra ou participa{Style.RESET_ALL}")
    print(f"{Fore.WHITE}2. Certifique-se de que sua sessão do Telegram está válida{Style.RESET_ALL}")
    print(f"{Fore.WHITE}3. Se você está usando VPN, tente desativar temporariamente{Style.RESET_ALL}")
    print(f"{Fore.WHITE}4. Se o problema persistir, tente reiniciar o programa{Style.RESET_ALL}")
    print(f"{Fore.WHITE}5. Como último recurso, remova o arquivo user.session e recrie sua autenticação{Style.RESET_ALL}")
    print(f"{Fore.WHITE}6. Ás vezes canais recém criados podem demorar para pegar o ID, tente novamente mais tarde{Style.RESET_ALL}")

    print(f"\n{Fore.CYAN}{Style.BRIGHT}Como ingressar em um canal ou grupo:{Style.RESET_ALL}")
    print(f"{Fore.WHITE}1. Abra o aplicativo do Telegram no seu celular ou desktop{Style.RESET_ALL}")
    print(f"{Fore.WHITE}2. Para canais públicos, use a função de busca e digite o nome do canal{Style.RESET_ALL}")
    print(f"{Fore.WHITE}3. Para canais privados, você precisa de um link de convite ou ser adicionado por um administrador{Style.RESET_ALL}")
    print(f"{Fore.WHITE}4. Você também pode criar seu próprio canal ou grupo: no aplicativo, clique no botão de nova mensagem e selecione 'Novo Grupo' ou 'Novo Canal'{Style.RESET_ALL}")
    
    print(f"\n{Fore.GREEN}Dica: Você também pode inserir o ID do canal manualmente.{Style.RESET_ALL}")
    print(f"{Fore.WHITE}- Para canais públicos, use @nome_do_canal{Style.RESET_ALL}")
    print(f"{Fore.WHITE}- Para canais privados, use o ID numérico (geralmente começa com -100){Style.RESET_ALL}")
    print(f"{Fore.WHITE}- O ID numérico pode ser obtido usando bots como @username_to_id_bot{Style.RESET_ALL}")
    print()

def select_channel(app, config):
    """
    Permite ao usuário selecionar um canal para envio.
    
    Args:
        app: Cliente Pyrogram
        config: Configuração atual
        
    Returns:
        str: ID do canal selecionado ou None se cancelado
    """
    try:
        # Tentar usar ID configurado primeiro
        channel_id = config.get('channel_id', '')
        if channel_id:
            try:
                print(f"{Fore.CYAN}🔍 Tentando usar canal configurado em config.json: {channel_id}{Style.RESET_ALL}")
                validated_id = verify_channel_id(app, channel_id)
                if validated_id:
                    print(f"{Fore.GREEN}✅ Canal configurado é válido!{Style.RESET_ALL}")
                    return validated_id
            except:
                print(f"{Fore.YELLOW}⚠️ Canal configurado não é válido. Mostrando lista de canais disponíveis...{Style.RESET_ALL}")
        
        # Listar canais disponíveis
        print(f"{Fore.CYAN}🔍 Buscando canais disponíveis, aguarde...{Style.RESET_ALL}")
        try:
            channels = list_available_channels(app)
        except Exception as e:
            print(f"{Fore.RED}❌ Erro ao buscar canais: {str(e)}{Style.RESET_ALL}")
            channels = {}
        
        # Se não encontrar canais automaticamente, oferecer entrada manual
        if not channels:
            print(f"{Fore.YELLOW}⚠️ Não foi possível obter a lista de canais automaticamente.{Style.RESET_ALL}")
            
            # Mostrar ajuda de solução de problemas
            show_troubleshooting_help()
            
            print(f"{Fore.CYAN}{Style.BRIGHT}Você tem duas opções:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}1) Inserir o ID do canal manualmente{Style.RESET_ALL}")
            print(f"{Fore.WHITE}2) Cancelar a operação{Style.RESET_ALL}")
            
            choice = input(f"{Fore.YELLOW}Escolha uma opção (1/2): {Style.RESET_ALL}")
            
            if choice == "1":
                print(f"{Fore.CYAN}{Style.BRIGHT}Digite o ID do canal ou nome de usuário (@username):{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}ℹ️ Dicas para o ID do canal:{Style.RESET_ALL}")
                print(f"{Fore.WHITE}- Para canais públicos, use @nome_do_canal{Style.RESET_ALL}")
                print(f"{Fore.WHITE}- Para canais privados, use o ID numérico (geralmente começa com -100){Style.RESET_ALL}")
                print(f"{Fore.WHITE}- Você deve ser membro do canal para enviar mensagens{Style.RESET_ALL}")
                
                manual_id = input(f"{Fore.YELLOW}ID do canal: {Style.RESET_ALL}")
                if manual_id:
                    validated_id = verify_channel_id(app, manual_id)
                    if validated_id:
                        # Atualizar config.json com o canal inserido manualmente
                        config['channel_id'] = str(validated_id)
                        with open('config.json', 'w', encoding='utf-8') as f:
                            json.dump(config, f, indent=4)
                        print(f"{Fore.GREEN}✅ Arquivo config.json atualizado com o novo canal.{Style.RESET_ALL}")
                        return validated_id
                    else:
                        print(f"{Fore.RED}❌ ID do canal inválido ou você não tem acesso.{Style.RESET_ALL}")
                        return None
                else:
                    print(f"{Fore.YELLOW}Operação cancelada pelo usuário.{Style.RESET_ALL}")
                    return None
            else:
                print(f"{Fore.YELLOW}Operação cancelada pelo usuário.{Style.RESET_ALL}")
                return None
        
        # Solicitar seleção ao usuário
        while True:
            try:
                print(f"{Fore.CYAN}{Style.BRIGHT}Selecione um canal pelo número, digite 'm' para entrada manual, ou 'q' para sair:{Style.RESET_ALL}")
                choice = input(f"{Fore.YELLOW}> {Style.RESET_ALL}")
                
                if choice.lower() == 'q':
                    print(f"{Fore.YELLOW}Operação cancelada pelo usuário.{Style.RESET_ALL}")
                    return None
                
                if choice.lower() == 'm':
                    # Opção para entrada manual
                    print(f"{Fore.CYAN}{Style.BRIGHT}Digite o ID do canal ou nome de usuário (@username):{Style.RESET_ALL}")
                    manual_id = input(f"{Fore.YELLOW}ID do canal: {Style.RESET_ALL}")
                    if manual_id:
                        validated_id = verify_channel_id(app, manual_id)
                        if validated_id:
                            # Atualizar config.json com o canal inserido manualmente
                            config['channel_id'] = str(validated_id)
                            with open('config.json', 'w', encoding='utf-8') as f:
                                json.dump(config, f, indent=4)
                            print(f"{Fore.GREEN}✅ Arquivo config.json atualizado com o novo canal.{Style.RESET_ALL}")
                            return validated_id
                        else:
                            print(f"{Fore.RED}❌ ID do canal inválido ou você não tem acesso.{Style.RESET_ALL}")
                            continue
                    else:
                        continue
                
                choice = int(choice)
                if choice in channels:
                    selected = channels[choice]
                    print(f"{Fore.GREEN}✅ Canal selecionado: {selected['title']}{Style.RESET_ALL}")
                    
                    # Atualizar config.json com o canal selecionado
                    config['channel_id'] = str(selected['id'])
                    with open('config.json', 'w', encoding='utf-8') as f:
                        json.dump(config, f, indent=4)
                    print(f"{Fore.GREEN}✅ Arquivo config.json atualizado com o novo canal.{Style.RESET_ALL}")
                    
                    return str(selected['id'])
                else:
                    print(f"{Fore.RED}❌ Opção inválida. Tente novamente.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED}❌ Digite um número válido, 'm' para entrada manual, ou 'q' para sair.{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}❌ Erro: {str(e)}{Style.RESET_ALL}")
        
    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao selecionar canal: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Erro ao selecionar canal: {str(e)}")
        return None

def verify_channel_id(app, channel_id):
    """
    Verifica se o ID do canal é válido e se o usuário tem acesso a ele.
    Ajusta o formato do ID se necessário.
    
    Args:
        app: Cliente Pyrogram
        channel_id (str): ID do canal a ser verificado
        
    Returns:
        str: ID do canal corrigido ou None se inválido
    """
    try:
        # Remover espaços em branco
        channel_id = channel_id.strip()
        
        # Verificar se é um ID numérico sem o prefixo -100
        if channel_id.lstrip('-').isdigit():
            # Se for apenas dígitos (com ou sem um sinal de menos)
            numeric_id = int(channel_id)
            
            # Se for um número positivo, presumimos que possa ser um ID de canal sem o prefixo correto
            if numeric_id > 0:
                print(f"{Fore.YELLOW}⚠️ ID do canal positivo detectado. Tentando converter para formato adequado...{Style.RESET_ALL}")
                channel_id = f"-100{numeric_id}"
            # Se for negativo mas não começar com -100
            elif not channel_id.startswith('-100') and numeric_id < 0:
                # Extrair o número após o sinal de menos
                abs_id = abs(numeric_id)
                channel_id = f"-100{abs_id}"
                print(f"{Fore.YELLOW}⚠️ Convertendo ID para formato adequado: {channel_id}{Style.RESET_ALL}")
        
        # Tentar encontrar o chat pelo ID
        print(f"{Fore.CYAN}🔍 Verificando acesso ao canal {channel_id}...{Style.RESET_ALL}")
        try:
            chat = app.get_chat(channel_id)
            print(f"{Fore.GREEN}✅ Canal encontrado: {chat.title}{Style.RESET_ALL}")
            return channel_id
        except errors.RPCError as e:
            if "CHANNEL_INVALID" in str(e) or "PEER_ID_INVALID" in str(e):
                # Tentar outros formatos se o atual falhar
                print(f"{Fore.YELLOW}⚠️ ID do canal não encontrado no formato atual. Tentando outros formatos...{Style.RESET_ALL}")
                
                # Tentar com -100 se não foi tentado ainda
                if not channel_id.startswith('-100') and channel_id.lstrip('-').isdigit():
                    abs_id = abs(int(channel_id))
                    new_id = f"-100{abs_id}"
                    print(f"{Fore.CYAN}🔄 Tentando com formato: {new_id}{Style.RESET_ALL}")
                    try:
                        chat = app.get_chat(new_id)
                        print(f"{Fore.GREEN}✅ Canal encontrado: {chat.title}{Style.RESET_ALL}")
                        return new_id
                    except:
                        pass
                
                # Tentar com @ se for um nome de usuário
                if not channel_id.startswith('@') and not channel_id.isdigit() and not channel_id.startswith('-'):
                    new_id = f"@{channel_id}"
                    print(f"{Fore.CYAN}🔄 Tentando com formato: {new_id}{Style.RESET_ALL}")
                    try:
                        chat = app.get_chat(new_id)
                        print(f"{Fore.GREEN}✅ Canal encontrado: {chat.title}{Style.RESET_ALL}")
                        return new_id
                    except:
                        pass
            
            print(f"{Fore.RED}❌ Erro ao acessar o canal: {str(e)}{Style.RESET_ALL}")
            logger.error(f"Erro ao acessar o canal: {str(e)}")
            
            if "CHANNEL_PRIVATE" in str(e):
                print(f"{Fore.RED}❌ O canal é privado e o usuário não tem acesso.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⚠️ Verifique se sua conta é membro do canal e tem permissões para postar.{Style.RESET_ALL}")
            elif "PEER_ID_INVALID" in str(e):
                print(f"{Fore.RED}❌ ID do canal inválido ou o usuário não é membro do canal.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⚠️ Você deve ser membro do canal para enviar mensagens para ele.{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}⚠️ Verifique se o ID está correto e tente novamente.{Style.RESET_ALL}")
            
            return None
    except Exception as e:
        print(f"{Fore.RED}❌ Erro ao verificar o canal: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Erro ao verificar o canal: {str(e)}")
        return None

def upload_file(app, file_path, channel_id):
    """
    Faz upload de um arquivo para o canal do Telegram.
    
    Args:
        app: Cliente Pyrogram
        file_path (str): Caminho do arquivo a ser enviado
        channel_id (str): ID do canal de destino
    """
    # Limpar a tela para melhor visualização
    clear_screen()
    
    try:
        # Função de progresso interna que tem acesso à variável progress_bar
        def progress(current, total, progress_bar):
            if total > 0:
                percentage = current * 100 / total
                speed = current / 1048576 if progress_bar.n == 0 else (current - progress_bar.n) / 1048576
                progress_bar.set_postfix(
                    {"Progresso": f"{percentage:.1f}%", "Velocidade": f"{speed:.2f} MB/s"}
                )
            progress_bar.update(current - progress_bar.n)
            
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}📤 Iniciando upload de {Fore.WHITE}{file_name}{Fore.YELLOW} ({format_size(file_size)}){Style.RESET_ALL}")
        logger.info(f"Iniciando upload de {file_name} ({format_size(file_size)})")
        
        # Verificar tipo de arquivo
        if file_path.lower().endswith(('.jpg', '.jpeg', '.png')):
            caption = read_caption()
            with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024, 
                     desc=f"{Fore.CYAN}Enviando imagem{Fore.RESET}", 
                     bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as progress_bar:
                app.send_photo(
                    channel_id, 
                    file_path, 
                    caption=caption, 
                    progress=lambda current, total: progress(current, total, progress_bar)
                )
        elif file_path.lower().endswith('.webp'):
            print(f"{Fore.CYAN}Enviando sticker...{Style.RESET_ALL}")
            app.send_sticker(channel_id, file_path)
        else:
            with tqdm(total=file_size, unit='B', unit_scale=True, unit_divisor=1024,
                     desc=f"{Fore.CYAN}Enviando arquivo{Fore.RESET}",
                     bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as progress_bar:
                app.send_document(
                    channel_id, 
                    file_path, 
                    progress=lambda current, total: progress(current, total, progress_bar),
                    force_document=True,
                    file_name=os.path.basename(file_path)  # Garantir que o nome do arquivo seja preservado
                )
                
        print(f"{Fore.GREEN}{Style.BRIGHT}✅ Upload de {file_name} concluído com sucesso!{Style.RESET_ALL}")
        logger.info(f"Upload de {file_name} concluído com sucesso!")
        # Pequena pausa para evitar limites de rate - reduzida para 0.5 segundos para arquivos menores
        time.sleep(0.5 if file_size < 10 * 1024 * 1024 else 1)
        return True
    except errors.FloodWait as e:
        print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ Limite de envio atingido. Aguardando {e.x} segundos...{Style.RESET_ALL}")
        logger.warning(f"Limite de envio atingido. Aguardando {e.x} segundos...")
        time.sleep(e.x)
        return upload_file(app, file_path, channel_id)  # Tentar novamente após espera
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}❌ Erro ao enviar {os.path.basename(file_path)}: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Erro ao enviar {os.path.basename(file_path)}: {str(e)}")
        return False

def format_size(size_bytes):
    """Formata bytes para uma representação legível."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 ** 2:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 ** 3:
        return f"{size_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_bytes / (1024 ** 3):.2f} GB"

def check_folders_content(input_folder, output_folder):
    """
    Verifica o conteúdo das pastas input e output.
    
    Args:
        input_folder (str): Caminho da pasta de entrada
        output_folder (str): Caminho da pasta de saída
        
    Returns:
        tuple: (input_has_content, output_has_content, output_folders)
    """
    # Verificar se há pastas para processar em input
    input_has_content = False
    for item in os.listdir(input_folder):
        if os.path.isdir(os.path.join(input_folder, item)):
            input_has_content = True
            break
    
    # Verificar se há pastas com conteúdo em output
    output_folders = []
    for item in os.listdir(output_folder):
        folder_path = os.path.join(output_folder, item)
        if os.path.isdir(folder_path):
            # Verificar se a pasta tem arquivos zip
            has_zips = any(file.endswith('.zip') for file in os.listdir(folder_path))
            if has_zips:
                output_folders.append(item)
    
    return input_has_content, len(output_folders) > 0, output_folders

def main():
    """Função principal do programa."""
    try:
        print_colored_step("1", "Carregando configuração")
        # Carregar configuração
        config = load_config()
        max_size_mb = config['max_size_mb']
        threads = config['threads']
        compression_level = config.get('compression_level', 0)
        max_concurrent = config.get('max_concurrent_transmissions', 2)
            
        print_colored_step("2", "Verificando pastas necessárias")
        # Verificar pastas necessárias
        verify_folders()
        
        # Definir caminhos
        input_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input")
        output_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")  
        
        # Verificar conteúdo das pastas input e output
        input_has_content, output_has_content, output_folders = check_folders_content(input_folder, output_folder)
        
        # Decidir o fluxo de execução com base no conteúdo das pastas
        if not input_has_content and not output_has_content:
            # Nem input nem output têm conteúdo
            logger.warning("Pasta input/ está vazia e não há arquivos processados em output/. Adicione arquivos para enviar.")
            print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ A pasta input/ está vazia e não há arquivos processados em output/. Adicione arquivos para enviar.{Style.RESET_ALL}")
            sys.exit(0)
        
        # Iniciar processamento se houver conteúdo em input
        if input_has_content:
            print_colored_step("3", "Processando arquivos de input/")
            process_folder(input_folder, output_folder, max_size_mb * (1024 ** 2), threads, compression_level)
        else:
            print(f"{Fore.CYAN}ℹ️ Pasta input/ está vazia. Pulando etapa de processamento.{Style.RESET_ALL}")
            logger.info("Pasta input/ está vazia. Pulando etapa de processamento.")
        
        # Verificar novamente o conteúdo de output após processamento (se necessário)
        if not output_has_content:
            _, output_has_content, output_folders = check_folders_content(input_folder, output_folder)
            
            # Se ainda não houver conteúdo em output
            if not output_has_content:
                logger.warning("Não há arquivos processados para enviar na pasta output/.")
                print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ Não há arquivos processados para enviar na pasta output/.{Style.RESET_ALL}")
                sys.exit(0)
        
        print_colored_step("4", "Iniciando cliente do Telegram")
        print(f"{Fore.GREEN}✅ Encontrados {len(output_folders)} pacote(s) para enviar em output/{Style.RESET_ALL}")
        
        # Iniciar cliente do Telegram
        try:
            # Tentar usar API ID e hash do config se estiverem disponíveis
            api_id = config.get('api_id', None)
            api_hash = config.get('api_hash', None)
            
            if api_id and api_hash:
                print(f"{Fore.CYAN}ℹ️ Usando credenciais salvas para iniciar o cliente do Telegram...{Style.RESET_ALL}")
                app = Client(session_name, api_id, api_hash, 
                            max_concurrent_transmissions=max_concurrent,  # Usar valor da configuração
                            sleep_threshold=10)              # Auto-retentar em case de FloodWait < 10s
            else:
                print(f"{Fore.CYAN}ℹ️ Iniciando cliente com sessão existente...{Style.RESET_ALL}")
                app = Client(session_name,
                            max_concurrent_transmissions=max_concurrent,  # Usar valor da configuração
                            sleep_threshold=10)              # Auto-retentar em case de FloodWait < 10s
        except Exception as e:
            logger.error(f"Erro ao iniciar cliente do Telegram: {str(e)}")
            print(f"{Fore.RED}{Style.BRIGHT}❌ Erro ao iniciar cliente do Telegram: {str(e)}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}⚠️ Tente executar o programa novamente para reautenticar.{Style.RESET_ALL}")
            sys.exit(1)
        
        # Upload dos arquivos
        with app:
            # Testar conexão antes de prosseguir
            try:
                me = app.get_me()
                print(f"{Fore.GREEN}✅ Conectado como {me.first_name} (@{me.username}){Style.RESET_ALL}")
            except Exception as e:
                logger.error(f"Erro ao conectar com o Telegram: {str(e)}")
                print(f"{Fore.RED}{Style.BRIGHT}❌ Erro ao conectar com o Telegram: {str(e)}{Style.RESET_ALL}")
                
                # Remover sessão se estiver inválida
                if os.path.exists(f"{session_name}.session"):
                    os.remove(f"{session_name}.session")
                    print(f"{Fore.YELLOW}⚠️ Sessão removida. Execute o programa novamente para reautenticar.{Style.RESET_ALL}")
                sys.exit(1)
                
            # Permitir ao usuário selecionar um canal
            print_colored_step("5", "Selecionando canal de destino")
            channel_id = select_channel(app, config)
            
            if not channel_id:
                print(f"{Fore.RED}{Style.BRIGHT}❌ Nenhum canal foi selecionado. Operação cancelada.{Style.RESET_ALL}")
                sys.exit(1)
                
            logger.info(f"Iniciando envio para o canal {channel_id}")
            print(f"\n{Fore.CYAN}{Style.BRIGHT}📢 Iniciando envio para o canal {channel_id}{Style.RESET_ALL}\n")
            
            # Obter lista de pastas a processar
            folders_to_process = [f for f in sorted(os.listdir(output_folder)) if os.path.isdir(os.path.join(output_folder, f))]
            total_folders = len(folders_to_process)
            
            if total_folders == 0:
                print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ Nenhuma pasta para processar na pasta output/{Style.RESET_ALL}")
                return
            
            print(f"{Fore.GREEN}Encontradas {total_folders} pasta(s) para processar{Style.RESET_ALL}")
            
            for folder_index, folder_name in enumerate(folders_to_process, 1):
                folder_path = os.path.join(output_folder, folder_name)
                if not os.path.isdir(folder_path):
                    continue
                    
                print(f"\n{Fore.GREEN}{Style.BRIGHT}📁 Processando pasta {folder_index}/{total_folders}: {folder_name}{Style.RESET_ALL}")
                    
                # Timestamp para cada pasta
                timestamp = datetime.now().strftime("%d/%m/%Y %H:%M")
                app.send_message(channel_id, f"📁 **{folder_name}**\n📅 {timestamp}")
                
                # Enviar capa primeiro, se existir
                has_cover = False
                for cover_name in ['cover.jpg', 'cover.png']:
                    cover_path = os.path.join(folder_path, cover_name)
                    if os.path.exists(cover_path):
                        print(f"{Fore.CYAN}🖼️ Enviando capa: {cover_name}{Style.RESET_ALL}")
                        upload_file(app, cover_path, channel_id)
                        has_cover = True
                        break
                
                if not has_cover:
                    print(f"{Fore.YELLOW}ℹ️ Nenhuma capa encontrada para esta pasta{Style.RESET_ALL}")
                
                # Enviar arquivos ZIP
                zip_files = [f for f in sorted(os.listdir(folder_path)) if f.endswith('.zip')]
                total_parts = len(zip_files)
                
                if total_parts > 0:
                    print(f"\n{Fore.CYAN}{Style.BRIGHT}📦 Enviando {folder_name} ({total_parts} partes){Style.RESET_ALL}\n")
                    
                    with tqdm(total=total_parts, desc=f"{Fore.BLUE}Progresso total{Fore.RESET}", 
                             bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]") as total_progress:
                        for i, zip_file in enumerate(zip_files, 1):
                            zip_path = os.path.join(folder_path, zip_file)
                            print(f"{Fore.YELLOW}📤 Enviando parte {i}/{total_parts}: {zip_file}{Style.RESET_ALL}")
                            success = upload_file(app, zip_path, channel_id)
                            if not success:
                                print(f"{Fore.RED}{Style.BRIGHT}⚠️ Falha ao enviar {zip_file}. Tentando novamente...{Style.RESET_ALL}")
                                # Tentar novamente após uma pausa
                                time.sleep(5)
                                success = upload_file(app, zip_path, channel_id)
                                if not success:
                                    print(f"{Fore.RED}{Style.BRIGHT}❌ Falha ao enviar {zip_file} após segunda tentativa.{Style.RESET_ALL}")
                            total_progress.update(1)
                
                # Enviar sticker (se existir)
                sticker_path = 'sticker.webp'
                if os.path.exists(sticker_path):
                    print(f"{Fore.CYAN}🏷️ Enviando sticker{Style.RESET_ALL}")
                    upload_file(app, sticker_path, channel_id)
                    
                print(f"{Fore.GREEN}{Style.BRIGHT}✅ Pasta {folder_name} enviada com sucesso!{Style.RESET_ALL}\n")
                
            print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 Todos os arquivos foram enviados com sucesso!{Style.RESET_ALL}")
            logger.info("Processamento finalizado com sucesso")
                
    except Exception as e:
        logger.error(f"Erro no programa principal: {str(e)}")
        print(f"{Fore.RED}{Style.BRIGHT}❌ Ocorreu um erro: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    show_banner()
    authenticate()
    main()