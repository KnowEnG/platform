import nest_py.hello_world.data_types.hello_tablelike as hello_tablelike
import nest_py.hello_world.data_types.hello_tablelike_sub as hello_tablelike_sub

def get_schemas():
    schemas = list()
    schemas.append(hello_tablelike.generate_schema())
    schemas.append(hello_tablelike_sub.generate_schema())
    return schemas

