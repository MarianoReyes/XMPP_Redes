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
from utils import *

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

        # generado por IA para los diferentes plugins que se usaran
        self.register_plugin('xep_0030')  # Service Discovery
        self.register_plugin('xep_0199')  # Ping
        self.register_plugin('xep_0045')  # MUC
        self.register_plugin('xep_0085')  # Notifications
        self.register_plugin('xep_0004')  # Data Forms
        self.register_plugin('xep_0060')  # PubSub
        self.register_plugin('xep_0066')  # Out of Band Data
        self.register_plugin('xep_0363')  # HTTP File Upload

        # eventos
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('subscription_request',
                               self.handler_presencia)
        self.add_event_handler('message', self.chat)
        self.add_event_handler('disco_items', self.salas)
        self.add_event_handler('groupchat_message', self.chat_room)

    # FUNCIONES DE CONTACTOS Y CHATS

    # aceptar mensajes entrantes

    async def handler_presencia(self, presence):

        # si se tiene solicitud
        if presence['type'] == 'subscribe':
            try:
                self.send_presence_subscription(
                    pto=presence['from'], ptype='subscribed')
                await self.get_roster()
                self.mostrar_notificacion("Solicitud de suscripción aceptada de " + str(
                    presence['from']).split('@')[0])  # se muestra una notificacion
            except IqError as e:
                print(
                    f"Error accepting subscription request: {e.iq['error']['text']}")
            except IqTimeout:
                print("No response from server.")

        # si hay presencia
        else:
            # notificacion si esta logeado
            if self.is_connected:
                if presence['type'] == 'available':
                    self.mostrar_presencia(presence, True)
                elif presence['type'] == 'unavailable':
                    self.mostrar_presencia(presence, False)
                else:
                    self.mostrar_presencia(presence, None)

    async def chat(self, message):

        # chat normal
        if message['type'] == 'chat':
            # solo user
            user = str(message['from']).split('@')[0]

            # recibir archivos
            if message['body'].startswith("file://"):
                # info del archivo
                file_info = message['body'][7:].split("://")
                extension = file_info[0]
                # contenido
                encoded_data = file_info[1]

                try:
                    # decodificar archivo de base64
                    decoded_data = base64.b64decode(encoded_data)

                    file_path = f"archivos_recibidos/archivo_nuevo.{extension}"

                    # Use asyncio.sleep(0) to yield control to the event loop
                    await asyncio.sleep(0)

                    with open(file_path, "wb") as file:
                        file.write(decoded_data)

                    self.mostrar_notificacion(
                        f"Archivo recibido y guardado .{extension} de {user}")

                except Exception as e:
                    print("\nError al recibir archivo:", e)

            # mensajes
            else:
                # si el mensaje es con el que chatea
                if user == self.actual_chat.split('@')[0]:
                    print_azul(f'{user}: {message["body"]}')

                # notificacion si es otro
                else:
                    self.mostrar_notificacion(
                        f"Tienes un nuevo mensaje de {user}")

    # funcion generada por chat gpt para imprimir con colores
    def mostrar_notificacion(self, mensaje):
        print_rojo(mensaje)
        print("v")

    def mostrar_presencia(self, presence, is_available):

        # verficaciones previas
        if str(presence['from']).split("/")[0] != self.boundjid.bare and "conference" not in str(presence['from']):

            # estado del usaurio
            if is_available:
                show = 'available'
            elif is_available == False:
                show = 'offline'
            else:
                show = presence['show']

            # obtener mensaje de usaurio
            user = (str(presence['from']).split('/')[0])
            # presencia de contactos
            status = presence['status']

            if status != '':
                notification_message = f'{user} esta {show} - {status}'
            else:
                notification_message = f'{user} esta {show}'

            # se muestra la notificacion
            self.mostrar_notificacion(notification_message)

    async def enviar_archivo(self, recipient_jid, file_path):
        print("Enviando archivo:", file_path)

        extension = file_path.split(".")[-1]
        print("Extension del archivo:", extension)

        with open(file_path, "rb") as file:
            file_data = file.read()

        encoded_data = base64.b64encode(file_data).decode()
        print("Largo del Archivo:", len(encoded_data))

        message = f"file://{extension}://{encoded_data}"
        print("Mandando mensaje:", message)

        self.send_message(mto=recipient_jid, mbody=message, mtype='chat')
        print("Archivo enviado correctamente.")

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
            message = await ainput('')
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
            message = await ainput('')
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
        try:
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

                # enviar archivos
                elif opcion == "7":
                    user = input(
                        "Ingresa el JID del usuario: ")
                    path = input("Ingresa la ruta del archivo: ")
                    await self.enviar_archivo(user, path)

                # cerrar sesion
                elif opcion == "8":
                    self.disconnect()
                    self.is_connected = False

                else:
                    print("\nOpción NO válida, ingrese de nuevo porfavor.")

                await asyncio.sleep(0.1)
        except Exception as e:
            print("An error occurred:", e)


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
