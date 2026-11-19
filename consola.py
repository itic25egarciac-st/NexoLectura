from conexion import conectar
from mysql.connector import Error

def ejecutar(sql, valores=()):
    conexion = conectar()
    if conexion is None:
        return
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, valores)
        conexion.commit()
        print("\nOperación realizada correctamente.")
    except Error as error:
        print("\nNo se pudo completar la operación:", error)
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

def consultar(sql, valores=()):
    conexion = conectar()
    if conexion is None:
        return []
    try:
        cursor = conexion.cursor()
        cursor.execute(sql, valores)
        filas = cursor.fetchall()
        if not filas:
            print("\nNo hay registros.")
        else:
            for fila in filas:
                print(" | ".join(str(dato) for dato in fila))
        return filas
    except Error as error:
        print("\nError al consultar:", error)
        return []
    finally:
        if conexion.is_connected():
            cursor.close()
            conexion.close()

def pedir_entero(mensaje):
    while True:
        try:
            return int(input(mensaje))
        except ValueError:
            print("Escribe un número entero válido.")

def registrar_alumno():
    print("\n--- Registrar alumno ---")
    datos = (input("Matrícula: "), input("Nombre: "), input("Apellido: "),
            input("Grupo: "), input("Teléfono: ") or None,
            input("Correo: ") or None)
    ejecutar("""INSERT INTO ALUMNOS
    (matricula,nombre,apellido,grupo,telefono,correo)
    VALUES (%s,%s,%s,%s,%s,%s)""", datos)

def consultar_alumnos():
    print("\nID | Matrícula | Nombre | Apellido | Grupo | Teléfono | Correo")
    consultar("SELECT id_alumno,matricula,nombre,apellido,grupo,telefono,correo FROM ALUMNOS ORDER BY id_alumno")

def registrar_libro():
    print("\n--- Registrar libro ---")
    titulo = input("Título: ")
    autor = input("Autor: ")
    editorial = input("Editorial: ") or None
    anio = pedir_entero("Año de publicación: ")
    ejecutar("""INSERT INTO LIBROS (titulo,autor,editorial,anio_publicacion)
    VALUES (%s,%s,%s,%s)""", (titulo,autor,editorial,anio))

def consultar_libros():
    print("\nID | Título | Autor | Editorial | Año")
    consultar("SELECT id_libro,titulo,autor,editorial,anio_publicacion FROM LIBROS ORDER BY titulo")

def registrar_prestamo():
    print("\n--- Registrar préstamo ---")
    consultar("SELECT id_alumno,matricula,nombre,apellido FROM ALUMNOS ORDER BY id_alumno")
    id_alumno = pedir_entero("ID del alumno: ")
    consultar("SELECT id_libro,titulo,autor FROM LIBROS ORDER BY id_libro")
    id_libro = pedir_entero("ID del libro: ")
    fecha = input("Fecha del préstamo (AAAA-MM-DD): ")
    devolucion = input("Fecha límite de devolución (AAAA-MM-DD): ")
    ejecutar("""INSERT INTO PRESTAMOS
    (id_alumno,id_libro,fecha_prestamo,fecha_devolucion)
    VALUES (%s,%s,%s,%s)""", (id_alumno,id_libro,fecha,devolucion))

def consultar_prestamos():
    print("\nID | Alumno | Libro | Préstamo | Fecha límite | Devolución real | Estado")
    consultar("""SELECT p.id_prestamo, CONCAT(a.nombre,' ',a.apellido),
    l.titulo,p.fecha_prestamo,p.fecha_devolucion,p.fecha_devolucion_real,p.estado
    FROM PRESTAMOS p JOIN ALUMNOS a ON p.id_alumno=a.id_alumno
    JOIN LIBROS l ON p.id_libro=l.id_libro ORDER BY p.id_prestamo""")

def modificar_alumno():
    consultar_alumnos()
    id_alumno = pedir_entero("ID del alumno que modificarás: ")
    nombre = input("Nuevo nombre: ")
    apellido = input("Nuevo apellido: ")
    grupo = input("Nuevo grupo: ")
    ejecutar("UPDATE ALUMNOS SET nombre=%s,apellido=%s,grupo=%s WHERE id_alumno=%s",
            (nombre,apellido,grupo,id_alumno))

def eliminar_alumno():
    consultar_alumnos()
    id_alumno = pedir_entero("ID del alumno que eliminarás: ")
    print("Si tiene préstamos asociados, primero debes resolverlos.")
    ejecutar("DELETE FROM ALUMNOS WHERE id_alumno=%s", (id_alumno,))

def modificar_libro():
    consultar_libros()
    id_libro = pedir_entero("ID del libro que modificarás: ")
    titulo = input("Nuevo título: ")
    autor = input("Nuevo autor: ")
    ejecutar("UPDATE LIBROS SET titulo=%s,autor=%s WHERE id_libro=%s",
            (titulo,autor,id_libro))

def eliminar_libro():
    consultar_libros()
    id_libro = pedir_entero("ID del libro que eliminarás: ")
    print("Si tiene préstamos asociados, primero debes resolverlos.")
    ejecutar("DELETE FROM LIBROS WHERE id_libro=%s", (id_libro,))

def registrar_devolucion():
    consultar_prestamos_pendientes()
    id_prestamo = pedir_entero("ID del préstamo devuelto: ")
    fecha = input("Fecha real de devolución (AAAA-MM-DD): ")
    ejecutar("""UPDATE PRESTAMOS SET estado='Devuelto',
    fecha_devolucion_real=%s WHERE id_prestamo=%s AND estado='Prestado'""",
            (fecha,id_prestamo))

def consultar_prestamos_pendientes():
    print("\n--- Préstamos pendientes ---")
    consultar("""SELECT p.id_prestamo,CONCAT(a.nombre,' ',a.apellido),
    l.titulo,p.fecha_prestamo,p.fecha_devolucion
    FROM PRESTAMOS p JOIN ALUMNOS a ON p.id_alumno=a.id_alumno
    JOIN LIBROS l ON p.id_libro=l.id_libro
    WHERE p.estado='Prestado' ORDER BY p.fecha_devolucion""")

def menu():
    while True:
        print("""
========================================
            NEXO LECTURA
    Sistema de gestión bibliotecaria
========================================
1.  Registrar alumno
2.  Consultar alumnos
3.  Registrar libro
4.  Consultar libros
5.  Registrar préstamo
6.  Consultar préstamos
7.  Modificar alumno
8.  Eliminar alumno
9.  Modificar libro
10. Eliminar libro
11. Registrar devolución
12. Consultar préstamos pendientes
13. Salir
========================================
""")
        opcion = input("Selecciona una opción: ")
        acciones = {
            "1": registrar_alumno, "2": consultar_alumnos,
            "3": registrar_libro, "4": consultar_libros,
            "5": registrar_prestamo, "6": consultar_prestamos,
            "7": modificar_alumno, "8": eliminar_alumno,
            "9": modificar_libro, "10": eliminar_libro,
            "11": registrar_devolucion, "12": consultar_prestamos_pendientes
        }
        if opcion == "13":
            print("Gracias por utilizar Nexo Lectura.")
            break
        elif opcion in acciones:
            acciones[opcion]()
        else:
            print("Opción no válida.")

if __name__ == "__main__":
    menu()