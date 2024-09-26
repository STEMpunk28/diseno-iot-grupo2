from peewee import Model, PostgresqlDatabase, CharField

# Tabla con los tipos de fields que hay en peewee
# https://docs.peewee-orm.com/en/latest/peewee/models.html#fields

# Configuracion de la base de datos
db_config = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',
    'database': 'iot_db'
}
db = PostgresqlDatabase(**db_config)

class BaseModel(Model):
    class Meta:
        database = db

# Se definen los modelos        
class User(BaseModel):
    username = CharField()

class User(BaseModel):
    username = CharField()


# Se crean las tablas
db.create_tables([User])