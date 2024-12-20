import logging
import requests
import os
import subprocess
import json
import sys
from concurrent.futures import ThreadPoolExecutor

CLIENT_DIRECTORY = os.path.join(os.getenv("APPDATA"), "genesisproject-client")
FILE_LIST_URL = "https://genesisproj.online/downloads/genesisproject-client/file_list.json"
LOCAL_FILE_LIST_SCRIPT = os.path.join(os.path.dirname(__file__), "local_file_list.py")  # Nome do script para gerar o local_file_list.json
LOCAL_FILE_LIST_PATH = os.path.join(os.path.dirname(__file__), "local_file_list.json")

# Configuração do logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def resource_path(relative_path):
    """Obter o caminho absoluto para recursos, funciona para dev e para PyInstaller."""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def fetch_server_file_list():
    """Baixa e retorna a lista de arquivos do servidor."""
    try:
        logging.info("Baixando file_list.json do servidor...")
        response = requests.get(FILE_LIST_URL)
        response.raise_for_status()
        logging.info("Lista de arquivos baixada com sucesso.")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao baixar file_list.json: {e}")
        return None
    
def generate_local_file_list():
    try:
        logging.info("Gerando local_file_list.json...")
        os.makedirs(CLIENT_DIRECTORY, exist_ok=True)
        subprocess.run(["python", resource_path(LOCAL_FILE_LIST_SCRIPT)], check=True)
        if os.path.exists(resource_path(LOCAL_FILE_LIST_PATH)):
            logging.info(f"Arquivo gerado em {LOCAL_FILE_LIST_PATH}")
        else:
            logging.error(f"Arquivo não encontrado em {LOCAL_FILE_LIST_PATH}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Erro ao executar o script para gerar local_file_list.json: {e}")
        raise
    except FileNotFoundError:
        logging.error(f"Script {LOCAL_FILE_LIST_SCRIPT} não encontrado.")
        raise

def read_local_file_list():
    """Lê e retorna a lista de arquivos locais."""
    if os.path.exists(resource_path(LOCAL_FILE_LIST_PATH)):
        try:
            with open(resource_path(LOCAL_FILE_LIST_PATH), 'r') as file:
                data = file.read()
                if data.strip():  # Verifica se o arquivo não está vazio
                    logging.info("local_file_list.json lido com sucesso.")
                    return json.loads(data)  # Certifique-se de retornar como dicionário
                else:
                    logging.warning("local_file_list.json está vazio.")
        except json.JSONDecodeError as e:
            logging.error(f"Erro ao decodificar JSON: {e}")
        except Exception as e:
            logging.error(f"Erro ao ler local_file_list.json: {e}")
    else:
        logging.warning(f"local_file_list.json não encontrado em {LOCAL_FILE_LIST_PATH}")
    return {}  # Retorna um dicionário vazio se o arquivo não existir ou estiver vazio

def check_for_updates(server_file_list, local_file_list):
    """Compara os arquivos locais com os do servidor e retorna os arquivos que precisam de atualização."""
    files_to_update = []
    for file_info in server_file_list.values():
        server_file_path = file_info['path'].replace("\\", "/")
        server_file_hash = file_info['hash']
        local_hash = local_file_list.get(file_info['path'], {}).get("hash")

        if local_hash != server_file_hash:
            files_to_update.append((server_file_path, server_file_hash))

    return files_to_update

def download_file(file_path, progress_callback=None):
    """Baixa um único arquivo."""
    download_url = f"https://genesisproj.online/downloads/genesisproject-client/{file_path}"
    local_file_path = os.path.join(CLIENT_DIRECTORY, file_path)
    try:
        logging.info(f"Baixando {file_path}...")
        with requests.get(download_url, stream=True) as response:
            response.raise_for_status()
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            with open(local_file_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=20*1024*1024):  # Aumentar o tamanho do chunk para 1MB
                    file.write(chunk)
        logging.info(f"Arquivo {file_path} atualizado com sucesso.")
        if progress_callback:
            progress_callback()
    except requests.exceptions.RequestException as e:
        logging.error(f"Erro ao baixar {file_path}: {e}")

def download_files(files_to_update, progress_callback=None):
    """Baixa os arquivos que precisam de atualização."""
    total_files = len(files_to_update)
    progress = [0]

    def update_progress():
        progress[0] += 1
        if progress_callback:
            progress_callback(progress[0], total_files)

    with ThreadPoolExecutor(max_workers=8) as executor:  # Usar 4 threads para download paralelo
        futures = [executor.submit(download_file, file_path, update_progress) for file_path, _ in files_to_update]
        for future in futures:
            future.result()

def download_all_files(server_file_list, progress_callback=None):
    """Baixa todos os arquivos do servidor."""
    files_to_update = [(file_info['path'].replace("\\", "/"), file_info['hash']) for file_info in server_file_list.values()]
    download_files(files_to_update, progress_callback)

def update_files():
    """Verifica e realiza atualizações nos arquivos, se necessário."""
    try:
        # Gerar local_file_list.json
        generate_local_file_list()

        # Ler listas do servidor e local
        server_file_list = fetch_server_file_list()
        if not server_file_list:
            logging.info("Não foi possível obter a lista de arquivos do servidor.")
            return False

        local_file_list = read_local_file_list()
        if local_file_list is None:
            logging.error("Não foi possível obter a lista de arquivos locais.")
            return False

        # Verificar atualizações
        if not local_file_list:
            logging.info("Lista de arquivos locais está vazia. Baixando todos os arquivos do servidor.")
            download_all_files(server_file_list)
        else:
            files_to_update = check_for_updates(server_file_list, local_file_list)
            if not files_to_update:
                logging.info("Todos os arquivos estão atualizados. Nenhuma ação necessária.")
                return False

            logging.info(f"Atualizações necessárias para {len(files_to_update)} arquivo(s).")
            download_files(files_to_update)
        
        logging.info("Atualização concluída.")
        return True
    except Exception as e:
        logging.error(f"Erro no processo de atualização: {e}")
        return False