import xmpp
import slixmpp
from slixmpp.exceptions import IqError, IqTimeout
from slixmpp.xmlstream.stanzabase import ET
from aioconsole import ainput
from aioconsole.stream import aprint
import asyncio
from asyncio import Future
from typing import Optional, Union
import tkinter as tk
from tkinter import messagebox
import menus
from slixmpp import Message
import base64
import math
import os

# implementacion modifica de registro simple extraido de repositorio https://github.com/xmpppy/xmpppy


def register(client, password):

    jid = xmpp.JID(client)
    account = xmpp.Client(jid.getDomain(), debug=[])
    account.connect()
    return bool(
        xmpp.features.register(account, jid.getDomain(), {
            'username': jid.getNode(),
            'password': password
        }))


class Cliente(slixmpp.ClientXMPP):
    def __init__(self, jid, password):

        super().__init__(jid, password)
        self.name = jid.split('@')[0]
        self.is_connected = False
        self.actual_chat = ''
        self.client_queue = asyncio.Queue()

        # generado por IA
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0199')  # Ping
        self.register_plugin('xep_0045')  # MUC
        self.register_plugin('xep_0085')  # Notifications
        self.register_plugin('xep_0004')  # Data Forms
        self.register_plugin('xep_0060')  # PubSub

        # eventos
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('subscription_request',
                               self.aceptar_subscripcion)
        self.add_event_handler('message', self.chat)
        self.add_event_handler('disco_items', self.salas)
        self.add_event_handler('groupchat_message', self.chat_room)
        self.add_event_handler('ibb_stream_start', self.recibir_archivo)

    # FUNCIONES DE CONTACTOS Y CHATS

    # aceptar mensajes entrantes

    async def aceptar_subscripcion(self, presence):
        if presence['type'] == 'subscribe':
            # aceptar suscriptcion
            try:
                self.send_presence_subscription(
                    pto=presence['from'], ptype='subscribed')
                await self.get_roster()
                print(f"Suscripcion aceptada de {presence['from']}")
            except IqError as e:
                print(
                    f"Error aceptando la suscripcion: {e.iq['error']['text']}")
            except IqTimeout:
                print("Sin respuesta del Servidor.")

    async def chat(self, message):  # mostrar chats
        if message['type'] == 'chat':
            user = str(message['from']).split('@')[0]
            if user == self.actual_chat.split('@')[0]:
                print(f'{user}: {message["body"]}')
            else:
                self.mostrar_notificacion(user)

    def mostrar_notificacion(self, user):  # notificacion de nuevo mensaje
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(
            "Nuevo Mensaje tipo Notificacion", f"Tienes un nuevo mensaje de {user}")
        root.destroy()

    async def enviar_notificacion(self, jid_to_notify, message):
        # Enviar un mensaje de chat como notificación
        self.send_message(mto=jid_to_notify, mbody=message, mtype='chat')
        print(f"Notificación enviada a {jid_to_notify} con éxito.")

        # Enviar un estado de chat activo
        msg = self.make_message(mto=jid_to_notify, mtype='chat')
        msg['chat_state'] = 'active'
        await msg.send()
        print("Estado de chat activo enviado.")

    async def enviar_archivo(self):  # enviar archivo
        jid_to_send = input(
            "Ingresa el JID del usuario al que deseas enviar el archivo: ")
        file_path = input(
            "Ingresa la ruta completa del archivo que deseas enviar: ")

        try:
            # Verifica si el archivo existe
            if not os.path.exists(file_path):
                print("El archivo no existe en la ruta especificada.")
                return

            # Lee el archivo y codifícalo en base64
            with open(file_path, "rb") as file:
                encoded_data = base64.b64encode(file.read()).decode()

            # Envía el archivo en fragmentos
            # Tamaño de cada trozo (ajusta según necesidades)
            chunk_size = 1024
            total_chunks = math.ceil(len(encoded_data) / chunk_size)

            for i in range(total_chunks):
                start = i * chunk_size
                end = (i + 1) * chunk_size
                chunk = encoded_data[start:end]

                # Crea un mensaje con el fragmento del archivo
                msg = self.Message()
                msg['to'] = jid_to_send
                msg['type'] = 'chat'
                msg['body'] = chunk

                # Agrega información sobre el fragmento actual y el total de fragmentos
                msg['file_fragment'] = str(i + 1)
                msg['file_total'] = str(total_chunks)

                # Envía el mensaje
                msg.send()

                # Espera brevemente antes de enviar el próximo fragmento (ajusta si es necesario)
                await asyncio.sleep(0.1)

            print(f"Archivo enviado a {jid_to_send} con éxito.")
        except IqTimeout:
            print("Sin respuesta del servidor.")
        except Exception as e:
            print(f"Error al enviar el archivo: {str(e)}")

    async def recibir_archivo(self):  # funcion para recibir archivos
        sender_jid = input(
            "Ingresa el JID del usuario del que deseas recibir el archivo: ")
        try:
            expected_fragment = 1
            total_fragments = None
            received_data = b''
            timeout_counter = 0

            # Ciclo para recibir fragmentos del archivo
            while True:
                # Verifica si hemos recibido todos los fragmentos esperados
                if total_fragments is not None and expected_fragment > total_fragments:
                    break

                # Espera un mensaje
                msg = await self.wait_for_message(timeout=10, from_jid=sender_jid)

                if msg is None:
                    # Incrementa el contador de tiempo de espera
                    timeout_counter += 1

                    # Si excede un límite de tiempo, finaliza la recepción
                    if timeout_counter > 10:  # Ajusta el límite de tiempo si es necesario
                        print(
                            "Tiempo de espera agotado. No se recibió ningún fragmento más del archivo.")
                        break

                    # Espera brevemente antes de intentar nuevamente
                    await asyncio.sleep(1)
                    continue

                # Reinicia el contador de tiempo de espera
                timeout_counter = 0

                # Verifica si es un mensaje de archivo
                if 'file_fragment' not in msg or 'file_total' not in msg:
                    print("Mensaje recibido no contiene información de archivo.")
                    continue

                # Obtén la información sobre el fragmento
                fragment_number = int(msg['file_fragment'])
                if total_fragments is None:
                    total_fragments = int(msg['file_total'])

                # Verifica si el fragmento del archivo es el esperado
                if fragment_number != expected_fragment:
                    print(
                        f"Se esperaba el fragmento {expected_fragment}, pero se recibió el fragmento {fragment_number}.")
                    continue

                # Decodifica y concatena el fragmento al archivo completo
                fragment_data = base64.b64decode(msg['body'])
                received_data += fragment_data

                # Verifica si es el último fragmento
                if fragment_number == total_fragments:
                    # Guarda el archivo recibido en el disco
                    file_path = f"archivos_recibidos/{sender_jid}_archivo_recibido"
                    with open(file_path, "wb") as file:
                        file.write(received_data)
                    print(f"Archivo recibido y guardado en: {file_path}")
                    break

                expected_fragment += 1
                print(
                    f"Recibido fragmento {fragment_number} de {total_fragments}.")

        except Exception as e:
            print(f"Error al recibir el archivo: {str(e)}")

    # Función para esperar mensajes entrantes, incluidos los fragmentos de archivo

    async def get_next_message_or_fragment(self, sender_jid):
        try:
            msg = await self.client_queue.get()
            if str(msg['from']) == sender_jid:
                return msg
            else:
                return None
        except Exception as e:
            print(f"Error al recibir mensaje o fragmento: {str(e)}")
            return None

    async def cambiar_presencia(self):  # cambiar el status

        flag = True
        status = ""

        while flag:
            menus.menu_status()
            status = input('')

            if status == '1':
                status = 'chat'
                flag = False

            elif status == '2':
                status = 'away'
                flag = False

            elif status == '3':
                status = 'xa'
                flag = False

            elif status == '4':
                status = 'dnd'
                flag = False

            else:
                print("\nOpción NO válida, ingrese de nuevo porfavor.")

        print('Escribe tu estado: ')
        status_message = input('')

        self.status = status
        self.status_message = status_message
        self.send_presence(pshow=self.status, pstatus=self.status_message)
        print("Status Cambiado")
        await self.get_roster()

    async def anadir_contacto(self):  # funcion para anadir contacto
        jid_to_add = input(
            "Ingresa el JID del usuario que deseas agregar (Ejemplo: usuario@servidor.com): ")
        try:
            self.send_presence_subscription(pto=jid_to_add)
            print(f"Solicitud de suscripción enviada a {jid_to_add}")
            await self.get_roster()
        except IqError as e:
            print(
                f"Error al mandar suscrpcion: {e.iq['error']['text']}")
        except IqTimeout:
            print("Sin respuesta del servidor.")

    async def mostrar_status_contacto(self):  # mostrar status de los contactos
        # Extract roster items and their presence status
        roster = self.client_roster
        contacts = roster.keys()
        contact_list = []

        if not contacts:
            print("No contacts found.")
            return

        for jid in contacts:
            user = jid

            # obtener presencia de cada contacto
            connection = roster.presence(jid)
            show = 'available'
            status = ''

            for answer, presence in connection.items():
                if presence['show']:
                    show = presence['show']
                if presence['status']:
                    status = presence['status']

            contact_list.append((user, show, status))

        print("\nLista de contactos:")
        for c in contact_list:
            print(f"Contacto: {c[0]}")
            print(f"Estado: {c[1]}")
            print(f"Mensaje de estado: {c[2]}")
            print("")
        print("")

    async def mostrar_detalles_contacto(self):  # mostrar detalles del contacto
        jid_to_find = input(
            "Ingresa el JID del usuario/contacto que deseas buscar: ")
        roster = self.client_roster
        contacts = roster._jids.keys()

        if jid_to_find not in contacts:
            print("El usuario/contacto no se encuentra en la lista de contactos.")
            return

        # Obtener presencia del contacto
        connection = roster.presence(jid_to_find)
        show = 'available'
        status = ''

        for answer, presence in connection.items():
            if presence['show']:
                show = presence['show']
            if presence['status']:
                status = presence['status']

        print("\nDetalles del contacto:")
        print(f"Usuario: {jid_to_find}")
        print(f"Mensaje de estado/status: {status}")
        print("")

    async def enviar_mensaje_contacto(self):  # enviar mensaje a algun contacto

        jid = await ainput('Ingrasa el JID del usuario\n')
        self.actual_chat = jid
        await aprint('\nPresiona x y luego enter para salir\n')
        chatting = True
        while chatting:
            message = await ainput('>> ')
            if message == 'x':
                chatting = False
                self.actual_chat = ''
            else:
                self.send_message(mto=jid, mbody=message, mtype='chat')

    # FUNCIONES DE ROOMS

    async def salas(self, iq):  # mostrar salas

        if iq['type'] == 'result':
            print('\nSalas de chat:')
            for salita in iq["disco_items"]:
                print(f'Nomrbre:{salita["name"]}')
                print(f'JID: {salita["jid"]}')
                print("")

    async def mostrar_rooms(self):  # muestra las salas
        try:
            await self['xep_0030'].get_items(jid="conference.alumchat.xyz")
        except (IqError, IqTimeout):
            print("Error")

    async def crear_room(self, roomName, nickName):  # crea una nueva sala
        self.room = roomName
        self.nick = nickName
        self.room_created = False

        try:
            await self.plugin['xep_0045'].join_muc(roomName, nickName)
            self.room_created = True
            print("Sala de chat creada exitosamente")
        except IqError as e:
            print(f"Error al crear la sala de chat: {e.iq['error']['text']}")
        except IqTimeout:
            print("Sin respuesta del Servidor.")

    async def unirse_room(self, roomName, nickName):  # unirse a una sala existente
        self.room = roomName
        self.nick = nickName
        self.room_created = False

        try:
            await self.plugin['xep_0045'].join_muc(roomName, nickName)
            self.room_created = True
            print("Sala de chat creada exitosamente")
        except IqError as e:
            print(f"Error al crear la sala de chat: {e.iq['error']['text']}")
        except IqTimeout:
            print("Sin respuesta del servidor.")
            return

        await aprint('\nPresiona x y luego enter para salir\n')
        chatting = True
        while chatting:
            message = await ainput('>> ')
            if message == 'x':
                chatting = False
                self.actual_chat = ''
                self.salir_room()
            else:
                self.send_message(self.room, message, mtype='groupchat')

    async def chat_room(self, message=''):  # chatear en la sala creada
        user = message['mucnick']
        is_actual_room = self.room in str(message['from'])
        display_message = f'{user}: {message["body"]}'

        if is_actual_room and user != self.nick:
            print(display_message)

    def salir_room(self):  # salirse de la sala
        self['xep_0045'].leave_muc(self.room, self.nick)
        self.room = None
        self.nick = None

    # FUNCION QUE CORRE TODO

    async def start(self, event):
        try:
            self.send_presence()
            await self.get_roster()
            self.is_connected = True
            print('Logged in')

            asyncio.create_task(self.instancia_usuario())

        # errores en log in
        except IqError as err:
            self.is_connected = False
            print(f"Error: {err.iq['error']['text']}")
            self.disconnect()
        except IqTimeout:
            self.is_connected = False
            print('Error de Time out')
            self.disconnect()

    async def instancia_usuario(self):  # funcion para menu de user

        while self.is_connected:

            menus.user_menu()  # menu de cliente
            opcion = await ainput("\n>> ")

            # todos los contactios con estado
            if opcion == "1":
                await self.mostrar_status_contacto()

            # agregar un nuevo usuario
            elif opcion == "2":
                await self.anadir_contacto()

            # detalles de un usuario
            elif opcion == "3":
                await self.mostrar_detalles_contacto()

            # chatear con usuario
            elif opcion == "4":
                await self.enviar_mensaje_contacto()

            # rooms
            elif opcion == "5":

                menus.group_chat()  # menu de rooms
                opcion = await ainput("\n>> ")

                # crear room
                if opcion == "1":
                    nickName = input(
                        "Ingresa el nickname que deseas usar en la sala: ")
                    room = input("Ingresa el nombre de la sala de chat: ")
                    roomName = f"{room}@conference.alumchat.xyz"
                    await self.crear_room(roomName, nickName)

                # chatear en room
                elif opcion == "2":
                    nickName = input(
                        "Ingresa el nickname que deseas usar en la sala: ")
                    room = input(
                        "Ingresa el nombre de la sala de chat a la cual te conectas: ")
                    await self.unirse_room(room, nickName)

                # mostrar rooms
                elif opcion == "3":
                    await self.mostrar_rooms()

                # salir de rooms
                elif opcion == "4":
                    print("Regresando...")
                    pass

            # cambiar presencia / status
            elif opcion == "6":
                await self.cambiar_presencia()

            # enviar o recibir notificaciones
            elif opcion == "7":
                jid_to_notify = input(
                    "Ingresa el JID del usuario al que deseas enviar la notificación: ")
                message = input("Ingresa el mensaje de la notificación: ")
                await self.enviar_notificacion(jid_to_notify, message)

            # enviar o recibir archivos
            elif opcion == "8":

                menus.menu_archivos()  # menu de archivos
                subopcion_archivos = await ainput("\n>> ")

                if subopcion_archivos == "1":
                    await self.enviar_archivo()
                elif subopcion_archivos == "2":
                    await self.recibir_archivo()
                else:
                    print("Opción inválida para enviar o recibir archivos.")

            # cerrar sesion
            elif opcion == "9":
                self.disconnect()
                self.is_connected = False

            else:
                print("\nOpción NO válida, ingrese de nuevo porfavor.")

            await asyncio.sleep(0.1)


class Borrar_Cliente(slixmpp.ClientXMPP):
    def __init__(self, jid, password):
        slixmpp.ClientXMPP.__init__(self, jid, password)
        self.user = jid
        self.add_event_handler("session_start", self.start)

    async def start(self, event):
        self.send_presence()
        await self.get_roster()
        await self.unregister()
        self.disconnect()

    async def unregister(self):
        response = self.Iq()
        response['type'] = 'set'
        response['from'] = self.boundjid.user
        fragment = ET.fromstring(
            "<query xmlns='jabber:iq:register'><remove/></query>")
        response.append(fragment)

        try:
            await response.send()
            print(f"Cuenta borrada correctamente: {self.boundjid.jid}!")
        except IqError as e:
            print(f"Error al borrar la cuenta: {e.iq['error']['text']}")
            self.disconnect()
        except IqTimeout:
            print("Sin respuesta del servidor.")
            self.disconnect()
