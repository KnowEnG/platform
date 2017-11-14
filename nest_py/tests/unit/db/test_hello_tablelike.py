# -*- coding: utf-8 -*-
import os
import sys
import json

import nest_py.core.db.nest_db as nest_db
import nest_py.core.db.core_db as core_db
import nest_py.core.db.db_ops_utils as db_ops_utils
import nest_py.hello_world.data_types.hello_tablelike as hello_tablelike
from nest_py.hello_world.data_types.hello_tablelike import HelloTablelikeDTO

import nest_py.hello_world.db.hw_db as hw_db

from nest_py.ops.nest_sites import NestSite
from nest_py.nest_envs import ProjectEnv
from nest_py.core.db.sqla_resources import JobsSqlaResources
from nest_py.core.data_types.nest_user import NestUser
from nest_py.core.data_types.nest_id import NestId

def setup_db():
    #FIXME: use an isolated database 'nest_test'.
    #for now, these tests will create and delete 
    #data in the hello_world table(s)
    sqla_md = nest_db.get_global_sqlalchemy_metadata()
    hw_db.register_sqla_bindings(sqla_md)
    db_ops_utils.ensure_tables_in_db()
    return

def test_sqla_tablelike_lifecycle():
    """
    walks through making a table, making it in the database,
    making an entry, updating, etc, using the nest config
    way of setting things up and crud_db_client
    """
    setup_db()
    sqla_md = nest_db.get_global_sqlalchemy_metadata()
    db_engine = nest_db.get_global_sqlalchemy_engine()

    db_registry = hw_db.get_sqla_makers()
    for tbl_name in db_registry:
        print('db registry: ' + str(tbl_name))
    db_client = db_registry['hello_tablelike'].get_db_client(db_engine, sqla_md)
    sys_user = core_db.get_system_user()
    db_client.set_requesting_user(sys_user)

    db_client.delete_all_entries()

    print('testing create_entry')
    tle_orig = HelloTablelikeDTO(1.1, 2.2, 'x', ['a','a'], [0.0, 0.0], NestId(1), [NestId(4), NestId(2)], {'x':'innerx'}, 5, [6, 7]).to_tablelike_entry()
    print(str(tle_orig))
    tle_updated = db_client.create_entry(tle_orig)
    assert(not tle_updated is None)
    nid = tle_updated.get_nest_id()
    print('generated nid: ' + str(nid))
    assert(not nid is None)

    print('testing read_entry')
    tle_rt = db_client.read_entry(nid)
    print('tle_rt: ' + str(tle_rt))
    print('tle_updated: ' + str(tle_updated))
    assert(tle_rt == tle_updated)

    print('testing update_entry')
    tle_unupdated = tle_rt
    tle_unupdated.set_value('flt_val_0', 22.0)
    tle_updated = db_client.update_entry(tle_unupdated)
    tle_updated_rt = db_client.read_entry(nid)
    assert(tle_updated_rt == tle_updated)

    print('testing delete_entry')
    deleted_nid = db_client.delete_entry(nid)
    assert(deleted_nid == nid)
    fetched_deleted = db_client.read_entry(nid)
    assert(fetched_deleted is None)

    print('testing bulk_create_entries')
    t1 = HelloTablelikeDTO(3.0, 3.3, 'y', ['a','a'], [0.0, 0.0], NestId(5), [NestId(1), NestId(2)], {'x':'innerx'}, 5, [6, 7]).to_tablelike_entry()
    t2 = HelloTablelikeDTO(4.0, 4.4, 'y', ['a','b'], [0.0, 0.0], NestId(5), [NestId(1), NestId(2)], {'x':'innerx'}, 5, [6, 7]).to_tablelike_entry()
    t3 = HelloTablelikeDTO(5.0, 5.5, 'x', ['b','b'], [0.0, 0.0], NestId(5), [NestId(1), NestId(2)], {'x':'innerx'}, 5, [6, 7]).to_tablelike_entry()

    tles = [t1, t2, t3]
    up_tles = db_client.bulk_create_entries(tles, batch_size=2)
    assert(not up_tles is None)
    assert(len(up_tles) == len(tles))
    for (orig_tle, up_tle) in zip(tles, up_tles):
        nid = up_tle.get_nest_id()
        assert(not nid is None)
        rt_tle = db_client.read_entry(nid)
        assert(rt_tle == up_tle)
        for att in ['flt_val_0', 'flt_val_1', 'string_val']:
            assert(orig_tle.get_value(att) == rt_tle.get_value(att))

    print('testing bulk_create_entries_async and simple_filter_query')
    db_client.delete_all_entries()
    t1 = HelloTablelikeDTO(6.0, 6.6, 'x', ['b','b'], [0.0, 0.0], NestId(5), [NestId(1), NestId(2)], {'x':'innerx'}, 5, [6, 7]).to_tablelike_entry()
    t2 = HelloTablelikeDTO(7.0, 7.7, 'z', ['a','b'], [2.0, 0.0], NestId(5), [NestId(1), NestId(2)], {'x':'innerx'}, 5, [6, 7]).to_tablelike_entry()
    t3 = HelloTablelikeDTO(8.0, 8.8, 'z', ['b','a'], [0.0, 3.0], NestId(5), [NestId(1), NestId(2)], {'x':'innerx'}, 5, [6, 7]).to_tablelike_entry()
    tles = [t1, t2, t3]
    print('begin async upload')
    upload_count = db_client.bulk_create_entries_async(tles, batch_size=2)
    print('upload count returned: ' + str(upload_count))

    z_tles = db_client.simple_filter_query({'string_val':'z'})
    for z_tle in z_tles:
        nid = z_tle.get_nest_id()
        assert(not nid is None)
        z_tle.set_nest_id(None) #so we can test equivalence easier
    assert(len(z_tles) == 2)
    assert(t2 in z_tles)
    assert(t3 in z_tles)

    x_tles = db_client.simple_filter_query({'string_val':'x', 'flt_val_0':6.0})

    for x_tle in x_tles:
        nid = x_tle.get_nest_id()
        assert(not nid is None)
        x_tle.set_nest_id(None) #so we can test equivalence easier
    assert(len(x_tles) == 1)
    assert(t1 in x_tles)

    print("testing filter by json attribute. should work b/c it's string matching in the db")
    json_tles = db_client.simple_filter_query({'json_val':json.dumps({'x':'innerx'})})
    assert(len(json_tles) == 3)
#
#    print('testing ensure_entry')
#    tK = HelloTablelikeDTO(9.0, 9.9, 'z', ['b','a'], [0.0, 3.0], NestId(5), [NestId(1), NestId(2)], {u'x':u'innerx'}).to_tablelike_entry()
#    tk2 = db_client.ensure_entry(tK)
#    tk3 = db_client.ensure_entry(tK)
#    assert(tk2.get_nest_id() == tk3.get_nest_id())
#    
    db_client.get_sqla_connection().close()
    return


