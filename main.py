import sqlite3
from datetime import datetime, date, timedelta
from getpass import getpass
import hashlib
import os

DB = os.path.join(os.path.dirname(__file__), 'timewise.db')

def conexion():
    return sqlite3.connect(DB)

def iniciar_bd():
    with conexion() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT NOT NULL UNIQUE, clave TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS tareas (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, titulo TEXT NOT NULL, prioridad INTEGER NOT NULL DEFAULT 2, minutos INTEGER NOT NULL DEFAULT 30, completada INTEGER NOT NULL DEFAULT 0, FOREIGN KEY(usuario_id) REFERENCES usuarios(id));
        CREATE TABLE IF NOT EXISTS eventos (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, titulo TEXT NOT NULL, fecha TEXT NOT NULL, FOREIGN KEY(usuario_id) REFERENCES usuarios(id));
        CREATE TABLE IF NOT EXISTS recordatorios (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER NOT NULL, texto TEXT NOT NULL, fecha TEXT NOT NULL, FOREIGN KEY(usuario_id) REFERENCES usuarios(id));
        ''')

def clave_hash(clave):
    return hashlib.sha256(clave.encode('utf-8')).hexdigest()

def pedir_fecha():
    while True:
        valor = input('Fecha y hora (DD/MM/AAAA HH:MM): ').strip()
        try:
            return datetime.strptime(valor, '%d/%m/%Y %H:%M').strftime('%Y-%m-%d %H:%M')
        except ValueError:
            print('Formato incorrecto. Ejemplo: 25/11/2026 09:00')

def iniciar_usuario():
    while True:
        print('\n=== TIMEWISE: ACCESO ===\n1. Registrarse\n2. Iniciar sesion\n3. Salir')
        opcion = input('Opcion: ').strip()
        if opcion == '3':
            return None
        if opcion not in ('1', '2'):
            print('Opcion incorrecta')
            continue
        nombre = input('Usuario: ').strip()
        clave = input('Contrasena: ').strip()
        if not nombre or not clave:
            print('Usuario y contrasena obligatorios')
            continue
        with conexion() as c:
            if opcion == '1':
                try:
                    c.execute('INSERT INTO usuarios(nombre,clave) VALUES (?,?)', (nombre, clave_hash(clave)))
                    print('Usuario registrado. Ya puedes iniciar sesion.')
                except sqlite3.IntegrityError:
                    print('Ese usuario ya existe')
            else:
                usuario = c.execute('SELECT id FROM usuarios WHERE nombre=? AND clave=?', (nombre, clave_hash(clave))).fetchone()
                if usuario:
                    print('Bienvenido, ' + nombre)
                    return usuario[0]
                print('Datos incorrectos')

def mostrar_tareas(uid):
    with conexion() as c:
        filas = c.execute('SELECT id,titulo,prioridad,minutos,completada FROM tareas WHERE usuario_id=? ORDER BY completada, prioridad, id', (uid,)).fetchall()
    if not filas:
        print('No tienes tareas')
    for id_, titulo, prioridad, minutos, hecha in filas:
        print(f'{id_}. {titulo} | prioridad {prioridad} | {minutos} min | {"Hecha" if hecha else "Pendiente"}')

def menu_tareas(uid):
    while True:
        print('\n=== TAREAS ===\n1. Anadir\n2. Ver\n3. Completar\n4. Eliminar\n5. Volver')
        op = input('Opcion: ').strip()
        if op == '5': return
        if op == '1':
            titulo = input('Nombre de la tarea: ').strip()
            if not titulo:
                print('El nombre es obligatorio'); continue
            try:
                prioridad = int(input('Prioridad (1 alta, 2 media, 3 baja): '))
                minutos = int(input('Duracion estimada en minutos: '))
                if prioridad not in (1,2,3) or minutos <= 0: raise ValueError
            except ValueError:
                print('Prioridad o duracion incorrecta'); continue
            with conexion() as c:
                c.execute('INSERT INTO tareas(usuario_id,titulo,prioridad,minutos) VALUES (?,?,?,?)', (uid,titulo,prioridad,minutos))
            print('Tarea guardada')
        elif op == '2': mostrar_tareas(uid)
        elif op in ('3','4'):
            mostrar_tareas(uid)
            try: id_ = int(input('ID de la tarea: '))
            except ValueError:
                print('ID incorrecto'); continue
            with conexion() as c:
                if op == '3':
                    cur = c.execute('UPDATE tareas SET completada=1 WHERE id=? AND usuario_id=?', (id_,uid))
                else:
                    cur = c.execute('DELETE FROM tareas WHERE id=? AND usuario_id=?', (id_,uid))
            print('Operacion realizada' if cur.rowcount else 'No existe esa tarea')
        else: print('Opcion incorrecta')

def menu_fechas(uid, tabla):
    nombre = 'EVENTOS' if tabla == 'eventos' else 'RECORDATORIOS'
    campo = 'titulo' if tabla == 'eventos' else 'texto'
    while True:
        print(f'\n=== {nombre} ===\n1. Anadir\n2. Ver\n3. Eliminar\n4. Volver')
        op = input('Opcion: ').strip()
        if op == '4': return
        if op == '1':
            texto = input('Nombre o descripcion: ').strip()
            if not texto:
                print('No puede estar vacio'); continue
            fecha = pedir_fecha()
            with conexion() as c:
                c.execute(f'INSERT INTO {tabla}(usuario_id,{campo},fecha) VALUES (?,?,?)', (uid,texto,fecha))
            print('Guardado correctamente')
        elif op in ('2','3'):
            with conexion() as c:
                filas = c.execute(f'SELECT id,{campo},fecha FROM {tabla} WHERE usuario_id=? ORDER BY fecha', (uid,)).fetchall()
            if not filas:
                print('No hay registros'); continue
            for id_, texto, fecha in filas:
                print(f'{id_}. {texto} - {datetime.strptime(fecha,"%Y-%m-%d %H:%M").strftime("%d/%m/%Y %H:%M")}')
            if op == '3':
                try: id_ = int(input('ID para eliminar: '))
                except ValueError:
                    print('ID incorrecto'); continue
                with conexion() as c:
                    cur = c.execute(f'DELETE FROM {tabla} WHERE id=? AND usuario_id=?', (id_,uid))
                print('Eliminado' if cur.rowcount else 'No existe ese registro')
        else: print('Opcion incorrecta')

def plan_diario(uid):
    print('\n=== PLAN DIARIO ORIENTATIVO ===')
    hora = input('Hora de inicio (HH:MM, Enter = 09:00): ').strip() or '09:00'
    try:
        inicio = datetime.strptime(hora, '%H:%M')
    except ValueError:
        print('Hora incorrecta'); return
    with conexion() as c:
        tareas = c.execute('SELECT titulo,prioridad,minutos FROM tareas WHERE usuario_id=? AND completada=0 ORDER BY prioridad,id', (uid,)).fetchall()
        eventos = c.execute('SELECT titulo,fecha FROM eventos WHERE usuario_id=? AND substr(fecha,1,10)=? ORDER BY fecha', (uid,date.today().isoformat())).fetchall()
    if not tareas: print('No tienes tareas pendientes')
    for titulo, prioridad, minutos in tareas:
        fin = inicio + timedelta(minutes=minutos)
        print(f'{inicio:%H:%M}-{fin:%H:%M} | {titulo} (prioridad {prioridad})')
        inicio = fin + timedelta(minutes=10)
    if eventos:
        print('\nEventos de hoy (revisa si coinciden con tu plan):')
        for titulo, fecha in eventos: print(f'{fecha[11:]} | {titulo}')
    print('Plan orientativo: no evita automaticamente los solapamientos con eventos.')

def avisos(uid):
    with conexion() as c:
        filas = c.execute('SELECT texto,fecha FROM recordatorios WHERE usuario_id=? AND fecha<=? ORDER BY fecha', (uid,datetime.now().strftime('%Y-%m-%d %H:%M'))).fetchall()
    if filas:
        print('\nRecordatorios vencidos o pendientes:')
        for texto, fecha in filas: print(f'- {texto} ({fecha})')

def main():
    iniciar_bd()
    uid = iniciar_usuario()
    if uid is None: return
    while True:
        print('\n===== TIMEWISE =====\n1. Gestionar tareas\n2. Gestionar eventos\n3. Ver plan diario\n4. Gestionar recordatorios\n5. Ver avisos pendientes\n6. Salir')
        op = input('Opcion: ').strip()
        if op == '1': menu_tareas(uid)
        elif op == '2': menu_fechas(uid,'eventos')
        elif op == '3': plan_diario(uid)
        elif op == '4': menu_fechas(uid,'recordatorios')
        elif op == '5': avisos(uid)
        elif op == '6':
            print('Hasta pronto'); break
        else: print('Opcion incorrecta')

if __name__ == '__main__':
    main()
