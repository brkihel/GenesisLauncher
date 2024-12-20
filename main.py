from gui import create_gui
import logging

def main():
    """Ponto de entrada do launcher."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    logging.info("Iniciando o launcher...")
    
    # Iniciar a interface gráfica
    create_gui()

if __name__ == "__main__":
    main()