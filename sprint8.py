from datetime import datetime, date
import logging
import sqlite3

#Logging
logging.basicConfig(
    filename="clinica_veterinaria.log",
    encoding='utf-8',
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#Clases de Utilidad para Consola
class UIUtils:
    """Clase estática para utilidades de interfaz de usuario en consola."""
    @staticmethod
    def print_title(text):
        print("\n" + "=" * 60)
        print(f"{text.center(60)}")
        print("=" * 60 + "\n")

    @staticmethod
    def print_message(text):
        print("\n * " + text)

    @staticmethod
    def get_int_input(prompt, error_msg="Entrada inválida. Por favor, ingrese un número."):
        """Solicita una entrada entera al usuario con manejo de errores."""
        while True:
            try:
                value = int(input(prompt))
                return value
            except ValueError:
                print(error_msg)
                logging.error(f"Entrada no numérica: '{prompt.strip()}'")

    @staticmethod
    def get_date_input(prompt, error_msg="Formato de fecha incorrecto. Use dd-mm-aaaa. Ejemplo: 05-06-2025."):
        """Solicita una fecha al usuario en formato dd-mm-aaaa con manejo de errores."""
        while True:
            date_str = input(prompt).strip()
            try:
                return datetime.strptime(date_str, "%d-%m-%Y").date()
            except ValueError:
                print(error_msg)
                logging.error(f"Formato de fecha inválido: '{date_str}'")

    @staticmethod
    def confirm_action(prompt):
        """Solicita confirmación al usuario para una acción."""
        while True:
            confirm = input(prompt + " (s/n): ").strip().lower()
            if confirm in ['s', 'n']:
                return confirm == 's'
            else:
                print("Respuesta inválida. Por favor, ingrese 's' o 'n'.")


#Clases Mascota, Propietario, Consulta
class Propietario:
    def __init__(self, nombre, telefono, direccion, id=None):
        self.id = id
        self.nombre = nombre
        self.telefono = telefono
        self.direccion = direccion

    def __str__(self):
        return (
            f"ID Propietario: {self.id}\n"
            f"Nombre: {self.nombre}\n"
            f"Teléfono: {self.telefono}\n"
            f"Dirección: {self.direccion}"
        )

class Mascota:
    def __init__(self, nombre, especie, raza, edad, propietario_id, id=None, propietario_nombre=None):
        self.id = id
        self.nombre = nombre
        self.especie = especie
        self.raza = raza
        self.edad = edad
        self.propietario_id = propietario_id
        self.propietario_nombre = propietario_nombre

    def __str__(self):
        propietario_display = self.propietario_nombre if self.propietario_nombre else f"ID Propietario: {self.propietario_id}"
        return (
            f"ID Mascota: {self.id}\n"
            f"Nombre: {self.nombre}\n"
            f"Especie: {self.especie}\n"
            f"Raza: {self.raza}\n"
            f"Edad: {self.edad} años\n"
            f"Propietario: {propietario_display}"
        )

class Consulta:
    def __init__(self, fecha, motivo, diagnostico, mascota_id, id=None, mascota_nombre=None):
        self.id = id
        if isinstance(fecha, date):
            self.fecha = fecha
        elif isinstance(fecha, str):
            try:
                self.fecha = datetime.strptime(fecha, "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Formato de fecha de la cadena incorrecto. Esperado YYYY-MM-DD.")
        else:
            raise ValueError("El argumento 'fecha' debe ser una cadena (YYYY-MM-DD) o un objeto datetime.date")
        self.motivo = motivo
        self.diagnostico = diagnostico
        self.mascota_id = mascota_id
        self.mascota_nombre = mascota_nombre

    def __str__(self):
        return (
            f"ID Consulta: {self.id}\n"
            f"Fecha: {self.fecha.strftime('%d-%m-%Y')}\n"
            f"Motivo: {self.motivo}\n"
            f"Diagnóstico: {self.diagnostico}\n"
            f"Mascota: {self.mascota_nombre if self.mascota_nombre else f'ID Mascota: {self.mascota_id}'}"
        )

#Gestor SQLite
class DatabaseManager:
    def __init__(self, db_name="clinica_veterinaria.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            logging.info(f"Conexión a la base de datos {self.db_name} establecida.")
        except sqlite3.Error as e:
            logging.error(f"Error al conectar a la base de datos: {e}")
            print(f"Error al conectar a la base de datos: {e}")

    def close_connection(self):
        if self.conn:
            self.conn.close()
            logging.info(f"Conexión a la base de datos {self.db_name} cerrada.")

    def create_tables(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS propietarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL UNIQUE,
                    telefono TEXT,
                    direccion TEXT
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS mascotas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre TEXT NOT NULL,
                    especie TEXT,
                    raza TEXT,
                    edad INTEGER,
                    id_propietario INTEGER,
                    FOREIGN KEY (id_propietario) REFERENCES propietarios(id) ON DELETE CASCADE
                )
            """)
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS consultas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT NOT NULL,
                    motivo TEXT,
                    diagnostico TEXT,
                    id_mascota INTEGER,
                    FOREIGN KEY (id_mascota) REFERENCES mascotas(id) ON DELETE CASCADE
                )
            """)
            self.conn.commit()
            logging.info("Tablas creadas o ya existentes.")
        except sqlite3.Error as e:
            logging.error(f"Error al crear tablas: {e}")
            print(f"Error al crear tablas: {e}")

    #CRUD Propietario
    def insert_propietario(self, propietario):
        try:
            self.cursor.execute(
                "INSERT INTO propietarios (nombre, telefono, direccion) VALUES (?, ?, ?)",
                (propietario.nombre, propietario.telefono, propietario.direccion)
            )
            self.conn.commit()
            propietario.id = self.cursor.lastrowid
            logging.info(f"Propietario '{propietario.nombre}' insertado con ID: {propietario.id}")
            return propietario
        except sqlite3.IntegrityError:
            logging.warning(f"Intento de insertar propietario duplicado: {propietario.nombre}")
            return None
        except sqlite3.Error as e:
            logging.error(f"Error al insertar propietario: {e}")
            return None

    def get_propietario_by_nombre(self, nombre):
        try:
            self.cursor.execute("SELECT id, nombre, telefono, direccion FROM propietarios WHERE nombre LIKE ?", (nombre,))
            row = self.cursor.fetchone()
            if row:
                return Propietario(row[1], row[2], row[3], row[0])
            return None
        except sqlite3.Error as e:
            logging.error(f"Error al buscar propietario por nombre: {e}")
            return None

    def get_propietario_by_id(self, propietario_id):
        try:
            self.cursor.execute("SELECT id, nombre, telefono, direccion FROM propietarios WHERE id = ?", (propietario_id,))
            row = self.cursor.fetchone()
            if row:
                return Propietario(row[1], row[2], row[3], row[0])
            return None
        except sqlite3.Error as e:
            logging.error(f"Error al buscar propietario por ID: {e}")
            return None

    def get_all_propietarios(self):
        try:
            self.cursor.execute("SELECT id, nombre, telefono, direccion FROM propietarios")
            rows = self.cursor.fetchall()
            return [Propietario(row[1], row[2], row[3], row[0]) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"Error al obtener todos los propietarios: {e}")
            return []

    def update_propietario(self, propietario_id, new_data):
        try:
            set_clause = ", ".join([f"{k} = ?" for k in new_data.keys()])
            values = list(new_data.values())
            values.append(propietario_id)
            self.cursor.execute(f"UPDATE propietarios SET {set_clause} WHERE id = ?", tuple(values))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al actualizar propietario: {e}")
            return False

    def delete_propietario(self, propietario_id):
        try:
            self.cursor.execute("DELETE FROM propietarios WHERE id = ?", (propietario_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al eliminar propietario: {e}")
            return False

    #CRUD Mascota
    def insert_mascota(self, mascota):
        try:
            self.cursor.execute(
                "INSERT INTO mascotas (nombre, especie, raza, edad, id_propietario) VALUES (?, ?, ?, ?, ?)",
                (mascota.nombre, mascota.especie, mascota.raza, mascota.edad, mascota.propietario_id)
            )
            self.conn.commit()
            mascota.id = self.cursor.lastrowid
            logging.info(f"Mascota '{mascota.nombre}' insertada con ID: {mascota.id}")
            return mascota
        except sqlite3.Error as e:
            logging.error(f"Error al insertar mascota: {e}")
            return None

    def get_all_mascotas(self):
        try:
            self.cursor.execute("""
                SELECT m.id, m.nombre, m.especie, m.raza, m.edad, m.id_propietario, p.nombre
                FROM mascotas m
                JOIN propietarios p ON m.id_propietario = p.id
            """)
            rows = self.cursor.fetchall()
            return [Mascota(row[1], row[2], row[3], row[4], row[5], row[0], row[6]) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"Error al obtener todas las mascotas: {e}")
            return []

    def get_mascota_by_id(self, mascota_id):
        try:
            self.cursor.execute("""
                SELECT m.id, m.nombre, m.especie, m.raza, m.edad, m.id_propietario, p.nombre
                FROM mascotas m
                JOIN propietarios p ON m.id_propietario = p.id
                WHERE m.id = ?
            """, (mascota_id,))
            row = self.cursor.fetchone()
            if row:
                return Mascota(row[1], row[2], row[3], row[4], row[5], row[0], row[6])
            return None
        except sqlite3.Error as e:
            logging.error(f"Error al buscar mascota por ID: {e}")
            return None

    def update_mascota(self, mascota_id, new_data):
        try:
            set_clause = ", ".join([f"{k} = ?" for k in new_data.keys()])
            values = list(new_data.values())
            values.append(mascota_id)
            self.cursor.execute(f"UPDATE mascotas SET {set_clause} WHERE id = ?", tuple(values))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al actualizar mascota: {e}")
            return False

    def delete_mascota(self, mascota_id):
        try:
            self.cursor.execute("DELETE FROM mascotas WHERE id = ?", (mascota_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al eliminar mascota: {e}")
            return False

    #CRUD Consulta
    def insert_consulta(self, consulta):
        try:
            self.cursor.execute(
                "INSERT INTO consultas (fecha, motivo, diagnostico, id_mascota) VALUES (?, ?, ?, ?)",
                (consulta.fecha.strftime("%Y-%m-%d"),
                 consulta.motivo, consulta.diagnostico, consulta.mascota_id)
            )
            self.conn.commit()
            consulta.id = self.cursor.lastrowid
            logging.info(f"Consulta para mascota ID {consulta.mascota_id} registrada con ID: {consulta.id}")
            return consulta
        except sqlite3.Error as e:
            logging.error(f"Error al insertar consulta: {e}")
            return None

    def get_consultas_by_mascota_id(self, mascota_id):
        try:
            self.cursor.execute("""
                SELECT c.id, c.fecha, c.motivo, c.diagnostico, c.id_mascota, m.nombre
                FROM consultas c
                JOIN mascotas m ON c.id_mascota = m.id
                WHERE c.id_mascota = ?
                ORDER BY c.fecha DESC
            """, (mascota_id,))
            rows = self.cursor.fetchall()
            return [Consulta(row[1], row[2], row[3], row[4], row[0], row[5]) for row in rows]
        except sqlite3.Error as e:
            logging.error(f"Error al obtener consultas por ID de mascota: {e}")
            return []

    def get_consulta_by_id(self, consulta_id):
        try:
            self.cursor.execute("""
                SELECT c.id, c.fecha, c.motivo, c.diagnostico, c.id_mascota, m.nombre
                FROM consultas c
                JOIN mascotas m ON c.id_mascota = m.id
                WHERE c.id = ?
            """, (consulta_id,))
            row = self.cursor.fetchone()
            if row:
                return Consulta(row[1], row[2], row[3], row[4], row[0], row[5])
            return None
        except sqlite3.Error as e:
            logging.error(f"Error al buscar consulta por ID: {e}")
            return None

    def update_consulta(self, consulta_id, new_data):
        try:
            if 'fecha' in new_data and isinstance(new_data['fecha'], date):
                new_data['fecha'] = new_data['fecha'].strftime("%Y-%m-%d")

            set_clause = ", ".join([f"{k} = ?" for k in new_data.keys()])
            values = list(new_data.values())
            values.append(consulta_id)
            self.cursor.execute(f"UPDATE consultas SET {set_clause} WHERE id = ?", tuple(values))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al actualizar consulta: {e}")
            return False

    def delete_consulta(self, consulta_id):
        try:
            self.cursor.execute("DELETE FROM consultas WHERE id = ?", (consulta_id,))
            self.conn.commit()
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logging.error(f"Error al eliminar consulta: {e}")
            return False

#Sistema Principal de la Veterinaria
class SistemaVeterinaria:
    def __init__(self):
        self.db_manager = DatabaseManager()

    def _get_propietario_or_create(self, owner_name):
        """Intenta obtener un propietario por nombre; si no existe, ofrece crearlo."""
        propietario = self.db_manager.get_propietario_by_nombre(owner_name)
        if not propietario:
            UIUtils.print_message(f"El propietario '{owner_name}' no está registrado.")
            if UIUtils.confirm_action("¿Desea registrarlo ahora?"):
                nombre = input("Nombre del NUEVO dueño: ").strip() # Podría ser diferente si el usuario se equivocó
                propietario_existente = self.db_manager.get_propietario_by_nombre(nombre)
                if propietario_existente:
                    print(f"El propietario '{nombre}' ya existe. Asignando mascota a este propietario.")
                    return propietario_existente
                telefono = input("Teléfono del NUEVO dueño: ")
                direccion = input("Dirección del NUEVO dueño: ")
                propietario = Propietario(nombre, telefono, direccion)
                propietario_registrado = self.db_manager.insert_propietario(propietario)
                if propietario_registrado:
                    print("Dueño registrado con éxito.")
                    logging.info(f"Dueño: {propietario_registrado.nombre} (ID: {propietario_registrado.id}) registrado.")
                return propietario_registrado
            else:
                UIUtils.print_message("Operación cancelada. Propietario no encontrado ni registrado.")
                logging.info("Registro de mascota/operación cancelada: propietario no encontrado/registrado.")
                return None
        return propietario

    def _get_mascota(self, prompt="Ingrese el ID de la mascota: "):
        """Solicita el ID de una mascota y la devuelve si existe."""
        mascota_id = UIUtils.get_int_input(prompt, "ID de mascota inválido.")
        mascota = self.db_manager.get_mascota_by_id(mascota_id)
        if not mascota:
            UIUtils.print_message(f"No se encontró ninguna mascota con el ID: {mascota_id}.")
            logging.info(f"Mascota con ID {mascota_id} no encontrada.")
        return mascota

    def _get_propietario(self, prompt="Ingrese el ID del propietario: "):
        """Solicita el ID de un propietario y lo devuelve si existe."""
        propietario_id = UIUtils.get_int_input(prompt, "ID de propietario inválido.")
        propietario = self.db_manager.get_propietario_by_id(propietario_id)
        if not propietario:
            UIUtils.print_message(f"No se encontró ningún propietario con el ID: {propietario_id}.")
            logging.info(f"Propietario con ID {propietario_id} no encontrado.")
        return propietario

    def _get_consulta(self, prompt="Ingrese el ID de la consulta: "):
        """Solicita el ID de una consulta y la devuelve si existe."""
        consulta_id = UIUtils.get_int_input(prompt, "ID de consulta inválido.")
        consulta = self.db_manager.get_consulta_by_id(consulta_id)
        if not consulta:
            UIUtils.print_message(f"No se encontró ninguna consulta con el ID: {consulta_id}.")
            logging.info(f"Consulta con ID {consulta_id} no encontrada.")
        return consulta

    def registrar_mascota(self):
        UIUtils.print_title("Registrar Mascota")
        nombre_mascota = input("Nombre de la mascota: ")
        especie_mascota = input("Especie de la mascota: ")
        raza_mascota = input("Raza de la mascota: ")
        edad_mascota = UIUtils.get_int_input("Edad de la mascota en años: ")
        while edad_mascota < 0:
            print("La edad no puede ser negativa.")
            edad_mascota = UIUtils.get_int_input("Edad de la mascota en años: ")

        UIUtils.print_message("--- Información del Propietario ---")
        nombre_propietario = input("Ingrese el nombre del dueño existente o nuevo: ").strip()
        propietario = self._get_propietario_or_create(nombre_propietario)

        if not propietario:
            return # Se canceló el registro del propietario o no se pudo crear.

        mascota = Mascota(nombre_mascota, especie_mascota, raza_mascota, edad_mascota, propietario.id)
        mascota_registrada = self.db_manager.insert_mascota(mascota)
        if mascota_registrada:
            print(f"\n - Mascota '{mascota_registrada.nombre}' registrada con ID: {mascota_registrada.id}, del dueño: {propietario.nombre}.")
            logging.info(f"Mascota: {mascota_registrada.nombre} (ID: {mascota_registrada.id}), del dueño: {propietario.nombre} (ID: {propietario.id}) registrada.")
        else:
            UIUtils.print_message("No se pudo registrar la mascota. Intente nuevamente.")

    def registrar_consulta(self):
        UIUtils.print_title("Registro de Consulta")
        mascota = self._get_mascota("Ingrese el ID de la mascota para la consulta: ")
        if not mascota:
            return

        print(f"Registrando consulta para: {mascota.nombre} (ID: {mascota.id})")
        fecha = UIUtils.get_date_input("Fecha de la consulta (dd-mm-aaaa): ")
        motivo = input("Motivo de la consulta: ")
        diagnostico = input("Diagnóstico: ")

        consulta = Consulta(fecha, motivo, diagnostico, mascota.id)
        consulta_registrada = self.db_manager.insert_consulta(consulta)
        if consulta_registrada:
            print("Consulta registrada con éxito.")
            logging.info(f"Consulta (ID: {consulta_registrada.id}) de la mascota: {mascota.nombre} (ID: {mascota.id}) registrada.")
        else:
            UIUtils.print_message("No se pudo registrar la consulta.")

    def listar_propietarios(self):
        UIUtils.print_title("Lista de Propietarios")
        propietarios = self.db_manager.get_all_propietarios()
        if not propietarios:
            UIUtils.print_message("No existen propietarios registrados.")
            logging.info("Lista de propietarios consultada: No hay registros.")
            return

        for prop in propietarios:
            print(prop)
            print("-" * 30)
        logging.info("Propietarios registrados consultados.")

    def listar_mascotas(self):
        UIUtils.print_title("Lista de Mascotas Registradas")
        mascotas = self.db_manager.get_all_mascotas()
        if not mascotas:
            UIUtils.print_message("No existen mascotas registradas.")
            logging.info("Lista de mascotas consultada: No hay registros.")
            return

        for mascota in mascotas:
            print(mascota)
            print("-" * 30)
        logging.info("Mascotas registradas consultadas.")

    def historia_clinica(self):
        UIUtils.print_title("Historia Clínica")
        mascota = self._get_mascota("Ingrese el ID de la mascota para ver su historial: ")
        if not mascota:
            return

        consultas = self.db_manager.get_consultas_by_mascota_id(mascota.id)
        if not consultas:
            UIUtils.print_message(f"No hay consultas registradas para {mascota.nombre} (ID: {mascota.id}).")
            logging.info(f"No se encontraron consultas para la mascota ID: {mascota.id}.")
            return

        print(f"\nHistorial clínico de {mascota.nombre} (ID: {mascota.id}):")
        for consulta in consultas:
            print(consulta)
            print("-" * 30)
        logging.info(f"Historia clínica de la mascota ID: {mascota.id} consultada.")

    def actualizar_propietario(self):
        UIUtils.print_title("Actualizar Propietario")
        propietario = self._get_propietario("Ingrese el ID del propietario a actualizar: ")
        if not propietario:
            return

        print(f"\nPropietario actual: {propietario}")
        print("\nIngrese los nuevos datos (deje en blanco para mantener el actual):")
        new_data = {}

        nombre = input(f"Nuevo nombre ({propietario.nombre}): ").strip()
        if nombre:
            existente = self.db_manager.get_propietario_by_nombre(nombre)
            if existente and existente.id != propietario.id:
                print(f"Error: El nombre '{nombre}' ya está siendo usado por otro propietario (ID: {existente.id}).")
                logging.warning(f"Intento de actualizar propietario ID {propietario.id} a nombre duplicado: {nombre}")
                return
            new_data['nombre'] = nombre

        telefono = input(f"Nuevo teléfono ({propietario.telefono}): ").strip()
        if telefono:
            new_data['telefono'] = telefono

        direccion = input(f"Nueva dirección ({propietario.direccion}): ").strip()
        if direccion:
            new_data['direccion'] = direccion

        if new_data:
            if self.db_manager.update_propietario(propietario.id, new_data):
                print("Propietario actualizado con éxito.")
                logging.info(f"Propietario ID {propietario.id} actualizado.")
            else:
                UIUtils.print_message("No se pudo actualizar el propietario.")
        else:
            UIUtils.print_message("No se ingresaron datos para actualizar.")

    def actualizar_mascota(self):
        UIUtils.print_title("Actualizar Mascota")
        mascota = self._get_mascota("Ingrese el ID de la mascota a actualizar: ")
        if not mascota:
            return

        print(f"\nMascota actual: {mascota}")
        print("\nIngrese los nuevos datos (deje en blanco para mantener el actual):")
        new_data = {}

        nombre = input(f"Nuevo nombre ({mascota.nombre}): ").strip()
        if nombre:
            new_data['nombre'] = nombre

        especie = input(f"Nueva especie ({mascota.especie}): ").strip()
        if especie:
            new_data['especie'] = especie

        raza = input(f"Nueva raza ({mascota.raza}): ").strip()
        if raza:
            new_data['raza'] = raza

        edad_str = input(f"Nueva edad en años ({mascota.edad}): ").strip()
        if edad_str:
            try:
                edad = int(edad_str)
                if edad < 0:
                    raise ValueError
                new_data['edad'] = edad
            except ValueError:
                print("Edad inválida. Se mantendrá la edad actual.")
                logging.warning(f"Intento de actualizar edad de mascota {mascota.id} con valor inválido: '{edad_str}'")

        if UIUtils.confirm_action("¿Desea cambiar el propietario de esta mascota?"):
            nombre_nuevo_propietario = input("Ingrese el nombre del nuevo propietario: ").strip()
            nuevo_propietario = self.db_manager.get_propietario_by_nombre(nombre_nuevo_propietario)
            if nuevo_propietario:
                new_data['id_propietario'] = nuevo_propietario.id
                print(f"Propietario de la mascota cambiado a: {nuevo_propietario.nombre}.")
            else:
                UIUtils.print_message("Propietario no encontrado. No se cambió el propietario.")
                logging.warning(f"Intento de cambiar propietario de mascota {mascota.id} a uno no existente: {nombre_nuevo_propietario}")

        if new_data:
            if self.db_manager.update_mascota(mascota.id, new_data):
                print("Mascota actualizada con éxito.")
                logging.info(f"Mascota ID {mascota.id} actualizada.")
            else:
                UIUtils.print_message("No se pudo actualizar la mascota.")
        else:
            UIUtils.print_message("No se ingresaron datos para actualizar.")

    def actualizar_consulta(self):
        UIUtils.print_title("Actualizar Consulta")
        consulta = self._get_consulta("Ingrese el ID de la consulta a actualizar: ")
        if not consulta:
            return

        print(f"\nConsulta actual (Mascota: {consulta.mascota_nombre}): {consulta}")
        print("\nIngrese los nuevos datos (deje en blanco para mantener el actual):")
        new_data = {}

        fecha_str = input(f"Nueva fecha (dd-mm-aaaa) ({consulta.fecha.strftime('%d-%m-%Y')}): ").strip()
        if fecha_str:
            try:
                new_data['fecha'] = datetime.strptime(fecha_str, "%d-%m-%Y").date()
            except ValueError:
                print("Formato de fecha incorrecto. Se mantendrá la fecha actual.")
                logging.warning(f"Intento de actualizar fecha de consulta {consulta.id} con formato inválido: {fecha_str}")

        motivo = input(f"Nuevo motivo ({consulta.motivo}): ").strip()
        if motivo:
            new_data['motivo'] = motivo

        diagnostico = input(f"Nuevo diagnóstico ({consulta.diagnostico}): ").strip()
        if diagnostico:
            new_data['diagnostico'] = diagnostico

        if new_data:
            if self.db_manager.update_consulta(consulta.id, new_data):
                print("Consulta actualizada con éxito.")
                logging.info(f"Consulta ID {consulta.id} actualizada.")
            else:
                UIUtils.print_message("No se pudo actualizar la consulta.")
        else:
            UIUtils.print_message("No se ingresaron datos para actualizar.")

    def eliminar_propietario(self):
        UIUtils.print_title("Eliminar Propietario")
        propietario = self._get_propietario("Ingrese el ID del propietario a eliminar: ")
        if not propietario:
            return

        if UIUtils.confirm_action(f"¿Está seguro de eliminar al propietario '{propietario.nombre}' (ID: {propietario.id})? Esto también eliminará SUS MASCOTAS y todas sus CONSULTAS."):
            if self.db_manager.delete_propietario(propietario.id):
                print("Propietario y sus datos asociados eliminados con éxito.")
                logging.info(f"Propietario ID {propietario.id} y datos asociados eliminados.")
            else:
                UIUtils.print_message("No se pudo eliminar el propietario.")
        else:
            print("Operación cancelada.")
            logging.info(f"Eliminación de propietario ID {propietario.id} cancelada.")

    def eliminar_mascota(self):
        UIUtils.print_title("Eliminar Mascota")
        mascota = self._get_mascota("Ingrese el ID de la mascota a eliminar: ")
        if not mascota:
            return

        if UIUtils.confirm_action(f"¿Está seguro de eliminar a la mascota '{mascota.nombre}' (ID: {mascota.id})? Esto también eliminará todas sus CONSULTAS."):
            if self.db_manager.delete_mascota(mascota.id):
                print("Mascota y sus consultas eliminadas con éxito.")
                logging.info(f"Mascota ID {mascota.id} y consultas asociadas eliminadas.")
            else:
                UIUtils.print_message("No se pudo eliminar la mascota.")
        else:
            print("Operación cancelada.")
            logging.info(f"Eliminación de mascota ID {mascota.id} cancelada.")

    def eliminar_consulta(self):
        UIUtils.print_title("Eliminar Consulta")
        consulta = self._get_consulta("Ingrese el ID de la consulta a eliminar: ")
        if not consulta:
            return

        if UIUtils.confirm_action(f"¿Está seguro de eliminar la consulta con ID: {consulta.id} para la mascota '{consulta.mascota_nombre}'?"):
            if self.db_manager.delete_consulta(consulta.id):
                print("Consulta eliminada con éxito.")
                logging.info(f"Consulta ID {consulta.id} eliminada.")
            else:
                UIUtils.print_message("No se pudo eliminar la consulta.")
        else:
            print("Operación cancelada.")
            logging.info(f"Eliminación de consulta ID {consulta.id} cancelada.")

# --- Función Principal del Programa ---
def main():
    logging.info("Se inició la aplicación")
    sistema = SistemaVeterinaria()
    try:
        while True:
            UIUtils.print_title("Sistema Veterinaria Amigos Peludos")

            print("Gestión de Registros")
            print("1. Registrar nueva mascota (incluye registro de propietario)")
            print("2. Registrar nueva consulta")
            print("Consultar Registros")
            print("3. Ver lista de propietarios")
            print("4. Ver lista de mascotas")
            print("5. Ver historia clínica de una mascota")
            print("Actualizar Registros")
            print("6. Actualizar propietario")
            print("7. Actualizar mascota")
            print("8. Actualizar consulta")
            print("Eliminar Registros")
            print("9. Eliminar propietario")
            print("10. Eliminar mascota")
            print("11. Eliminar consulta")
            print("12. Salir del sistema")

            UIUtils.print_message("Elija una opción: ")
            opcion = input("> ")

            if opcion == '1':
                sistema.registrar_mascota()
            elif opcion == '2':
                sistema.registrar_consulta()
            elif opcion == '3':
                sistema.listar_propietarios()
            elif opcion == '4':
                sistema.listar_mascotas()
            elif opcion == '5':
                sistema.historia_clinica()
            elif opcion == '6':
                sistema.actualizar_propietario()
            elif opcion == '7':
                sistema.actualizar_mascota()
            elif opcion == '8':
                sistema.actualizar_consulta()
            elif opcion == '9':
                sistema.eliminar_propietario()
            elif opcion == '10':
                sistema.eliminar_mascota()
            elif opcion == '11':
                sistema.eliminar_consulta()
            elif opcion == '12':
                print("¡Gracias por usar el sistema! Hasta luego.")
                logging.info("Se cerró la aplicación")
                break
            else:
                print("Opción inválida. Por favor, intente nuevamente.")
    except Exception as e:
        logging.critical(f"Ocurrió un error crítico inesperado: {e}", exc_info=True)
        print(f"Ocurrió un error inesperado: {e}")
        print("Por favor, revise el archivo de log para más detalles.")
    finally:
        sistema.db_manager.close_connection()

if __name__ == "__main__":
    main()