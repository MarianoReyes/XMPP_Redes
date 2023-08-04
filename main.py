import menus
import cliente
import asyncio

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

        # login pendiente

    # eliminar cuenta
    elif opcion == "3":
        jid = input('usuario: ')
        password = input('contraseña: ')

        # delete pendiente

    else:
        print("\nOpción NO válida, ingrese de nuevo porfavor.")

    menus.menu()
    opcion = input("\n>> ")
