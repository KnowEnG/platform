import nest_py.core.flask.accounts.token as token
from nest_py.core.flask.accounts.token import TokenPayload
from nest_py.core.flask.accounts.token import TokenAgent
from nest_py.core.data_types.nest_user import NestUser
from nest_py.core.data_types.nest_id import NestId

from datetime import timedelta
import time

def make_user():
    nu = NestUser(NestId(11), 'usernm1', 'given_nm1', 'family_nm1', thumb_url='thumbu1')
    return nu

def test_roundtrip():
    jwt_secret = 'hi'
    jwt_issuer = 'me'
    jwt_audiences = ['us']
    lifespan = timedelta(seconds=1)
    nu = make_user()

    tp1 = token.create_user_payload_now(nu, jwt_issuer, jwt_audiences, lifespan)
    token1 = tp1.to_jwt_token(jwt_secret)

    audience = jwt_audiences[0]
    tp2 = token.decode_token(token1, jwt_secret, audience, jwt_issuer)
    user_rt = tp2.to_nest_user()
    print('orig: ' + str(nu))
    print('rt  : ' + str(user_rt)) 
    assert(user_rt == nu)
    assert(not tp2.is_expired())

    #bad audience
    audience = 'them'
    tp3 = token.decode_token(token1, jwt_secret, audience, jwt_issuer)
    assert(tp3 is None)

    #bad issuer
    audience = 'us'
    issuer = 'someone_else'
    tp4 = token.decode_token(token1, jwt_secret, audience, issuer)
    assert(tp4 is None)

    time.sleep(2) #wait 2 seconds for the token to expire

    issuer = 'me'
    tp5 = token.decode_token(token1, jwt_secret, audience, issuer)
    assert(not tp5 is None)
    print('tp5: ' + str(tp5.data))
    assert(tp5.is_expired())

