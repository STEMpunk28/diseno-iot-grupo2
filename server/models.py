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
    mac_adress = BigIntegerField()

class Log(BaseModel):
    msg_id = IntegerField()
    packet_id = IdentityField()
    device_id = ForeignKeyField(Dev)
    protocol_id = IntegerField()
    transport_layer = IntegerField()
    length = IntegerField()

class Data(BaseModel):
    data_id = IdentityField()
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
    acc_x = ArrayField(FloatField, null = True)
    acc_y = ArrayField(FloatField, null = True)
    acc_z = ArrayField(FloatField, null = True)
    gyr_x = ArrayField(FloatField, null = True)
    gyr_y = ArrayField(FloatField, null = True)
    gyr_z = ArrayField(FloatField, null = True)

class Conf(BaseModel):
    protocol = IntegerField()
    transport_layer = IntegerField()

# Se crean las tablas
db.create_tables([Dev, Log, Data, Conf])