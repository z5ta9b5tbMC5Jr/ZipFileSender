import os
import shutil
import zipfile
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor
from halo import Halo
import logging
import sys
from colorama import Fore, Back, Style

logger = logging.getLogger("ZipFileSender.AutoZip")

def compress_directory(src_dir, zip_name, total_size, zip_folder, compression=zipfile.ZIP_STORED):
    """
    Compacta um diretório em um arquivo ZIP.
    
    Args:
        src_dir (str): Diretório fonte a ser compactado
        zip_name (str): Nome do arquivo ZIP a ser criado
        total_size (int): Tamanho total em bytes dos arquivos a serem compactados
        zip_folder (str): Pasta onde será salvo o arquivo ZIP
        compression (int): Método de compressão (padrão: ZIP_STORED)
    """
    zip_file_path = os.path.join(zip_folder, zip_name)
    try:
        with zipfile.ZipFile(zip_file_path, 'w', compression) as zipf:
            with tqdm(total=total_size, desc=f"{Fore.MAGENTA}Compactando {zip_name}{Fore.RESET}", 
                     unit="B", unit_scale=True, unit_divisor=1024,
                     bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as pbar:
                for root, _, files in os.walk(src_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            file_size = os.path.getsize(file_path)
                            arcname = os.path.relpath(file_path, src_dir)
                            zipf.write(file_path, arcname)
                            pbar.update(file_size)
                        except Exception as e:
                            logger.error(f"Erro ao adicionar arquivo {file_path} ao ZIP: {str(e)}")
                            continue
        
        print(f"{Fore.GREEN}{Style.BRIGHT}✅ Arquivo {zip_name} criado com sucesso!{Style.RESET_ALL}")
        logger.info(f"Arquivo {zip_name} criado com sucesso.")
        return True
    except Exception as e:
        print(f"{Fore.RED}{Style.BRIGHT}❌ Erro ao compactar diretório {src_dir}: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Erro ao compactar diretório {src_dir}: {str(e)}")
        # Se o arquivo ZIP já foi criado mas está corrompido, remova-o
        if os.path.exists(zip_file_path):
            os.remove(zip_file_path)
        return False

def create_subfolders(files, max_size):
    """
    Divide os arquivos em subpastas com base no tamanho máximo.
    
    Args:
        files (dict): Dicionário de arquivos e seus tamanhos
        max_size (int): Tamanho máximo em bytes para cada subpasta
        
    Returns:
        list: Lista de listas de arquivos, cada lista representa uma subpasta
    """
    subfolders = []
    current_subfolder = []
    current_size = 0
    
    print(f"{Fore.CYAN}{Style.BRIGHT}📊 Organizando {len(files)} arquivos em partes...{Style.RESET_ALL}")
    
    # Ordenar arquivos por tamanho (do maior para o menor)
    for file, size in sorted(files.items(), key=lambda item: -item[1]):
        # Se o arquivo for maior que o tamanho máximo permitido, pule-o
        if size > max_size:
            print(f"{Fore.YELLOW}⚠️ Arquivo {Fore.WHITE}{os.path.basename(file)}{Fore.YELLOW} ({size/(1024**2):.2f} MB) é maior que o tamanho máximo permitido ({max_size/(1024**2):.2f} MB). Será compactado separadamente.{Style.RESET_ALL}")
            logger.warning(f"Arquivo {os.path.basename(file)} ({size/(1024**2):.2f} MB) é maior que o tamanho máximo permitido ({max_size/(1024**2):.2f} MB). Será compactado separadamente.")
            subfolders.append([file])
            continue
            
        # Se adicionar este arquivo fizer a pasta atual exceder o tamanho máximo,
        # comece uma nova pasta
        if current_size + size > max_size:
            if current_subfolder:
                subfolders.append(current_subfolder)
                current_subfolder = []
                current_size = 0
                
        current_subfolder.append(file)
        current_size += size
        
    # Adicione a última pasta se ela não estiver vazia
    if current_subfolder:
        subfolders.append(current_subfolder)
        
    print(f"{Fore.GREEN}Arquivos organizados em {len(subfolders)} partes.{Style.RESET_ALL}")
    return subfolders

def generate_zip_name(base_name, index):
    """
    Gera um nome para o arquivo ZIP com base no nome da pasta e no índice.
    
    Args:
        base_name (str): Nome base (nome da pasta)
        index (int): Índice da parte
        
    Returns:
        str: Nome do arquivo ZIP
    """
    return f"{base_name}_parte_{index:02}.zip"

def process_folder(input_folder, output_folder, max_size_per_zip, threads=4, compression_level=0):
    """
    Processa as pastas de entrada, dividindo arquivos e criando ZIPs.
    
    Args:
        input_folder (str): Pasta de entrada contendo os diretórios a serem processados
        output_folder (str): Pasta de saída onde serão salvos os ZIPs
        max_size_per_zip (int): Tamanho máximo em bytes para cada ZIP
        threads (int): Número de threads para compressão paralela
        compression_level (int): Nível de compressão (0=nenhuma, 9=máxima)
    """
    if not os.path.isdir(input_folder):
        error_msg = f"O caminho especificado não é um diretório: {input_folder}"
        logger.error(error_msg)
        print(f"{Fore.RED}{Style.BRIGHT}❌ {error_msg}{Style.RESET_ALL}")
        raise ValueError(error_msg)
        
    # Selecionar método de compressão baseado no nível
    if compression_level == 0:
        compression = zipfile.ZIP_STORED
        print(f"{Fore.BLUE}ℹ️ Usando modo sem compressão (mais rápido){Style.RESET_ALL}")
    else:
        compression = zipfile.ZIP_DEFLATED
        print(f"{Fore.BLUE}ℹ️ Usando modo comprimido (nível {compression_level}){Style.RESET_ALL}")
        
    # Criar pasta de saída se não existir
    os.makedirs(output_folder, exist_ok=True)
    
    # Lista de pastas para processar
    folders_to_process = []
    for folder in os.listdir(input_folder):
        folder_path = os.path.join(input_folder, folder)
        if os.path.isdir(folder_path):
            folders_to_process.append(folder_path)
            
    if not folders_to_process:
        logger.warning(f"Nenhuma pasta encontrada em {input_folder}")
        print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ Nenhuma pasta encontrada em {input_folder}{Style.RESET_ALL}")
        return
        
    print(f"{Fore.CYAN}{Style.BRIGHT}🔍 Encontradas {len(folders_to_process)} pasta(s) para processar{Style.RESET_ALL}")
    logger.info(f"Processando {len(folders_to_process)} pasta(s)")
    
    # Barra de progresso para processamento de pastas
    with tqdm(total=len(folders_to_process), desc=f"{Fore.BLUE}Processando pastas{Fore.RESET}", 
             bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt}") as folders_progress:
    
        for folder_path in folders_to_process:
            base_folder_name = os.path.basename(folder_path.rstrip("\\/"))
            zip_folder = os.path.join(output_folder, base_folder_name)
            os.makedirs(zip_folder, exist_ok=True)
            
            print(f"\n{Fore.CYAN}{Style.BRIGHT}📁 Processando pasta: {base_folder_name}{Style.RESET_ALL}")
            logger.info(f"Processando pasta: {base_folder_name}")
            
            # Copiar arquivos de capa para a pasta de saída
            has_cover = False
            for cover_name in ['cover.jpg', 'cover.png']:
                cover_path = os.path.join(folder_path, cover_name)
                if os.path.exists(cover_path):
                    try:
                        shutil.copy(cover_path, zip_folder)
                        print(f"{Fore.GREEN}🖼️ Capa {cover_name} copiada para {zip_folder}{Style.RESET_ALL}")
                        logger.info(f"Capa {cover_name} copiada para {zip_folder}")
                        has_cover = True
                    except Exception as e:
                        print(f"{Fore.RED}❌ Erro ao copiar capa {cover_name}: {str(e)}{Style.RESET_ALL}")
                        logger.error(f"Erro ao copiar capa {cover_name}: {str(e)}")
                    break  # Sair do loop após copiar a primeira capa encontrada

            if not has_cover:
                print(f"{Fore.YELLOW}ℹ️ Nenhuma capa encontrada para esta pasta{Style.RESET_ALL}")

            # Processar os arquivos da pasta
            try:
                prepare_files_for_upload(folder_path, threads, zip_folder, max_size_per_zip, compression)
                
                # Após a compactação, remover a pasta original se for bem-sucedido
                shutil.rmtree(folder_path)
                print(f"{Fore.GREEN}{Style.BRIGHT}✅ Pasta {folder_path} removida com sucesso!{Style.RESET_ALL}")
                logger.info(f"Pasta {folder_path} removida com sucesso.")
            except Exception as e:
                print(f"{Fore.RED}{Style.BRIGHT}❌ Erro ao processar pasta {folder_path}: {str(e)}{Style.RESET_ALL}")
                logger.error(f"Erro ao processar pasta {folder_path}: {str(e)}")
                continue
                
            folders_progress.update(1)

def prepare_files_for_upload(folder_path, threads, zip_folder, max_size, compression=zipfile.ZIP_STORED):
    """
    Prepara os arquivos para upload, dividindo em partes e compactando.
    
    Args:
        folder_path (str): Caminho da pasta a ser processada
        threads (int): Número de threads para compressão paralela
        zip_folder (str): Pasta onde serão salvos os ZIPs
        max_size (int): Tamanho máximo em bytes para cada ZIP
        compression (int): Método de compressão
    """
    base_folder_name = os.path.basename(folder_path.rstrip("\\/"))
    
    # Obter lista de arquivos e seus tamanhos
    print(f"{Fore.CYAN}🔍 Escaneando arquivos na pasta {base_folder_name}...{Style.RESET_ALL}")
    
    files = {os.path.join(root, file): os.path.getsize(os.path.join(root, file))
             for root, dirs, files in os.walk(folder_path)
             for file in files}

    if not files:
        logger.warning(f"Não há arquivos a serem zipados na pasta {folder_path}.")
        print(f"{Fore.YELLOW}{Style.BRIGHT}⚠️ Não há arquivos a serem zipados na pasta {folder_path}.{Style.RESET_ALL}")
        return

    total_files = len(files)
    total_size = sum(files.values())
    print(f"{Fore.GREEN}📊 Encontrados {total_files} arquivos ({total_size/(1024**2):.2f} MB){Style.RESET_ALL}")

    spinner = Halo(text=f'{Fore.MAGENTA}Dividindo arquivos em partes...{Fore.RESET}', spinner='dots', color='magenta')
    spinner.start()

    subfolders = []
    temp_folders = []

    try:
        # Criar subpastas baseadas no tamanho máximo
        subfolders = create_subfolders(files, max_size)
        logger.info(f"Pasta {base_folder_name} dividida em {len(subfolders)} parte(s)")
        
        # Criar pastas temporárias e mover arquivos
        print(f"{Fore.CYAN}📋 Preparando {len(subfolders)} parte(s) para compactação...{Style.RESET_ALL}")
        
        for index, subfolder in enumerate(subfolders, start=1):
            temp_folder = os.path.join(zip_folder, f"temp_folder_{index}")
            os.makedirs(temp_folder, exist_ok=True)
            total_size = sum(files[file] for file in subfolder)
            temp_folders.append((temp_folder, total_size))

            # Barra de progresso para cópia de arquivos
            with tqdm(total=len(subfolder), desc=f"{Fore.BLUE}Copiando arquivos (parte {index}){Fore.RESET}", 
                     bar_format="{l_bar}{bar:30}| {n_fmt}/{total_fmt}") as copy_progress:
                for file in subfolder:
                    try:
                        rel_path = os.path.relpath(file, folder_path)
                        dest_path = os.path.join(temp_folder, rel_path)
                        
                        # Criar diretórios de destino se não existirem
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        
                        # Copiar arquivo
                        shutil.copy2(file, dest_path)
                        copy_progress.update(1)
                    except Exception as e:
                        logger.error(f"Erro ao copiar arquivo {file}: {str(e)}")
                        copy_progress.update(1)
                        continue
        
        spinner.stop()
        
        # Compactar cada pasta temporária em um arquivo ZIP
        print(f"{Fore.CYAN}{Style.BRIGHT}📦 Iniciando compactação em {threads} threads...{Style.RESET_ALL}")
        
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = []
            
            for index, (temp_folder, total_size) in enumerate(temp_folders, start=1):
                zip_name = generate_zip_name(base_folder_name, index)
                future = executor.submit(
                    compress_directory, 
                    temp_folder, 
                    zip_name, 
                    total_size, 
                    zip_folder, 
                    compression
                )
                futures.append((future, temp_folder, zip_name))
                
            # Processar resultados e limpar pastas temporárias
            for future, temp_folder, zip_name in futures:
                result = future.result()  # Isso vai esperar a conclusão da tarefa
                if result:
                    logger.info(f"Arquivo {zip_name} criado com sucesso.")
                    try:
                        # Remover pasta temporária após a compactação bem-sucedida
                        shutil.rmtree(temp_folder)
                        logger.info(f"Pasta temporária {temp_folder} removida.")
                    except Exception as e:
                        logger.error(f"Erro ao remover pasta temporária {temp_folder}: {str(e)}")
                else:
                    logger.error(f"Falha ao criar arquivo {zip_name}.")

        print(f"{Fore.GREEN}{Style.BRIGHT}✅ Processamento da pasta {base_folder_name} concluído!{Style.RESET_ALL}")
        return True
        
    except Exception as e:
        spinner.stop()
        print(f"{Fore.RED}{Style.BRIGHT}❌ Erro ao preparar arquivos para upload: {str(e)}{Style.RESET_ALL}")
        logger.error(f"Erro ao preparar arquivos para upload: {str(e)}")
        
        # Limpar pastas temporárias em caso de erro
        for temp_folder, _ in temp_folders:
            try:
                if os.path.exists(temp_folder):
                    shutil.rmtree(temp_folder)
            except:
                pass
        
        return False