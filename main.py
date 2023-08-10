import menus
import cliente
import asyncio
from cliente import Cliente, Borrar_Cliente

'''
Disclaimer: ChatGPT sugirió seguir la estructura de 3 principales clases:
1. main donde se ejecutará el programa
2. Una clase para los diferentes menús de las aplicaciones
3. Una clase de Cliente, que se encargará de toda la comunicación con XMPP
'''

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

menus.menu()
opcion = input("\n>> ")

while opcion != "4":

    # registro
    if opcion == "1":
        jid = input('usuario: ')
        password = input('contraseña: ')

        if cliente.register(jid, password):
            print("Registro completado de manera correcta")
        else:
            print("Registro NO completado")

    # log in
    elif opcion == "2":
        jid = input('usuario: ')
        password = input('contraseña: ')

        client = Cliente(jid, password)
        client.connect(disable_starttls=True)
        client.process(forever=False)

    # eliminar cuenta
    elif opcion == "3":
        jid = input('usuario: ')
        password = input('contraseña: ')

        client = Borrar_Cliente(jid, password)
        client.connect(disable_starttls=True)
        client.process(forever=False)

    else:
        print("\nOpción NO válida, ingrese de nuevo porfavor.")

    menus.menu()
    opcion = input("\n>> ")
