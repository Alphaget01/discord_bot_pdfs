import base64

def convert_json_to_base64(file_path: str) -> str:
    """
    Convierte un archivo JSON a una cadena codificada en Base64.

    :param file_path: Ruta del archivo JSON.
    :return: Cadena codificada en Base64.
    """
    try:
        with open(file_path, 'rb') as json_file:
            # Lee el contenido del archivo JSON en formato binario
            json_data = json_file.read()
        
        # Convierte los datos binarios a Base64
        base64_encoded = base64.b64encode(json_data).decode('utf-8')
        
        print("Archivo convertido exitosamente a Base64:")
        print(base64_encoded)  # Imprime la cadena Base64
        return base64_encoded
    except Exception as e:
        print(f"Error al convertir el archivo a Base64: {str(e)}")
        return None


if __name__ == "__main__":
    # Cambia esta ruta al archivo de tu service_account.json
    file_path = "data/service_account.json"
    
    base64_string = convert_json_to_base64(file_path)
    
    if base64_string:
        # Guarda la cadena Base64 en un archivo para reutilizarla o copiarla
        with open("data/service_account_base64.txt", "w") as output_file:
            output_file.write(base64_string)
        print("La cadena Base64 se guardó en 'data/service_account_base64.txt'.")
