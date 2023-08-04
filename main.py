import menus

'''
Disclaimer: ChatGPT sugirió seguir la estructura de 3 principales clases:
1. main donde se ejecutará el programa
2. Una clase para los diferentes menús de las aplicaciones
3. Una clase de Cliente, que se encargará de toda la comunicación con XMPP
'''

menus.menu()
opcion = input("\n>> ")

while opcion != "4":

    # registro
    if opcion == "1":
        jid = input('usuario: ')
        password = input('contraseña: ')

        # registro pendiente

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
