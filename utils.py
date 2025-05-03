import os
from colorama import Fore, Back, Style, init
import pyfiglet
import random
from pyrogram import Client
from unidecode import unidecode
import json
import sys

# Inicializar o colorama para funcionar corretamente em qualquer plataforma
init(autoreset=True)

session_name = 'user'

def authenticate():
    """
    Autentica o usuário usando a API do Telegram.
    Verifica se já existe uma sessão ou solicita credenciais.
    """
    def get_credentials():
        try:
            print(f"{Fore.CYAN}{Style.BRIGHT}===== Autenticação do Telegram =====")
            api_id = input(f"{Fore.YELLOW}Digite seu API ID: {Style.RESET_ALL}")
            api_hash = input(f"{Fore.YELLOW}Digite seu API Hash: {Style.RESET_ALL}")
            
            # Validação básica
            if not api_id.isdigit() or len(api_hash) < 10:
                print(f"{Fore.RED}{Style.BRIGHT}Credenciais inválidas. Por favor, verifique os valores fornecidos.{Style.RESET_ALL}")
                return get_credentials()
                
            return api_id, api_hash
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}Processo de autenticação cancelado pelo usuário.{Style.RESET_ALL}")
            sys.exit(0)

    def test_session_validity():
        """Verifica se a sessão atual é válida tentando uma operação simples"""
        try:
            print(f"{Fore.CYAN}Verificando sessão existente...{Style.RESET_ALL}")
            config = load_config()
            api_id = config.get('api_id', None)
            api_hash = config.get('api_hash', None)
            
            # Se não houver API ID/hash no config, usamos Client sem parâmetros
            # para tentar usar a sessão salva com credenciais armazenadas
            if api_id and api_hash:
                client = Client(session_name, api_id, api_hash)
            else:
                client = Client(session_name)
                
            with client as app:
                me = app.get_me()
                print(f"{Fore.GREEN}{Style.BRIGHT}✅ Sessão válida! {Fore.GREEN}Conectado como {me.first_name} (@{me.username}).{Style.RESET_ALL}")
                return True
        except Exception as e:
            print(f"{Fore.RED}❌ Sessão inválida: {str(e)}{Style.RESET_ALL}")
            if os.path.exists(f"{session_name}.session"):
                os.remove(f"{session_name}.session")
                print(f"{Fore.YELLOW}⚠️ Arquivo de sessão antigo removido.{Style.RESET_ALL}")
            return False

    try:
        # Se a sessão existe, verificar validade
        if os.path.exists(f"{session_name}.session"):
            if test_session_validity():
                return True
            else:
                print(f"{Fore.YELLOW}⚠️ Necessário criar uma nova sessão.{Style.RESET_ALL}")
        
        # Obter novas credenciais
        api_id, api_hash = get_credentials()
        
        print(f"{Fore.CYAN}{Style.BRIGHT}Iniciando autenticação com o Telegram...{Style.RESET_ALL}")
        
        # Criar nova sessão
        try:
            with Client(session_name, api_id, api_hash) as app:
                me = app.get_me()
                print(f"{Fore.GREEN}{Style.BRIGHT}✅ Autenticação bem-sucedida! {Style.RESET_ALL}{Fore.GREEN}Conectado como {me.first_name} (@{me.username}).{Style.RESET_ALL}")
                
                # Salvar API ID e hash no config.json para uso futuro
                config = load_config()
                config['api_id'] = api_id
                config['api_hash'] = api_hash
                with open('config.json', 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4)
                
                return True
        except Exception as e:
            print(f"{Fore.RED}{Style.BRIGHT}❌ Erro durante a autenticação: {str(e)}{Style.RESET_ALL}")
            if "401 UNAUTHORIZED" in str(e) or "SESSION_REVOKED" in str(e):
                print(f"{Fore.RED}⚠️ Credenciais inválidas ou sessão revogada.{Style.RESET_ALL}")
            elif "PHONE_CODE_INVALID" in str(e):
                print(f"{Fore.RED}⚠️ Código de verificação inválido.{Style.RESET_ALL}")
            elif "FLOOD_WAIT" in str(e):
                print(f"{Fore.RED}⚠️ Muitas tentativas. Aguarde um tempo antes de tentar novamente.{Style.RESET_ALL}")
            
            # Limpar sessão inválida
            if os.path.exists(f"{session_name}.session"):
                os.remove(f"{session_name}.session")
            
            print(f"{Fore.YELLOW}ℹ️ Tente novamente mais tarde ou verifique suas credenciais.{Style.RESET_ALL}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}Processo de autenticação cancelado pelo usuário.{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}❌ Erro inesperado: {str(e)}{Style.RESET_ALL}")
        # Remover sessão corrompida
        if os.path.exists(f"{session_name}.session"):
            os.remove(f"{session_name}.session")
        print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ Sessão removida. Por favor, tente novamente.{Style.RESET_ALL}")
        sys.exit(1)

class Banner:
    def __init__(self, banner):
        self.banner = banner
        self.lg = Fore.LIGHTGREEN_EX
        self.w = Fore.WHITE
        self.cy = Fore.CYAN
        self.ye = Fore.YELLOW
        self.r = Fore.RED
        self.n = Fore.RESET

    def print_banner(self):
        colors = [self.lg, self.r, self.w, self.cy, self.ye]
        f = pyfiglet.Figlet(font='slant')
        banner = f.renderText(self.banner)
        print(f'{random.choice(colors)}{banner}{self.n}')
        print(f'{self.r}{Style.BRIGHT}  Version: v 1.1.0 https://github.com/z5ta9b5tbMC5Jr{self.n}\n')

def show_banner():
    banner = Banner('ZipFileSender')
    banner.print_banner()

def load_config():
    """
    Carrega a configuração do arquivo config.json.
    Se não existir, cria um arquivo de configuração padrão.
    """
    config_file = 'config.json'
    default_config = {
        "channel_id": "",
        "max_size_mb": 1900,
        "threads": 4,
        "compression_level": 0,
        "delete_after_upload": True,
        "max_concurrent_transmissions": 2  # Número máximo de uploads concorrentes
    }
    
    try:
        if not os.path.exists(config_file):
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4)
            print(f"{Fore.YELLOW}{Style.BRIGHT}Arquivo de configuração criado. Por favor, edite {config_file}.{Style.RESET_ALL}")
            return default_config
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
            
        # Verificar se todos os campos necessários existem
        for key in default_config:
            if key not in config:
                config[key] = default_config[key]
                
        # Atualizar o arquivo se foram adicionados campos padrão
        if len(config) != len(default_config):
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4)
                
        return config
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}Erro ao carregar configuração: {str(e)}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}Usando configuração padrão.{Style.RESET_ALL}")
        return default_config

def verify_folders():
    """
    Verifica e cria as pastas necessárias para o funcionamento do programa.
    """
    folders = ['input', 'output']
    for folder in folders:
        if not os.path.exists(folder):
            os.makedirs(folder)
            print(f"{Fore.GREEN}{Style.BRIGHT}Pasta {folder}/ criada com sucesso!{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}Pasta {folder}/ verificada.{Style.RESET_ALL}")

def print_colored_step(step, message):
    """
    Imprime uma mensagem formatada como passo em cores.
    """
    print(f"{Fore.BLUE}{Style.BRIGHT}[{step}] {Fore.CYAN}{message}{Style.RESET_ALL}")