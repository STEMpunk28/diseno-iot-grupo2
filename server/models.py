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
    msg_id = IdentityField()
    packet_id = IntegerField()
    device_id = ForeignKeyField(Dev)
    protocol_id = IntegerField()
    transport_layer = IntegerField()
    length = IntegerField()

class Data(BaseModel):
    data_id = IdentityField()
    packet_id = ForeignKeyField(Log)
    timestamp = IntegerField()
    batt_level = IntegerField()
    temp = IntegerField()
    press = IntegerField()
    hum = IntegerField()
    co = FloatField()
    amp_x = FloatField()
    amp_y = FloatField()
    amp_z = FloatField()
    fre_x = FloatField()
    fre_y = FloatField()
    fre_z = FloatField()
    rms = FloatField()
    acc_x = ArrayField(FloatField)
    acc_y = ArrayField(FloatField)
    acc_z = ArrayField(FloatField)
    gyr_x = ArrayField(FloatField)
    gyr_y = ArrayField(FloatField)
    gyr_z = ArrayField(FloatField)

class Conf(BaseModel):
    protocol = IntegerField()
    transport_layer = IntegerField()

# Se crean las tablas
db.create_tables([Dev, Log, Data, Conf])