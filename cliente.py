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
                               self.accept_subscription)
        self.add_event_handler('message', self.chat_received)
        self.add_event_handler('disco_items', self.print_rooms)
        self.add_event_handler('groupchat_message', self.chatroom_message)
