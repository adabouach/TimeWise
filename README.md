# TimeWise

## Funcionalidades
- Registro e inicio de sesion
- Gestion de tareas y prioridades
- Gestion de eventos
- Recordatorios y consulta de avisos vencidos
- Plan diario orientativo con pausas de 10 minutos
- Persistencia local en SQLite

## Requisitos
Python 3.9 o posterior. No requiere librerias externas.

## Ejecucion
En la carpeta del proyecto:

```bash
python main.py
```

La base de datos `timewise.db` se crea automaticamente al iniciar la aplicacion.

## Limitaciones de la primera version
- No usa IA ni envia notificaciones del sistema.
- El plan ordena tareas por prioridad, pero no evita solapamientos con eventos.
- El almacenamiento de contrasenas es demostrativo; para un uso real se necesita un algoritmo de hash con sal como Argon2 o bcrypt.
