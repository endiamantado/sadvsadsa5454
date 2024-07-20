import telebot
from telebot import types
import os
import time
from flask import Flask, request
import urllib3

# Reemplaza con tu token de bot
TOKEN = '7342680297:AAFhPjtIVsYn8f7hISqSuUZWoK5gYelzbrA'  # Usa variables de entorno para el token
bot = telebot.TeleBot(TOKEN)

# URL del webhook
WEBHOOK_URL = "https://loginfinder.onrender.com/"  # Ajusta según tu configuración
PORT = int(os.environ.get('PORT', 5000))

# FLASK
server = Flask(__name__)

# Lista de archivos de texto
DIRECTORY = [
    'ar-full-teleconsultado-PantherSearchBot-part1.txt', 
    'ar-full-teleconsultado-PantherSearchBot-part2.txt', 
    'ar-full-teleconsultado-PantherSearchBot-part3.txt', 
    'ar-full-teleconsultado-PantherSearchBot-part4.txt', 
    'ar-full-teleconsultado-PantherSearchBot-part5.txt', 
    'ar-full-teleconsultado-PantherSearchBot-part6.txt', 
    'cup pami-full-teleconsultado-PantherSearchBot-part1.txt', 
    'gob ar-full-teleconsultado-PantherSearchBot-part1.txt', 
    'gov ar-full-teleconsultado-PantherSearchBot-part1.txt'
]

# Variable global para almacenar los resultados encontrados
global_results = []
global_filename = None  # Variable global para el nombre del archivo

# Diccionario para almacenar tokens por usuario
tokens = {}

# ID del administrador
ADMIN_ID = 7221787019  # Cambia esto por tu ID de usuario

def extract_details(text):
    """Extrae los detalles de la URL del texto."""
    details = {}
    lines = text.strip().split('\n')
    for line in lines:
        if line.startswith('URL:'):
            details['URL'] = line[len('URL: '):]
        elif line.startswith('USERNAME:'):
            details['USERNAME'] = line[len('USERNAME: '):]
        elif line.startswith('PASSWORD:'):
            details['PASSWORD'] = line[len('PASSWORD: '):]
        elif line.startswith('DateAdded:'):
            details['DateAdded'] = line[len('DateAdded: '):]
    return details

def create_results_file(results):
    """Crea un archivo de texto con los resultados y devuelve la ruta."""
    filename = f'search_results_{int(time.time())}.txt'
    with open(filename, 'w') as file:
        for entry in results:
            details = extract_details(entry)
            file.write(f"URL: {details.get('URL', 'No disponible')}\n"
                       f"USERNAME: {details.get('USERNAME', 'No disponible')}\n"
                       f"PASSWORD: {details.get('PASSWORD', 'No disponible')}\n"
                       f"DateAdded: {details.get('DateAdded', 'No disponible')}\n\n")
    return filename

@bot.message_handler(commands=['url'])
def handle_url_command(message):
    user_id = message.from_user.id

    # Verificar si el usuario tiene tokens disponibles
    if tokens.get(user_id, 0) <= 0:
        bot.reply_to(message, "❗ No tienes tokens disponibles. Por favor, adquiere más tokens para usar este comando.")
        return

    args = message.text.split(' ', 1)
    if len(args) != 2:
        bot.reply_to(message, 'Uso: /url [URL]')
        return

    url = args[1]

    print(f"El usuario {user_id} ha solicitado una URL: {url}")

    # Verificar que el URL tenga al menos 3 caracteres y no contenga la palabra "https"
    if len(url) < 3:
        bot.reply_to(message, 'El URL debe tener al menos 3 caracteres.')
        return
    if 'https' in url.lower():
        bot.reply_to(message, 'El URL no puede contener la palabra "https".')
        return
    if 'http' in url.lower():
        bot.reply_to(message, 'El URL no puede contener la palabra "http".')
        return

    bot.reply_to(message, '[ 🔍 ] Iniciando búsqueda, esto puede tardar...')
    time.sleep(5)

    global global_results  # Usa la variable global
    global_results = []

    try:
        # Leer y buscar en todos los archivos en la lista
        for file_name in DIRECTORY:
            if os.path.isfile(file_name):
                try:
                    with open(file_name, 'r') as file:
                        content = file.read()
                        entries = content.split('\n\n')  # Suponiendo que las entradas están separadas por líneas en blanco
                        global_results.extend([entry for entry in entries if url in entry])  # Guarda los resultados encontrados
                except FileNotFoundError:
                    bot.reply_to(message, f'Archivo no encontrado: {file_name}')
                    return

        if global_results:
            # Mostrar solo los primeros 3 resultados
            results_to_show = global_results[:3]

            response = ''
            for entry in results_to_show:
                details = extract_details(entry)
                response += (f"<b>› URL:</b> <code>{details.get('URL', 'No disponible')}</code>\n"
                             f"<b>› USERNAME:</b> <code>{details.get('USERNAME', 'No disponible')}</code>\n"
                             f"<b>› PASSWORD:</b> <code>{details.get('PASSWORD', 'No disponible')}</code>\n"
                             f"<b>› DATE ADDED:</b> <code>{details.get('DateAdded', 'No disponible')}</code>\n\n")

            # Eliminar el último '\n\n' para una mejor presentación
            response = response.strip()

            # Crear el archivo con los resultados
            global global_filename
            global_filename = create_results_file(global_results)

            # Contar el total de resultados en el archivo generado
            total_results = len(global_results)

            # Enviar los resultados encontrados primero
            bot.send_message(message.chat.id, f'<b>Total de Resultados Encontrados:</b> <code>{total_results}</code> \n\n' + response, parse_mode='HTML')

            # Preguntar si el usuario desea descargar el archivo
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("Sí", callback_data="download_all"))
            markup.add(types.InlineKeyboardButton("No", callback_data="no_download"))

            # Enviar el mensaje con la pregunta y el teclado debajo
            bot.send_message(message.chat.id, f'<b>¿Desea descargar los resultados?</b> <i>Total de resultados encontrados: {total_results}</i>', reply_markup=markup, parse_mode='HTML')

        else:
            bot.reply_to(message, 'No se encontró la URL en los archivos.')

    except Exception as e:
        bot.reply_to(message, f'Error inesperado: {e}')

def handle_download_choice(call):
    global global_filename  # Usa la variable global
    user_id = call.from_user.id

    if call.data == "download_all":
        # Verificar si el usuario tiene tokens disponibles
        if tokens.get(user_id, 0) > 0:
            # Enviar el mensaje de "Archivo enviándose"
            bot.reply_to(call.message, '<b>El archivo se está enviando, por favor espere!</b>', parse_mode='HTML')

            # Esperar un momento antes de enviar el archivo
            time.sleep(1)

            # Enviar el archivo generado
            with open(global_filename, 'rb') as file:
                bot.send_document(call.message.chat.id, file)

            # Eliminar el archivo después de enviarlo
            os.remove(global_filename)

            # Actualizar la cantidad de tokens disponibles
            tokens[user_id] = tokens.get(user_id, 0) - 1

            # Confirmar la descarga
            bot.reply_to(call.message, '<b>Archivo enviado exitosamente!</b>', parse_mode='HTML')

        else:
            bot.reply_to(call.message, "❗ No tienes tokens disponibles. Por favor, adquiere más tokens para usar esta opción.")

    elif call.data == "no_download":
        bot.reply_to(call.message, '<b>No se ha descargado el archivo.</b>', parse_mode='HTML')



# Manejador de actualizaciones entrantes del bot
@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return "!", 200

# Configurar el webhook
@server.route("/")
def webhook():
    bot.remove_webhook()  # Remove any existing webhook
    bot.set_webhook(url=WEBHOOK_URL)  # Set the new webhook
    return "BOT ENCENDIDO CULIAU", 200

if __name__ == "__main__":
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    server.run(host="0.0.0.0", port=PORT)
