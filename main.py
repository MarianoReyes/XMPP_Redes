# clase futura para menus
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

    # clase futura para menus
    menus.menu()
    opcion = input("\n>> ")
