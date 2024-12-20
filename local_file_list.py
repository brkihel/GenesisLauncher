import os
import hashlib
import json

CLIENT_DIRECTORY = os.path.join(os.getenv("APPDATA"), "genesisproject-client")  # Caminho para a pasta do cliente
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "local_file_list.json")  # Caminho para o arquivo JSON de saída

def get_file_hash(file_path):
    """Calcula o hash SHA256 de um arquivo."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
    except FileNotFoundError:
        return None  # Arquivo não existe
    return sha256_hash.hexdigest()

def generate_file_list():
    """Gera um arquivo JSON com todos os arquivos e seus hashes no diretório do cliente."""
    file_list = {}
    for root, dirs, files in os.walk(CLIENT_DIRECTORY):
        for file_name in files:
            file_path = os.path.relpath(os.path.join(root, file_name), CLIENT_DIRECTORY)
            file_hash = get_file_hash(os.path.join(root, file_name))
            if file_hash:
                file_list[file_path] = {
                    "hash": file_hash,
                    "path": file_path
                }

    with open(OUTPUT_FILE, "w") as json_file:
        json.dump(file_list, json_file, indent=4)
    print(f"Arquivo {OUTPUT_FILE} gerado com sucesso!")

if __name__ == "__main__":
    generate_file_list()
