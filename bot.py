import telebot
from telebot import types
import os
import time

# Reemplaza con tu token de bot
TOKEN = '7342680297:AAFhPjtIVsYn8f7hISqSuUZWoK5gYelzbrA'
bot = telebot.TeleBot(TOKEN)

# Lista de archivos de texto
DIRECTORY = ['ar-full-teleconsultado-PantherSearchBot-part6.txt'] 

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
    filename = 'search_results.txt'
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

    print(f"el usuario {user_id} ha solicitado una URL: {url}")

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
            time.sleep(5)  # Espera de 5 segundos

            if global_filename:
                # Enviar el archivo
                with open(global_filename, 'rb') as file:
                    bot.send_document(call.message.chat.id, file, caption="✅ Archivo Entregado | @Fiscalizacion")
                    print(f"el usuario {user_id} ha descargado un archivo")

                # Eliminar el archivo después de enviarlo
                os.remove(global_filename)
                global_filename = None  # Limpiar la variable global

                # Restar un token
                tokens[user_id] -= 1
                bot.reply_to(call.message, f"📉 Busquedas Disponibles: {tokens.get(user_id, 0)}.")
            else:
                bot.reply_to(call.message, "❗ No se encontró el archivo de resultados.")
        else:
            bot.reply_to(call.message, "❗ No tienes suficientes tokens para descargar el archivo. Para comprar más, contacta a @teleconsultado")

    elif call.data == "no_download":
        bot.reply_to(call.message, 'No descargaste el archivo.')
        if global_filename and os.path.exists(global_filename):
            # Elimina el archivo solo si existe
            os.remove(global_filename)
            global_filename = None  # Limpiar la variable global

    # Editar el mensaje original para eliminar el teclado
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)

# Manejar los callbacks de los botones en línea
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    handle_download_choice(call)

# Comando /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Bienvenido al bot! Usa /url [URL] para buscar en los archivos.")
    print("ejecutaron /start")

# Comando /tokens
@bot.message_handler(commands=['tokens'])
def handle_tokens(message):
    user_id = message.from_user.id
    user_tokens = tokens.get(user_id, 0)
    print(f"el usuario {user_id} ha solicitado ver sus tokens")
    bot.reply_to(message, f"📊 Busquedas Disponibles: {user_tokens}")

# Comando /whitelist (solo para el administrador)
@bot.message_handler(commands=['whitelist'])
def handle_whitelist(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❗ Solo el administrador puede usar este comando.")
        return

    if not tokens:
        bot.reply_to(message, "La lista de tokens está vacía.")
        return

    whitelist_message = "📝 Lista de usuarios y sus tokens:\n\n"
    for user_id, token_count in tokens.items():
        user = bot.get_chat_member(message.chat.id, user_id)
        username = user.user.username if user.user.username else "No disponible"
        whitelist_message += f"ID: {user_id}, Usuario: @{username}, Tokens: {token_count}\n"

    bot.reply_to(message, whitelist_message)

# Comando /add (solo para el administrador)
@bot.message_handler(commands=['add'])
def handle_add(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❗ Solo el administrador puede usar este comando.")
        return

    args = message.text.split()
    if len(args) != 3:
        bot.reply_to(message, 'Uso: /add [ID] [NUMERO_DE_TOKENS]')
        return

    user_id = int(args[1])

    print(f"el usuario {user_id} ha solicitado agregar tokens")
    try:
        num_tokens = int(args[2])
    except ValueError:
        bot.reply_to(message, 'El número de tokens debe ser un número entero.')
        return

    if user_id in tokens:
        tokens[user_id] += num_tokens
    else:
        tokens[user_id] = num_tokens

    bot.reply_to(message, f"Tokens añadidos: {num_tokens} tokens para el usuario ID {user_id}")
    print(f"se agrego {num_tokens} tokens al usuario {user_id}")

# Comando /delwhitelist (solo para el administrador)
@bot.message_handler(commands=['delwhitelist'])
def handle_delwhitelist(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❗ Solo el administrador puede usar este comando.")
        return

    args = message.text.split()
    if len(args) != 2:
        bot.reply_to(message, 'Uso: /delwhitelist [ID]')
        return

    user_id = int(args[1])
    if user_id in tokens:
        del tokens[user_id]
        bot.reply_to(message, f"Usuario con ID {user_id} eliminado de la whitelist.")
    else:
        bot.reply_to(message, f"No se encontró al usuario con ID {user_id} en la whitelist.")

# Ejecutar el bot
bot.polling()
