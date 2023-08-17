from utils import *

# estructura sugerida por chat gpt


def menu():
    print_cyan("\nXMPP CHAT: Qué desea hacer? (Ingresar número de opción)")
    print_cyan("1. Registrarse")
    print_cyan("2. Iniciar sesión")
    print_cyan("3. Eliminar cuenta")
    print_cyan("4. Salir")


def user_menu():
    print_cyan("\nQué desea hacer? (Ingresar número de opción)")
    print_cyan("1. Mostrar todos los contactos y su estado")
    print_cyan("2. Agregar contacto")
    print_cyan("3. Mostrar detalles de contacto de un usuario")
    print_cyan("4. Comunicacion 1 a 1 con cualquier usuario/contacto")
    print_cyan("5. Participar en conversaciones grupales")
    print_cyan("6. Definir mensaje de presencia (status)")
    print_cyan("7. Enviar archivos")
    print_cyan("8. Desconectarse")


def group_chat():

    print_magenta("\nQué desea hacer? (Ingresar número de opción)")
    print_magenta("1) Crear una sala de chat")
    print_magenta("2) Unirse a una sala de chat existente")
    print_magenta("3) Mostrar todas las salas de chat existentes")
    print_magenta("4) Regresar")


def menu_status():
    print_magenta("\nQué desea hacer? (Ingresar número de opción)")
    print_magenta("1) Disponible")
    print_magenta("2) Ausente")
    print_magenta("3) Ocupado")
    print_magenta("4) No molestar")
