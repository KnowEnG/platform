import traceback
import math
from sqlalchemy.sql import select, update, delete
from nest_py.core.data_types.nest_id import NestId
from nest_py.core.db.security_policy import SecurityException
from nest_py.core.db.security_policy import SecurityPolicy

class CrudDbClient(object):
    """
    The basic pattern: if a call fails for any reason, logs a detailed
    message and returns None. The exception is if the NestUser is
    unauthorized, then raises a NestSecurityException.

    If Create/Update/Delete commands succeed, normally returns just the NestId
    of the entry(ies) affected.

    If a Read command succeeds, returns the data payload parsed into
    dicts and lists, then to the actual data-type object by the abstract
    method jdata_to_object()
    """

    def __init__(self, sqla_engine, sqla_table, json_transcoder,
            security_policy=None):
        """
        sqla_engine(SQLAlchemy.Engine): configured against against
        a database and engine containing this object's table
        sqla_table(SQLAlchemy.Table) table representation
        json_transcoder(SqlaJsonTranscoder) converts to and from
        dictionaries that sqla uses
        security_policy(SecurityPolicy): provides rules for what
            users are allowed to operate on the data collection
            this client interacts with. If None, will use the
            default SecurityPolicy

        e.g. for http://localhost/api/foo/bar

        the http client is configured for server='localhost', port=80
        the eve_endpoint is 'foo/bar',
        and 'api' is configured in Eve config's URL_PREFIX and hard-coded
        to always be added by NestHttpClient
        """
        self.sqla_engine = sqla_engine
        self.sqla_table = sqla_table
        self.transcoder = json_transcoder
        self.requesting_user = None
        if security_policy is None:
            self.security_policy = SecurityPolicy()
        else:
            self.security_policy = security_policy
        return

    def _db_connection(self):
        return self.sqla_engine.connect()

    def get_collection_name(self):
        return self.sqla_table.name

    def set_requesting_user(self, user):
        """
        user (NestUser) default user that will own any created entries in a
        database table, and all queries will filter by this user's id by
        default. The individual CRUD operations have the ability to user a
        different user per-call, but if that is not specified, this is the user that
        will be used by default.
        """
        self.requesting_user = user
        return

    def _object_to_sqla_values(self, dto, user):
        """
        converts the dto we can handle using object_to_flat_jdata into
        a dictionary that is suitable for passing to sqla in an 
        insert command as the 'values'.
        call object_to_flat_jdata and then manages the special
        'id' field that is handled by the database,
        and adds the 'owner_id' field for the user who is making
        the call
        """
        flat_jdata = self.transcoder.object_to_flat_jdata(dto)
        #this also deletes 'id' from the dict
        id_val = flat_jdata.pop('id', None)
        if not id_val is None:
            raise Exception("Can't use 'create' on an \
                    object that already has a non-None id field. " +
                    " id was: " + str(id_val))
            #log('flat_jdata: ' + str(flat_jdata))

        #add the data's owner. currently required.
        if user is None:
            raise SecurityException("Can't save data with no owner")
        flat_jdata['owner_id'] = user.get_nest_id().get_value()
        return flat_jdata

    def _sqla_values_to_object(self, query_res, user, fields=None):
        flat_jdata = dict(query_res)
        #print('flat_jdata from sqla: ' + str(flat_jdata))
        obs_owner_id = flat_jdata.get('owner_id', None)
        no_owner = obs_owner_id is None
        owned_by_someone_else = not user.get_nest_id().get_value() == obs_owner_id
        allowed_to_read_anyones = self.security_policy.can_read_all_entries(user)
        if (no_owner or owned_by_someone_else) and not allowed_to_read_anyones:
            raise SecurityException('userid: ' + str(user.get_nest_id()) + 
                ' attempting to access row owned by userid: ' + 
                str(obs_owner_id))
        if fields is None:
            dto = self.transcoder.flat_jdata_to_object(flat_jdata)
        else:
            dto = flat_jdata
            #they specified fields, so we give them the id always but 
            #never the owner_id
            dto.pop('owner_id')
        return dto

    def create_entry(self, dto, user=None):
        """
        dto is an object of the type registered with SqlAlchemy to
        the table this client is pointed at
        """
        if user is None:
            user = self.requesting_user
        sqla_vals = self._object_to_sqla_values(dto, user)
        if not self.security_policy.can_write_entries(user):
            raise SecurityException('User not allowed to write')
        db_conn = self._db_connection()
        try:
            stmt = self.sqla_table.insert()
            db_res = db_conn.execute(stmt, sqla_vals)
            #not sure why the generated id comes back as a list
            generated_id = db_res.inserted_primary_key[0]
            #log("inserted_primary_key: " + str(generated_id))
            nid = NestId(generated_id) 
            dto.set_nest_id(nid)
            db_conn.close()
        except Exception as e:
            db_conn.close()
            traceback.print_exc()
            log("create_entry error from sqlalchemy")
            log("Exception: " + str(e))
            dto = None
        return dto
    
    def bulk_create_entries(self, dto_lst, user=None, batch_size=100):
        if user is None:
            user = self.requesting_user
        if not self.security_policy.can_write_entries(user):
            raise SecurityException('User not allowed to write')
        createds = list()
        for dto in dto_lst:
            c = self.create_entry(dto, user=user)
            if c is None:
                createds = None
                break
            else:
                createds.append(c)
        return createds

    def bulk_create_entries_async(self, dto_lst, user=None, batch_size=100):
        """
        uploads entries in batches. only returns the number that
        was uploaded. 
        
        TODO: currently can't return the dto's with
        the generated primary_keys like we would want b/c of this
        issue:
        https://bitbucket.org/zzzeek/sqlalchemy/issues/2613/batch-insert-with-returning-specified-is
        """
        if user is None:
            user = self.requesting_user
        if not self.security_policy.can_write_entries(user):
            raise SecurityException('User not allowed to write')
        dto_batches = self._split_to_batches(dto_lst, batch_size)
        total_count = len(dto_lst)
        num_done = 0
        db_conn = self._db_connection()
        try:
            for dto_batch in dto_batches:
                sqla_vals_batch = \
                    [self._object_to_sqla_values(dto, user) for dto in dto_batch]
                tbl = self.sqla_table
                #log('sqlv_batch: ' + str(sqla_vals_batch))
                stmt = tbl.insert()
                db_res = db_conn.execute(stmt, sqla_vals_batch)
                num_done += len(sqla_vals_batch)
                log('batch uploaded entries: ' + str(num_done) + '/' + 
                    str(total_count))
            db_conn.close()
        except Exception as e:
            db_conn.close()
            #TODO: make the bulk writes in a single transaction
            #and roll it back if there is an error part way through
            traceback.print_exc()
            log("bulk_create_entries error from sqlalchemy")
            log("Exception: " + str(e))
            num_done = None
        return num_done

    def read_entry(self, nest_id, user=None):
        """

        nest_id(NestId): nest_id of the entry we want to fetch
        """
        if user is None:
            user = self.requesting_user
        nid = nest_id.get_value()
        tbl = self.sqla_table
        stmt = select([tbl]).where(tbl.c['id'] == nid)
        db_conn = self._db_connection()
        try:
            res = db_conn.execute(stmt).fetchone()
            #log('read entry: ' + str(res))
            if res is None:
                dto = None
            else:
                dto = self._sqla_values_to_object(res, user)
            db_conn.close()
        except Exception as e:
            dto = None
            db_conn.close()
        return dto

    def paged_filter_query(self, filter_params, user=None, 
        results_per_page=100, page_num=1, fields=None, sort_fields=None):
        """
        TODO: Hopefully this can be much more efficient, but needing
        to get the total number of possible results makes it
        not straightforward.
        """
        if user is None:
            user = self.requesting_user
        if results_per_page is None:
            results_per_page = 100
        if page_num is None:
            page_num = 1

        found_dtos = self.simple_filter_query(filter_params, 
            user=user, fields=fields, sort_fields=sort_fields)
        if found_dtos is None:
            res = None
        else:
            res = dict()
            page_dtos = list()
            offset = (page_num - 1) * results_per_page 
            end = offset + results_per_page
            if end > len(found_dtos):
                end = len(found_dtos)
            for i in range(offset, end):
                page_dtos.append(found_dtos[i])
            res['items'] = page_dtos
            total_available = len(found_dtos)
            num_items = len(page_dtos)
            last_page = int(math.ceil(float(total_available) / float(results_per_page)))
            res['total_available'] = total_available
            res['num_items'] = num_items
            res['last_page'] = last_page
            res['page'] = page_num
        return res
        
    def simple_filter_query(self, filter_params, user=None, fields=None,
        sort_fields=None):
        """
        values in filter params can be a single primitive, or a list.
        if it's a list, any entry that matches any one of the values
        in the list will match

        if 'fields' is a list of fieldnames (not None), will return a list
            of dicts with only those attributes, not a list of objects

        sort_fields: list of column names to sort by. currently always in
            ascending order. Note that whatever the list of fields is,
            the '_id' field will be added as a final field to sort by.
            Therefore '_id' is also the default ordering. '_id' is
            essentially the order the entries were added to the database
            b/c of the current implementation.
        """
        if user is None:
            user = self.requesting_user
        #log('crud_db_client.simple_filter_query using user: ' + str(user.get_username()) + ' : ' + str(user.get_nest_id()))
        tbl = self.sqla_table
        db_conn = self._db_connection()
        try:
            #only return requested fields, or all columns in 
            #table if returning whole objects
            if fields is None:
                stmt = select([tbl])
            else:
                self._validate_fields_for_table(fields)
                stmt = select([tbl.c.id, tbl.c.owner_id]) #always include the primary key
                for fieldname in fields:
                    #print('adding projection field: ' + str(fieldname))
                    stmt = stmt.column(tbl.c[fieldname])

            #only give users back data they created if can't read all
            if not self.security_policy.can_read_all_entries(user):
                owner_id = user.get_nest_id().get_value()
                stmt = stmt.where(tbl.c.owner_id == owner_id)

            filter_params = self._nest_ids_to_ints(filter_params)
            #apply matching filters using 'where' clauses
            self._validate_fields_for_table(filter_params.keys())
            for k in filter_params:
                #if a list was given for the field's value in the filter, an entry
                #whose value is any value in that list will match
                #print('filter param [' + str(k) + '] is : ' + str(filter_params[k]))
                col_type = self.sqla_table.c[k].type
                if str(col_type) == 'JSONB':
                    stmt = stmt.where(tbl.c[k].contains(filter_params[k]))
                else:
                    if isinstance(filter_params[k], list):
                        stmt = stmt.where(tbl.c[k].in_(filter_params[k]))
                    else:
                        stmt = stmt.where(tbl.c[k] == filter_params[k])

            #apply requested sort order
            if sort_fields is not None:
                self._validate_fields_for_table(sort_fields)
                for fieldname in sort_fields:
                    stmt = stmt.order_by(tbl.c[fieldname])
            #always sort by _id as the final criteria
            stmt = stmt.order_by(tbl.c['id'])

            #print('final query: ' + str(stmt))
            res = db_conn.execute(stmt).fetchall()
            found_dtos = list()
            for sqla_row in res:
                dto = self._sqla_values_to_object(sqla_row, user, fields=fields) 
                #log('as dto: ' + str(dto))
                found_dtos.append(dto)
            db_conn.close()
        except Exception as e:
            db_conn.close()
            log('Error in simple_filter_query: ' + str(e))
            traceback.print_exc()
            raise e
            #found_dtos = None
        return found_dtos

    def _validate_fields_for_table(self, fields):
        """
        validates that the given list of fields all map to columns
        in this CrudDbClient's Postgres table. If not, raises an
        exception with a user-centric error message (suitable for
        the API to show a user).
        """
        bad_fields = list()
        for f in fields:
            if not f in self.sqla_table.c:
                bad_fields.append(f)

        if len(bad_fields) > 0:
            good_fields = ['_id'] + self.sqla_table.c.keys()
            good_fields.remove('id')
            good_fields.remove('owner_id')
            raise Exception("Unexpected fields '" + str(bad_fields) + \
                "' received in query.\nValid fields for this data_type are: " + \
                str(good_fields))
        return
    
    def _nest_ids_to_ints(self, filter_params):
        """
        Given a dict of filter params used by simple_filter_query, converts all
        NestId objects (which are valid if the field is a foreignid_attribute)
        into type int, which sqlalchemy can use to query on.
        """
        clean_filter = dict(filter_params)
        for k in clean_filter:
            if isinstance(clean_filter[k], NestId):
                clean_filter[k] = clean_filter[k].get_value()
            elif isinstance(clean_filter[k], list):
                for i in range(len(clean_filter[k])):
                    if isinstance(clean_filter[k][i], NestId):
                        clean_filter[k][i] = clean_filter[k][i].get_value()
        return clean_filter

    def update_entry(self, dto, user=None):
        """
        returns the updated dto on success, None on failure
        """
        if user is None:
            user = self.requesting_user
        if not self.security_policy.can_write_entries(user):
            #TODO: also only allow the owner to edit an entry
            raise SecurityException('User not allowed to write')
        db_conn = self._db_connection()
        try:
            jdata = self.transcoder.object_to_flat_jdata(dto)

            #this also deletes 'id' from the dict
            id_val = jdata.pop('id', None)
            if id_val is None:
                raise Exception("Can't use 'update_entry' on an \
                    object that doesn't have an id in it's jdata")
            jdata['owner_id'] = user.get_nest_id().get_value()

            tbl = self.sqla_table
            stmt = update(tbl).where(tbl.c.id == id_val).values(**jdata)
            db_conn.execute(stmt)
            db_conn.close()
            updated_dto = self.read_entry(NestId(id_val), user=user)
        except Exception as e:
            db_conn.close()
            traceback.print_exc()
            updated_dto = None
        return updated_dto

    def delete_entry(self, nest_id, user=None):
        """
        returns the input nest_id if it is succesfully deleted,
        None on failure
        """
        if user is None:
            user = self.requesting_user
        if not self.security_policy.can_write_entries(user):
            #TODO: also only allow the owner to edit an entry
            raise SecurityException('User not allowed to write')
        db_conn = self._db_connection()
        try:
            tbl = self.sqla_table
            id_val = nest_id.get_value()
            stmt = delete(tbl).where(tbl.c.id == id_val)
            db_conn.execute(stmt)

            deleted_id = nest_id
            db_conn.close()
        except Exception as e:
            db_conn.close()
            traceback.print_exc()
            deleted_id = None
        return deleted_id

    def delete_all_entries(self, user=None):
        """
        deletes all rows in the current table. intended only for
        tools and unit testing situations
        """
        if user is None:
            user = self.requesting_user
        if not self.security_policy.can_write_entries(user):
            #TODO: also only allow the owner to edit an entry
            raise SecurityException('User not allowed to write')
        db_conn = self._db_connection()
        try:
            stmt = delete(self.sqla_table)
            res = db_conn.execute(stmt)
            num_deleted = res.rowcount
            print('deleted count: ' + str(num_deleted))
            db_conn.close()
        except Exception as e:
            db_conn.close()
        return num_deleted

    def _split_to_batches(self, dto_lst, batch_size):
        """
        splits a list of dtos into batches and also does
        the transform to jdata (with error checks)
        returns a list of lists of jdata
        """
        entries_idx = 0
        num_entries = len(dto_lst)
        batches = list()
        while entries_idx < num_entries:
            current_batch = list()
            batch_idx = 0
            while (entries_idx < num_entries) and (batch_idx < batch_size):
                current_batch.append(dto_lst[entries_idx])
                batch_idx += 1
                entries_idx += 1
            batches.append(current_batch)
        #log('batches: ' + str(batches))
        return batches

    def get_sqla_connection(self):
        return self._db_connection()

def log(msg):
    print msg
