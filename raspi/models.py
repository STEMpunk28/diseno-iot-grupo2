from playhouse.postgres_ext import *

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
db = PostgresqlExtDatabase(**db_config)

class BaseModel(Model):
    class Meta:
        database = db

# Se definen los modelos        
class Dev(BaseModel):
    device_id = IdentityField()
    mac_adress = CharField()

class Log(BaseModel):
    packet_id = IdentityField()
    device_mac = CharField()
    msg_id = IntegerField()
    protocol_id = IntegerField()
    connection_type = IntegerField()
    length = IntegerField()

class Data(BaseModel):
    packet_id = ForeignKeyField(Log)
    timestamp = IntegerField()
    batt_level = IntegerField(null = True)
    temp = IntegerField(null = True)
    press = IntegerField(null = True)
    hum = IntegerField(null = True)
    co = FloatField(null = True)
    amp_x = FloatField(null = True)
    amp_y = FloatField(null = True)
    amp_z = FloatField(null = True)
    fre_x = FloatField(null = True)
    fre_y = FloatField(null = True)
    fre_z = FloatField(null = True)
    rms = FloatField(null = True)

class Conf(BaseModel):
    protocol = IntegerField()
    connection = IntegerField()

# Se crean las tablas
db.create_tables([Dev, Log, Data, Conf])
Conf.insert(protocol=0, transport_layer=0).execute()