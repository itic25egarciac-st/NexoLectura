
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs, quote
from datetime import date
from html import escape
from http.cookies import SimpleCookie
import os
import secrets
import hmac

from conexion import conectar

HOST = "0.0.0.0"
PUERTO = int(os.environ.get("PORT", 8000))

ADMIN_PASSWORD = os.environ.get("NEXO_ADMIN_PASSWORD")
SESIONES = {}


# -------------------- BASE DE DATOS --------------------

def consultar(sql, valores=()):
    conexion = conectar()
    if conexion is None:
        raise Exception("No se pudo conectar con la base de datos.")

    cursor = conexion.cursor(dictionary=True)
    try:
        cursor.execute(sql, valores)
        return cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()


def ejecutar(sql, valores=()):
    conexion = conectar()
    if conexion is None:
        raise Exception("No se pudo conectar con la base de datos.")

    cursor = conexion.cursor()
    try:
        cursor.execute(sql, valores)
        conexion.commit()
    finally:
        cursor.close()
        conexion.close()


# -------------------- DISEÑO --------------------

def pagina(titulo, contenido, mensaje="", admin=False):
    aviso = ""
    if mensaje:
        aviso = f'<div class="aviso">{escape(mensaje)}</div>'

    acceso = (
        '<form method="POST" action="/logout" style="display:inline;">'
        '<button class="boton-nav">Cerrar sesión</button></form>'
        if admin else '<a href="/login">Administradora</a>'
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{escape(titulo)} | Nexo Lectura</title>
<style>
:root {{
    --cafe:#493326; --cafe-claro:#74543d;
    --dorado:#bd9560; --crema:#f6f1e9; --texto:#463629;
}}
* {{box-sizing:border-box;}}
body {{
    margin:0; background:var(--crema); color:var(--texto);
    font-family:Georgia,'Times New Roman',serif;
}}
header {{
    background:var(--cafe); color:#fff8ed;
    padding:25px max(6%,calc((100% - 1180px)/2));
    border-bottom:4px solid var(--dorado);
}}
.marca {{
    font-family:Arial,sans-serif; font-size:30px;
    font-weight:bold; letter-spacing:4px; margin:0;
}}
.submarca {{
    color:#e3ceb2; font:13px Arial,sans-serif;
    letter-spacing:2px; margin:8px 0 0;
}}
nav {{
    background:var(--cafe-claro);
    padding:16px max(6%,calc((100% - 1180px)/2));
    display:flex; flex-wrap:wrap; align-items:center; gap:24px;
}}
nav a,.boton-nav {{
    color:#fff8ed; text-decoration:none;
    font:bold 14px Arial,sans-serif;
}}
nav a:hover {{color:#f0d19e;}}
.boton-nav {{
    background:transparent; border:1px solid #e3ceb2;
    padding:7px 12px; cursor:pointer;
}}
main {{
    max-width:1180px; margin:34px auto;
    padding:0 22px; min-height:420px;
}}
.hero {{
    min-height:390px; border-radius:18px; padding:52px;
    color:white; display:flex; flex-direction:column;
    justify-content:center;
    background:
    linear-gradient(90deg,rgba(35,24,17,.88),rgba(35,24,17,.18)),
    url("https://images.unsplash.com/photo-1507842217343-583bb7270b66?auto=format&fit=crop&w=1800&q=85")
    center/cover no-repeat;
    box-shadow:0 12px 30px rgba(50,35,22,.18);
}}
.hero .etiqueta {{
    color:#f0d19e; font:bold 12px Arial,sans-serif;
    letter-spacing:3px; text-transform:uppercase;
}}
.hero h2 {{
    font-size:clamp(32px,5vw,52px);
    line-height:1.12; max-width:600px; margin:14px 0;
}}
.hero p {{
    max-width:510px; font:16px/1.8 Arial,sans-serif;
    color:#fff8ed;
}}
.titulo-seccion {{margin:34px 0 8px;font-size:28px;}}
.subtitulo {{color:#806b58;font:14px/1.6 Arial,sans-serif;}}
.tarjetas {{
    display:grid; grid-template-columns:repeat(auto-fit,minmax(190px,1fr));
    gap:18px; margin:22px 0 35px;
}}
.tarjeta {{
    background:white; padding:24px; border-radius:13px;
    border-top:4px solid var(--dorado);
    box-shadow:0 5px 18px rgba(70,45,25,.07);
    font:14px Arial,sans-serif;
}}
.numero {{font:bold 36px Arial,sans-serif;color:#8b6543;margin-top:12px;}}
.panel {{
    background:white; padding:28px; border-radius:15px;
    margin-bottom:24px; box-shadow:0 5px 20px rgba(70,45,25,.07);
}}
.panel h2 {{margin-top:0;}}
label {{
    display:block; margin:13px 0 7px;
    font:bold 14px Arial,sans-serif;
}}
input,select {{
    display:block; width:100%; padding:12px;
    border:1px solid #ded1c1; border-radius:8px;
    background:#fdfbf8; font-size:14px;
}}
input:focus,select:focus {{outline:2px solid #bd9560;}}
button {{
    background:#806044; color:white; border:0;
    padding:11px 19px; border-radius:8px;
    cursor:pointer; font-weight:bold;
}}
button:hover {{background:#493326;}}
.aviso {{
    background:#f0e2c9; color:#493326;
    padding:14px 17px; border-radius:9px;
    margin-bottom:20px; font:14px Arial,sans-serif;
}}
.tabla-contenedor {{width:100%;overflow-x:auto;}}
table {{
    width:100%; border-collapse:collapse;
    margin-top:16px; font:14px Arial,sans-serif; background:white;
}}
th,td {{padding:13px;border-bottom:1px solid #eee4d8;text-align:left;}}
th {{background:#f0e6d9;color:#60452f;}}
tr:hover {{background:#fcf8f2;}}
.eliminar {{background:#a3483e;}}
.eliminar:hover {{background:#762d27;}}
footer {{
    text-align:center; padding:28px; color:#806044;
    font:13px Arial,sans-serif;
}}
@media(max-width:650px) {{
    .hero {{padding:28px;min-height:320px;}}
    nav {{gap:17px;}}
    .panel {{padding:19px;}}
}}
</style>
</head>
<body>
<header>
    <h1 class="marca">NEXO LECTURA</h1>
    <p class="submarca">SISTEMA DE GESTIÓN BIBLIOTECARIA</p>
</header>
<nav>
    <a href="/">Inicio</a>
    <a href="/alumnos">Alumnos</a>
    <a href="/libros">Libros</a>
    <a href="/prestamos">Préstamos</a>
    <a href="/consultas">Consultas</a>
    {acceso}
</nav>
<main>
    {aviso}
    {contenido}
</main>
<footer>NEXO LECTURA · Sistema de Gestión Bibliotecaria</footer>
</body>
</html>"""


def campo(nombre, etiqueta, tipo="text", requerido=True):
    obligatorio = "required" if requerido else ""
    return (
        f'<label for="{escape(nombre)}">{escape(etiqueta)}</label>'
        f'<input id="{escape(nombre)}" name="{escape(nombre)}" '
        f'type="{escape(tipo)}" {obligatorio}>'
    )


def valor_formulario(datos, nombre):
    return datos.get(nombre, [""])[0].strip()


# -------------------- SERVIDOR --------------------

class Servidor(BaseHTTPRequestHandler):

    def es_administradora(self):
        cookie = SimpleCookie()
        cookie.load(self.headers.get("Cookie", ""))
        sesion = cookie.get("nexo_session")
        return sesion is not None and sesion.value in SESIONES

    def crear_sesion(self):
        token = secrets.token_urlsafe(32)
        SESIONES[token] = True
        return token

    def responder(self, contenido, codigo=200):
        datos = contenido.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(datos)

    def redirigir(self, ruta, mensaje=""):
        if mensaje:
            ruta += "?mensaje=" + quote(mensaje)
        self.send_response(303)
        self.send_header("Location", ruta)
        self.end_headers()

    def datos_formulario(self):
        longitud = int(self.headers.get("Content-Length", 0))
        cuerpo = self.rfile.read(longitud).decode("utf-8")
        return parse_qs(cuerpo)

    def do_GET(self):
        ruta = urlparse(self.path).path
        mensaje = parse_qs(urlparse(self.path).query).get("mensaje", [""])[0]
        admin = self.es_administradora()

        try:
            # INICIO DE SESION
            if ruta == "/login":
                contenido = """
                <div class="panel" style="max-width:500px;margin:auto;">
                    <h2>Acceso de administradora</h2>
                    <p class="subtitulo">Inicia sesión para administrar Nexo Lectura.</p>
                    <form method="POST" action="/login">
                        <label for="password">Contraseña</label>
                        <input type="password" id="password" name="password" required>
                        <br><button type="submit">Iniciar sesión</button>
                    </form>
                </div>
                """
                self.responder(pagina("Acceso", contenido, mensaje, admin))

            # INICIO
            elif ruta == "/":
                alumnos = consultar("SELECT COUNT(*) AS total FROM ALUMNOS")[0]["total"]
                libros = consultar("SELECT COUNT(*) AS total FROM LIBROS")[0]["total"]
                activos = consultar(
                    "SELECT COUNT(*) AS total FROM PRESTAMOS WHERE estado='Prestado'"
                )[0]["total"]
                devueltos = consultar(
                    "SELECT COUNT(*) AS total FROM PRESTAMOS WHERE estado='Devuelto'"
                )[0]["total"]

                contenido = """
                <section class="hero">
                    <span class="etiqueta">Bienvenido a tu biblioteca</span>
                    <h2>Un mundo de conocimiento te espera</h2>
                    <p>Organiza, consulta y administra los recursos de tu biblioteca escolar en un solo lugar.</p>
                </section>
                <h2 class="titulo-seccion">Resumen de la biblioteca</h2>
                <p class="subtitulo">Consulta la información general de Nexo Lectura.</p>
                """
                contenido += f"""
                <section class="tarjetas">
                    <div class="tarjeta">Alumnos registrados<div class="numero">{alumnos}</div></div>
                    <div class="tarjeta">Libros registrados<div class="numero">{libros}</div></div>
                    <div class="tarjeta">Préstamos activos<div class="numero">{activos}</div></div>
                    <div class="tarjeta">Libros devueltos<div class="numero">{devueltos}</div></div>
                </section>
                """
                if admin:
                    contenido += '<p class="subtitulo">Sesión de administradora activa.</p>'

                self.responder(pagina("Inicio", contenido, mensaje, admin))

            # ALUMNOS
            elif ruta == "/alumnos":
                filas = consultar("SELECT * FROM ALUMNOS ORDER BY id_alumno DESC")
                contenido = ""

                if admin:
                    contenido += """
                    <div class="panel">
                        <h2>Registrar alumno</h2>
                        <p class="subtitulo">Agrega un nuevo alumno a la biblioteca.</p>
                        <form method="POST" action="/alumnos">
                    """
                    contenido += campo("matricula", "Matrícula")
                    contenido += campo("nombre", "Nombre")
                    contenido += campo("apellido", "Apellido")
                    contenido += campo("grupo", "Grupo")
                    contenido += campo("telefono", "Teléfono", requerido=False)
                    contenido += campo("correo", "Correo electrónico", "email", False)
                    contenido += '<br><button type="submit">Guardar alumno</button></form></div>'

                contenido += """
                <div class="panel">
                    <h2>Alumnos registrados</h2>
                    <div class="tabla-contenedor"><table>
                    <tr><th>Matrícula</th><th>Nombre</th>
                    <th>Apellido</th><th>Grupo</th>
                """
                if admin:
                    contenido += "<th>Acción</th>"
                contenido += "</tr>"

                for f in filas:
                    contenido += f"""
                    <tr>
                        <td>{escape(str(f['matricula']))}</td>
                        <td>{escape(str(f['nombre']))}</td>
                        <td>{escape(str(f['apellido']))}</td>
                        <td>{escape(str(f['grupo']))}</td>
                    """
                    if admin:
                        contenido += f"""
                        <td><form method="POST" action="/alumnos/eliminar/{f['id_alumno']}">
                        <button class="eliminar">Eliminar</button></form></td>
                        """
                    contenido += "</tr>"

                contenido += "</table></div></div>"
                self.responder(pagina("Alumnos", contenido, mensaje, admin))

            # LIBROS
            elif ruta == "/libros":
                filas = consultar("SELECT * FROM LIBROS ORDER BY id_libro DESC")
                contenido = ""

                if admin:
                    contenido += """
                    <div class="panel">
                        <h2>Registrar libro</h2>
                        <p class="subtitulo">Agrega un nuevo libro al catálogo.</p>
                        <form method="POST" action="/libros">
                    """
                    contenido += campo("titulo", "Título")
                    contenido += campo("autor", "Autor")
                    contenido += campo("editorial", "Editorial", requerido=False)
                    contenido += campo("anio_publicacion", "Año de publicación", "number")
                    contenido += '<br><button type="submit">Guardar libro</button></form></div>'

                contenido += """
                <div class="panel">
                    <h2>Libros registrados</h2>
                    <div class="tabla-contenedor"><table>
                    <tr><th>Título</th><th>Autor</th>
                    <th>Editorial</th><th>Año</th>
                """
                if admin:
                    contenido += "<th>Acción</th>"
                contenido += "</tr>"

                for f in filas:
                    contenido += f"""
                    <tr>
                        <td>{escape(str(f['titulo']))}</td>
                        <td>{escape(str(f['autor']))}</td>
                        <td>{escape(str(f['editorial'] or ''))}</td>
                        <td>{escape(str(f['anio_publicacion']))}</td>
                    """
                    if admin:
                        contenido += f"""
                        <td><form method="POST" action="/libros/eliminar/{f['id_libro']}">
                        <button class="eliminar">Eliminar</button></form></td>
                        """
                    contenido += "</tr>"

                contenido += "</table></div></div>"
                self.responder(pagina("Libros", contenido, mensaje, admin))

            # PRESTAMOS: SOLO REGISTRO DE NUEVOS PRESTAMOS
            elif ruta == "/prestamos":
                libros = consultar("SELECT id_libro,titulo FROM LIBROS ORDER BY titulo")
                contenido = """
                <div class="panel">
                    <h2>Registrar préstamo</h2>
                    <p class="subtitulo">Escribe la matrícula del alumno y selecciona el libro que llevará.</p>
                """
                if admin:
                    contenido += '<form method="POST" action="/prestamos">'
                    contenido += campo("matricula", "Matrícula del alumno")
                    contenido += '<label for="id_libro">Libro</label><select id="id_libro" name="id_libro" required>'
                    if libros:
                        contenido += '<option value="">Selecciona un libro</option>'
                        for libro in libros:
                            contenido += (
                                f'<option value="{libro["id_libro"]}">'
                                f'{escape(str(libro["titulo"]))}</option>'
                            )
                    else:
                        contenido += '<option value="">No hay libros registrados</option>'
                    contenido += '</select>'
                    contenido += campo("fecha_prestamo", "Fecha de préstamo", "date")
                    contenido += campo("fecha_devolucion", "Fecha prevista de devolución", "date")
                    contenido += '<br><button type="submit">Registrar préstamo</button></form>'
                else:
                    contenido += '<p>Inicia sesión como administradora para registrar préstamos.</p>'
                contenido += "</div>"
                contenido += (
                    '<div class="panel"><h2>Historial de préstamos</h2>'
                    '<p class="subtitulo">Consulta el historial completo en el apartado '
                    '<a href="/consultas">Consultas</a>.</p></div>'
                )
                self.responder(pagina("Préstamos", contenido, mensaje, admin))

            # CONSULTAS: HISTORIAL DE PRESTAMOS Y DEVOLUCIONES
            elif ruta == "/consultas":
                columnas_prestamos = {
                    columna["Field"]
                    for columna in consultar("SHOW COLUMNS FROM PRESTAMOS")
                }

                expresion_devolucion_real = (
                    "p.fecha_devolucion_real"
                    if "fecha_devolucion_real" in columnas_prestamos
                    else "NULL"
                )
                expresion_estado = (
                    "p.estado" if "estado" in columnas_prestamos
                    else "'Prestado'"
                )

                filas = consultar(f"""
                    SELECT p.id_prestamo, a.matricula,
                        CONCAT(a.nombre,' ',a.apellido) AS alumno,
                        l.titulo,
                        p.fecha_prestamo, p.fecha_devolucion,
                        {expresion_devolucion_real} AS fecha_devolucion_real,
                        {expresion_estado} AS estado
                    FROM PRESTAMOS p
                    INNER JOIN ALUMNOS a ON p.id_alumno=a.id_alumno
                    INNER JOIN LIBROS l ON p.id_libro=l.id_libro
                    ORDER BY p.id_prestamo DESC
                """)

                contenido = """
                <div class="panel">
                    <h2>Consultas de préstamos</h2>
                    <p class="subtitulo">Historial de alumnos, libros prestados y estado de devolución.</p>
                    <div class="tabla-contenedor"><table>
                    <tr><th>Matrícula</th><th>Alumno</th><th>Libro</th>
                    <th>Fecha de préstamo</th>
                    <th>Devolución prevista</th><th>Devolución real</th><th>Estado</th>
                """
                if admin:
                    contenido += "<th>Acción</th>"
                contenido += "</tr>"

                if filas:
                    for f in filas:
                        fecha_real = f["fecha_devolucion_real"] or "Pendiente"
                        contenido += f"""
                        <tr>
                            <td>{escape(str(f['matricula']))}</td>
                            <td>{escape(str(f['alumno']))}</td>
                            <td>{escape(str(f['titulo']))}</td>
                            <td>{escape(str(f['fecha_prestamo']))}</td>
                            <td>{escape(str(f['fecha_devolucion']))}</td>
                            <td>{escape(str(fecha_real))}</td>
                            <td>{escape(str(f['estado']))}</td>
                        """
                        if admin:
                            accion = ""
                            if f["estado"] == "Prestado":
                                accion = (
                                    f'<form method="POST" action="/prestamos/devolver/{f["id_prestamo"]}">'
                                    '<button>Registrar devolución</button></form>'
                                )
                            contenido += f"<td>{accion}</td>"
                        contenido += "</tr>"
                else:
                    columnas = 8 if admin else 7
                    contenido += f'<tr><td colspan="{columnas}">Todavía no hay préstamos registrados.</td></tr>'

                contenido += "</table></div></div>"
                self.responder(pagina("Consultas", contenido, mensaje, admin))

            else:
                self.responder(
                    pagina("No encontrado", "<div class='panel'><h2>La página no existe.</h2></div>", admin=admin),
                    404
                )

        except Exception as error:
            contenido = (
                "<div class='panel'><h2>Ocurrió un problema</h2>"
                "<p>Revisa la conexión con TiDB y las tablas de la base de datos.</p><p>"
                + escape(str(error)) + "</p></div>"
            )
            self.responder(pagina("Error", contenido, admin=admin), 500)

    def do_POST(self):
        ruta = urlparse(self.path).path
        datos = self.datos_formulario()

        def valor(nombre):
            return valor_formulario(datos, nombre)

        # INICIAR SESION
        if ruta == "/login":
            contraseña = valor("password")

            if ADMIN_PASSWORD and hmac.compare_digest(contraseña, ADMIN_PASSWORD):
                token = self.crear_sesion()
                seguro = "; Secure" if self.headers.get("X-Forwarded-Proto") == "https" else ""

                self.send_response(303)
                self.send_header("Location", "/")
                self.send_header(
                    "Set-Cookie",
                    f"nexo_session={token}; HttpOnly; SameSite=Strict; Path=/{seguro}"
                )
                self.end_headers()
            else:
                self.redirigir("/login", "Contraseña incorrecta.")
            return

        # CERRAR SESION
        if ruta == "/logout":
            cookie = SimpleCookie()
            cookie.load(self.headers.get("Cookie", ""))
            sesion = cookie.get("nexo_session")

            if sesion:
                SESIONES.pop(sesion.value, None)

            self.send_response(303)
            self.send_header("Location", "/")
            self.send_header(
                "Set-Cookie",
                "nexo_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0"
            )
            self.end_headers()
            return

        # PROTEGER TODAS LAS OPERACIONES
        if not self.es_administradora():
            self.redirigir("/login", "Inicia sesión para realizar esa operación.")
            return

        try:
            if ruta == "/alumnos":
                ejecutar("""
                    INSERT INTO ALUMNOS
                    (matricula,nombre,apellido,grupo,telefono,correo)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (
                    valor("matricula"), valor("nombre"), valor("apellido"),
                    valor("grupo"), valor("telefono") or None,
                    valor("correo") or None
                ))
                self.redirigir("/alumnos", "Alumno registrado correctamente.")

            elif ruta.startswith("/alumnos/eliminar/"):
                identificador = int(ruta.split("/")[-1])
                ejecutar("DELETE FROM ALUMNOS WHERE id_alumno=%s", (identificador,))
                self.redirigir("/alumnos", "Alumno eliminado.")

            elif ruta == "/libros":
                ejecutar("""
                    INSERT INTO LIBROS (titulo,autor,editorial,anio_publicacion)
                    VALUES (%s,%s,%s,%s)
                """, (
                    valor("titulo"), valor("autor"),
                    valor("editorial") or None, valor("anio_publicacion")
                ))
                self.redirigir("/libros", "Libro registrado correctamente.")

            elif ruta.startswith("/libros/eliminar/"):
                identificador = int(ruta.split("/")[-1])
                ejecutar("DELETE FROM LIBROS WHERE id_libro=%s", (identificador,))
                self.redirigir("/libros", "Libro eliminado.")

            elif ruta == "/prestamos":
                matricula = valor("matricula")
                id_libro = valor("id_libro")
                fecha_prestamo = valor("fecha_prestamo")
                fecha_devolucion = valor("fecha_devolucion")

                if not matricula:
                    self.redirigir("/prestamos", "Escribe la matrícula del alumno.")
                    return

                alumno = consultar(
                    "SELECT id_alumno FROM ALUMNOS WHERE matricula=%s",
                    (matricula,)
                )
                if not alumno:
                    self.redirigir(
                        "/prestamos",
                        "Matrícula no encontrada. Verifica el número o registra primero al alumno."
                    )
                    return

                if not id_libro:
                    self.redirigir("/prestamos", "Selecciona un libro.")
                    return

                libro = consultar(
                    "SELECT id_libro FROM LIBROS WHERE id_libro=%s",
                    (id_libro,)
                )
                if not libro:
                    self.redirigir("/prestamos", "El libro seleccionado no existe.")
                    return

                ocupado = consultar(
                    "SELECT id_prestamo FROM PRESTAMOS "
                    "WHERE id_libro=%s AND estado='Prestado' LIMIT 1",
                    (id_libro,)
                )
                if ocupado:
                    self.redirigir(
                        "/prestamos",
                        "Este libro ya está prestado. No se puede registrar otro préstamo hasta que sea devuelto."
                    )
                    return

                if not fecha_prestamo or not fecha_devolucion:
                    self.redirigir("/prestamos", "Completa las fechas del préstamo y devolución.")
                    return

                columnas_prestamos = {
                    columna["Field"]
                    for columna in consultar("SHOW COLUMNS FROM PRESTAMOS")
                }
                if "fecha_registro" in columnas_prestamos:
                    ejecutar("""
                        INSERT INTO PRESTAMOS
                        (id_alumno,id_libro,fecha_registro,fecha_prestamo,fecha_devolucion)
                        VALUES (%s,%s,NOW(),%s,%s)
                    """, (
                        alumno[0]["id_alumno"], id_libro,
                        fecha_prestamo, fecha_devolucion
                    ))
                else:
                    ejecutar("""
                        INSERT INTO PRESTAMOS
                        (id_alumno,id_libro,fecha_prestamo,fecha_devolucion)
                        VALUES (%s,%s,%s,%s)
                    """, (
                        alumno[0]["id_alumno"], id_libro,
                        fecha_prestamo, fecha_devolucion
                    ))
                self.redirigir("/prestamos", "Préstamo registrado correctamente.")

            elif ruta.startswith("/prestamos/devolver/"):
                identificador = int(ruta.split("/")[-1])
                columnas_prestamos = {
                    columna["Field"]
                    for columna in consultar("SHOW COLUMNS FROM PRESTAMOS")
                }
                if "fecha_devolucion_real" in columnas_prestamos:
                    ejecutar("""
                        UPDATE PRESTAMOS
                        SET estado='Devuelto', fecha_devolucion_real=%s
                        WHERE id_prestamo=%s AND estado='Prestado'
                    """, (date.today().isoformat(), identificador))
                else:
                    ejecutar("""
                        UPDATE PRESTAMOS
                        SET estado='Devuelto'
                        WHERE id_prestamo=%s AND estado='Prestado'
                    """, (identificador,))
                self.redirigir("/consultas", "Devolución registrada correctamente.")

            else:
                self.redirigir("/", "Operación no encontrada.")

        except Exception as error:
            if ruta.startswith("/alumnos"):
                destino = "/alumnos"
            elif ruta.startswith("/libros"):
                destino = "/libros"
            else:
                destino = "/prestamos"
            self.redirigir(destino, "No se pudo completar: " + str(error))


# -------------------- INICIAR SERVIDOR --------------------

if __name__ == "__main__":
    if not ADMIN_PASSWORD:
        raise RuntimeError(
            "Falta configurar la variable de entorno NEXO_ADMIN_PASSWORD."
        )

    servidor = HTTPServer((HOST, PUERTO), Servidor)

    print("NEXO LECTURA está funcionando.")
    print(f"Puerto: {PUERTO}")
    print("Deja esta ventana abierta mientras utilizas la página.")

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
        servidor.server_close()
