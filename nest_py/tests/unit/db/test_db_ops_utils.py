import pytest
import nest_py.core.db.db_ops_utils as db_ops_utils

def test_validate_configs():
    """Tests __init__."""

    # no app
    with pytest.raises(AttributeError):
        db_ops_utils._validate_user_configs(None)

    # no DEMO_AUTHENTICATION_ACCOUNTS key in config
    with pytest.raises(AttributeError):
        db_ops_utils._validate_user_configs([])

    # duplicate usernames
    with pytest.raises(AttributeError):
        db_ops_utils._validate_user_configs(
            [
                {
                    'username': 'demouser',
                    'password': 'demopass',
                    'given_name': 'Demo',
                    'family_name': 'User',
                }, {
                    'username': 'demouser',
                    'password': 'otherpass',
                    'given_name': 'Other',
                    'family_name': 'User',
                }
            ])

    # no username
    with pytest.raises(AttributeError):
        db_ops_utils._validate_user_configs(
            [{
                'password': 'demopass',
                'given_name': 'Demo',
                'family_name': 'User'}])
    # no password
    with pytest.raises(AttributeError):
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'given_name': 'Demo',
                'family_name': 'User'}])
    # no given_name
    with pytest.raises(AttributeError):
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'password': 'demopass',
                'family_name': 'User'}])
    # no family_name
    with pytest.raises(AttributeError):
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'password': 'demopass',
                'given_name': 'Demo'}])

    # empty username
    with pytest.raises(AttributeError) as exc:
        db_ops_utils._validate_user_configs(
            [{
                'username': '',
                'password': 'demopass',
                'given_name': 'Demo',
                'family_name': 'User'}])
        assert str(exc.value) == 'username cannot be empty'
    # empty password
    with pytest.raises(AttributeError) as exc:
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'password': '',
                'given_name': 'Demo',
                'family_name': 'User'}])
        assert str(exc.value) == 'password cannot be empty'
    # empty given_name
    with pytest.raises(AttributeError) as exc:
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'password': 'demopass',
                'given_name': '',
                'family_name': 'User'}])
        assert str(exc.value) == 'given_name cannot be empty'
    # empty family_name
    with pytest.raises(AttributeError) as exc:
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'password': 'demopass',
                'given_name': 'Demo',
                'family_name': ''}])
        assert str(exc.value) == 'family_name cannot be empty'

    # spaces-only username
    with pytest.raises(AttributeError) as exc:
        db_ops_utils._validate_user_configs(
            [{
                'username': '  ',
                'password': 'demopass',
                'given_name': 'Demo',
                'family_name': 'User'}])
        assert str(exc.value) == 'username cannot be empty'
    # spaces-only password
    with pytest.raises(AttributeError) as exc:
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'password': '   ',
                'given_name': 'Demo',
                'family_name': 'User'}])
        assert str(exc.value) == 'password cannot be empty'
    # space-only given_name
    with pytest.raises(AttributeError) as exc:
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'password': 'demopass',
                'given_name': '  ',
                'family_name': 'User'}])
        assert str(exc.value) == 'given_name cannot be empty'
    # spaces-only family_name
    with pytest.raises(AttributeError) as exc:
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'password': 'demopass',
                'given_name': 'Demo',
                'family_name': '  '}])
        assert str(exc.value) == 'family_name cannot be empty'

    # username w/ spaces
    with pytest.raises(AttributeError) as exc:
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser ',
                'password': 'demopass',
                'given_name': 'Demo',
                'family_name': 'User'}])
        assert str(exc.value) == \
            'DEMO_AUTHENTICATION_USERNAME cannot contain spaces'

    # password w/ spaces
    with pytest.raises(AttributeError):
        db_ops_utils._validate_user_configs(
            [{
                'username': 'demouser',
                'password': 'demopass ',
                'given_name': 'Demo',
                'family_name': 'User'}])
        assert str(exc.value) == \
            'DEMO_AUTHENTICATION_PASSWORD cannot contain spaces'

    # good username and password
    db_ops_utils._validate_user_configs(
        [ {
            'username': 'demouser',
            'userid': 11,
            'password': 'demopass',
            'given_name': 'Demo',
            'family_name': 'User',
        }, {
            'username': 'otheruser',
            'userid': 12,
            'password': 'otherpass',
            'given_name': 'Other',
            'family_name': 'User',
        }
        ])
    return


