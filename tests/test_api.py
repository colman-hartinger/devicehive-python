from six import string_types
from devicehive import ApiResponseError
from devicehive import DeviceError
from devicehive.user import User


def test_get_info(test):
    device_hive_api = test.device_hive_api()
    info = device_hive_api.get_info()
    assert isinstance(info['api_version'], string_types)
    assert isinstance(info['server_timestamp'], string_types)
    if info.get('rest_server_url'):
        assert info['websocket_server_url'] is None
        assert isinstance(info['rest_server_url'], string_types)
        return
    assert isinstance(info['websocket_server_url'], string_types)
    assert info['rest_server_url'] is None


def test_get_cluster_info(test):
    device_hive_api = test.device_hive_api()
    cluster_info = device_hive_api.get_cluster_info()
    assert isinstance(cluster_info['bootstrap.servers'], string_types)
    assert isinstance(cluster_info['zookeeper.connect'], string_types)


def test_create_token(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    login = test.generate_id('c-t', test.USER_ENTITY)
    password = test.generate_id('c-t')
    role = User.ADMINISTRATOR_ROLE
    data = {'k': 'v'}
    user = device_hive_api.create_user(login, password, role, data)
    tokens = device_hive_api.create_token(user.id)
    assert isinstance(tokens['access_token'], string_types)
    assert isinstance(tokens['refresh_token'], string_types)
    user_id = user.id
    user.remove()
    try:
        device_hive_api.create_token(user_id)
        assert False
    except ApiResponseError as api_response_error:
        assert api_response_error.code == 404


def test_refresh_token(test):
    device_hive_api = test.device_hive_api()
    access_token = device_hive_api.refresh_token()
    assert isinstance(access_token, string_types)


def test_subscribe_insert_commands(test):

    def init_devices(handler):
        devices, command_ids, command_names = [], [], []
        _, device_ids = test.generate_ids('s-i-c', test.DEVICE_ENTITY, 2)
        for device_id in device_ids:
            device = handler.api.put_device(device_id)
            devices.append(device)
            command_name = '%s-name' % device.id
            command = device.send_command(command_name)
            command_ids.append(command.id)
            command_names.append(command_name)
        return devices, device_ids, command_ids, command_names

    def set_handler_data(handler, devices, device_ids, command_ids,
                         command_names):
        handler.data['devices'] = devices
        handler.data['device_ids'] = device_ids
        handler.data['command_ids'] = command_ids
        handler.data['command_names'] = command_names

    def handle_connect(handler):
        devices, device_ids, command_ids, command_names = init_devices(handler)
        handler.api.subscribe_insert_commands(device_ids)
        set_handler_data(handler, devices, device_ids, command_ids,
                         command_names)

    def handle_command_insert(handler, command):
        assert command.id in handler.data['command_ids']
        handler.data['command_ids'].remove(command.id)
        if handler.data['command_ids']:
            return
        [device.remove() for device in handler.data['devices']]
        handler.disconnect()

    test.run(handle_connect, handle_command_insert)

    def handle_connect(handler):
        devices, device_ids, command_ids, command_names = init_devices(handler)
        command_name = command_names[0]
        handler.api.subscribe_insert_commands(device_ids, names=[command_name])
        set_handler_data(handler, devices, device_ids, command_ids,
                         command_names)

    def handle_command_insert(handler, command):
        assert command.id == handler.data['command_ids'][0]
        [device.remove() for device in handler.data['devices']]
        handler.disconnect()

    test.run(handle_connect, handle_command_insert)

    def handle_connect(handler):
        devices, device_ids, command_ids, command_names = init_devices(handler)
        handler.api.subscribe_insert_commands(device_ids)
        try:
            handler.api.subscribe_insert_commands(device_ids)
            assert False
        except DeviceError:
            pass
        [device.remove() for device in devices]
        if test.http_transport:
            return
        try:
            handler.api.subscribe_insert_commands(device_ids)
            assert False
        except ApiResponseError as api_response_error:
            assert api_response_error.code == 404

    test.run(handle_connect)


def test_unsubscribe_insert_commands(test):

    def handle_connect(handler):
        _, device_ids = test.generate_ids('u-i-c', test.DEVICE_ENTITY, 3)
        devices = []
        for device_id in device_ids:
            device = handler.api.put_device(device_id)
            devices.append(device)
            command_name = '%s-name' % device_id
            device.send_command(command_name)
        handler.api.subscribe_insert_commands(device_ids)
        handler.api.unsubscribe_insert_commands(device_ids)
        try:
            handler.api.unsubscribe_insert_commands(device_ids)
            assert False
        except DeviceError:
            pass
        handler.api.subscribe_insert_commands(device_ids)
        [device.remove() for device in devices]
        try:
            handler.api.unsubscribe_insert_commands(device_ids)
            assert False
        except DeviceError:
            pass

    test.run(handle_connect)


def test_subscribe_update_commands(test):

    def init_devices(handler):
        devices, command_ids, command_names = [], [], []
        _, device_ids = test.generate_ids('s-u-c', test.DEVICE_ENTITY, 2)
        for device_id in device_ids:
            device = handler.api.put_device(device_id)
            devices.append(device)
            command_name = '%s-name' % device.id
            command = device.send_command(command_name)
            command.status = 'status'
            command.save()
            command_ids.append(command.id)
            command_names.append(command_name)
        return devices, device_ids, command_ids, command_names

    def set_handler_data(handler, devices, device_ids, command_ids,
                         command_names):
        handler.data['devices'] = devices
        handler.data['device_ids'] = device_ids
        handler.data['command_ids'] = command_ids
        handler.data['command_names'] = command_names

    def handle_connect(handler):
        devices, device_ids, command_ids, command_names = init_devices(handler)
        handler.api.subscribe_update_commands(device_ids)
        set_handler_data(handler, devices, device_ids, command_ids,
                         command_names)

    def handle_command_update(handler, command):
        assert command.id in handler.data['command_ids']
        handler.data['command_ids'].remove(command.id)
        if handler.data['command_ids']:
            return
        [device.remove() for device in handler.data['devices']]
        handler.disconnect()

    test.run(handle_connect, handle_command_update=handle_command_update)

    def handle_connect(handler):
        devices, device_ids, command_ids, command_names = init_devices(handler)
        command_name = command_names[0]
        handler.api.subscribe_update_commands(device_ids, names=[command_name])
        set_handler_data(handler, devices, device_ids, command_ids,
                         command_names)

    def handle_command_update(handler, command):
        assert command.id == handler.data['command_ids'][0]
        [device.remove() for device in handler.data['devices']]
        handler.disconnect()

    test.run(handle_connect, handle_command_update=handle_command_update)

    def handle_connect(handler):
        devices, device_ids, command_ids, command_names = init_devices(handler)
        handler.api.subscribe_update_commands(device_ids)
        try:
            handler.api.subscribe_update_commands(device_ids)
            assert False
        except DeviceError:
            pass
        [device.remove() for device in devices]
        if test.http_transport:
            return
        try:
            handler.api.subscribe_update_commands(device_ids)
            assert False
        except ApiResponseError as api_response_error:
            assert api_response_error.code == 404

    test.run(handle_connect)


def test_unsubscribe_update_commands(test):

    def handle_connect(handler):
        _, device_ids = test.generate_ids('u-u-c', test.DEVICE_ENTITY, 3)
        devices = []
        for device_id in device_ids:
            device = handler.api.put_device(device_id)
            devices.append(device)
            command_name = '%s-name' % device_id
            command = device.send_command(command_name)
            command.status = 'status'
            command.save()
        handler.api.subscribe_update_commands(device_ids)
        handler.api.unsubscribe_update_commands(device_ids)
        try:
            handler.api.unsubscribe_update_commands(device_ids)
            assert False
        except DeviceError:
            pass
        handler.api.subscribe_update_commands(device_ids)
        [device.remove() for device in devices]
        try:
            handler.api.unsubscribe_update_commands(device_ids)
            assert False
        except DeviceError:
            pass

    test.run(handle_connect)


def test_subscribe_notifications(test):

    def init_devices(handler):
        _, device_ids = test.generate_ids('s-n', test.DEVICE_ENTITY, 2)
        devices, notification_ids = [], []
        notification_names = []
        for device_id in device_ids:
            device = handler.api.put_device(device_id)
            devices.append(device)
            notification_name = '%s-name' % device.id
            notification = device.send_notification(notification_name)
            notification_ids.append(notification.id)
            notification_names.append(notification_name)
        return devices, device_ids, notification_ids, notification_names

    def set_handler_data(handler, devices, device_ids, notification_ids,
                         notification_names):
        handler.data['devices'] = devices
        handler.data['device_ids'] = device_ids
        handler.data['notification_ids'] = notification_ids
        handler.data['notification_names'] = notification_names

    def handle_connect(handler):
        (devices,
         device_ids,
         notification_ids,
         notification_names) = init_devices(handler)
        handler.api.subscribe_notifications(device_ids)
        set_handler_data(handler, devices, device_ids, notification_ids,
                         notification_names)

    def handle_notification(handler, notification):
        if notification.notification[0] == '$':
            return
        assert notification.id in handler.data['notification_ids']
        handler.data['notification_ids'].remove(notification.id)
        if handler.data['notification_ids']:
            return
        [device.remove() for device in handler.data['devices']]
        handler.disconnect()

    test.run(handle_connect, handle_notification=handle_notification)

    def handle_connect(handler):
        (devices,
         device_ids,
         notification_ids,
         notification_names) = init_devices(handler)
        notification_name = notification_names[0]
        handler.api.subscribe_notifications(device_ids,
                                            names=[notification_name])
        set_handler_data(handler, devices, device_ids, notification_ids,
                         notification_names)

    def handle_notification(handler, notification):
        assert notification.id == handler.data['notification_ids'][0]
        [device.remove() for device in handler.data['devices']]
        handler.disconnect()

    test.run(handle_connect, handle_notification=handle_notification)

    def handle_connect(handler):
        (devices,
         device_ids,
         notification_ids,
         notification_names) = init_devices(handler)
        handler.api.subscribe_notifications(device_ids)
        try:
            handler.api.subscribe_notifications(device_ids)
            assert False
        except DeviceError:
            pass
        [device.remove() for device in devices]
        if test.http_transport:
            return
        try:
            handler.api.subscribe_notifications(device_ids)
            assert False
        except ApiResponseError as api_response_error:
            assert api_response_error.code == 404

    test.run(handle_connect)


def test_unsubscribe_notifications(test):

    def handle_connect(handler):
        _, device_ids = test.generate_ids('u-n', test.DEVICE_ENTITY, 3)
        devices = []
        for device_id in device_ids:
            device = handler.api.put_device(device_id)
            devices.append(device)
            notification_name = '%s-name' % device_id
            device.send_notification(notification_name)
        handler.api.subscribe_notifications(device_ids)
        handler.api.unsubscribe_notifications(device_ids)
        try:
            handler.api.unsubscribe_notifications(device_ids)
            assert False
        except DeviceError:
            pass
        handler.api.subscribe_notifications(device_ids)
        [device.remove() for device in devices]
        try:
            handler.api.unsubscribe_notifications(device_ids)
            assert False
        except DeviceError:
            pass

    test.run(handle_connect)


def test_list_devices(test):
    device_hive_api = test.device_hive_api()
    test_id, device_ids = test.generate_ids('l-d', test.DEVICE_ENTITY, 2)
    options = [{'device_id': device_id, 'name': '%s-name' % device_id}
               for device_id in device_ids]
    test_devices = [device_hive_api.put_device(**option) for option in options]
    devices = device_hive_api.list_devices()
    assert len(devices) >= len(options)
    name = options[0]['name']
    device, = device_hive_api.list_devices(name=name)
    assert device.name == name
    name_pattern = test.generate_id('l-d-n-e')
    assert not device_hive_api.list_devices(name_pattern=name_pattern)
    name_pattern = test_id + '%'
    devices = device_hive_api.list_devices(name_pattern=name_pattern)
    assert len(devices) == len(options)
    device_0, device_1 = device_hive_api.list_devices(name_pattern=name_pattern,
                                                      sort_field='name',
                                                      sort_order='ASC')
    assert device_0.id == options[0]['device_id']
    assert device_1.id == options[1]['device_id']
    device_0, device_1 = device_hive_api.list_devices(name_pattern=name_pattern,
                                                      sort_field='name',
                                                      sort_order='DESC')
    assert device_0.id == options[1]['device_id']
    assert device_1.id == options[0]['device_id']
    device, = device_hive_api.list_devices(name_pattern=name_pattern,
                                           sort_field='name', sort_order='ASC',
                                           take=1)
    assert device.id == options[0]['device_id']
    device, = device_hive_api.list_devices(name_pattern=name_pattern,
                                           sort_field='name', sort_order='ASC',
                                           take=1, skip=1)
    assert device.id == options[1]['device_id']
    [test_device.remove() for test_device in test_devices]


def test_get_device(test):
    device_hive_api = test.device_hive_api()
    device_id = test.generate_id('g-d', test.DEVICE_ENTITY)
    name = '%s-name' % device_id
    data = {'data_key': 'data_value'}
    device_hive_api.put_device(device_id, name=name, data=data)
    device = device_hive_api.get_device(device_id)
    assert device.id == device_id
    assert device.name == name
    assert device.data == data
    assert isinstance(device.network_id, int)
    assert isinstance(device.device_type_id, int)
    assert not device.is_blocked
    device.remove()
    device_id = test.generate_id('g-d-n-e')
    try:
        device_hive_api.get_device(device_id)
        assert False
    except ApiResponseError as api_response_error:
        if test.admin_refresh_token:
            assert api_response_error.code == 404
        else:
            assert api_response_error.code == 403


def test_put_device(test):
    device_hive_api = test.device_hive_api()
    device_id = test.generate_id('p-d', test.DEVICE_ENTITY)
    device = device_hive_api.put_device(device_id)
    assert device.id == device_id
    assert device.name == device_id
    assert not device.data
    assert isinstance(device.network_id, int)
    assert isinstance(device.device_type_id, int)
    assert not device.is_blocked
    device.remove()
    name = '%s-name' % device_id
    data = {'data_key': 'data_value'}
    device = device_hive_api.put_device(device_id, name=name, data=data,
                                        is_blocked=True)
    assert device.id == device_id
    assert device.name == name
    assert device.data == data
    assert isinstance(device.network_id, int)
    assert isinstance(device.device_type_id, int)
    assert device.is_blocked
    device.remove()


def test_list_networks(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    test_id, network_ids = test.generate_ids('l-n', test.NETWORK_ENTITY, 2)
    options = [{'name': network_id,
                'description': '%s-description' % network_id}
               for network_id in network_ids]
    test_networks = [device_hive_api.create_network(**option)
                     for option in options]
    networks = device_hive_api.list_networks()
    assert len(networks) >= len(options)
    name = options[0]['name']
    network, = device_hive_api.list_networks(name=name)
    assert network.name == name
    name_pattern = test.generate_id('l-n-n-e')
    assert not device_hive_api.list_networks(name_pattern=name_pattern)
    name_pattern = test_id + '%'
    networks = device_hive_api.list_networks(name_pattern=name_pattern)
    assert len(networks) == len(options)
    network_0, network_1 = device_hive_api.list_networks(
            name_pattern=name_pattern, sort_field='name', sort_order='ASC')
    assert network_0.name == options[0]['name']
    assert network_1.name == options[1]['name']
    network_0, network_1 = device_hive_api.list_networks(
            name_pattern=name_pattern, sort_field='name', sort_order='DESC')
    assert network_0.name == options[1]['name']
    assert network_1.name == options[0]['name']
    network, = device_hive_api.list_networks(name_pattern=name_pattern,
                                             sort_field='name',
                                             sort_order='ASC', take=1)
    assert network.name == options[0]['name']
    network, = device_hive_api.list_networks(name_pattern=name_pattern,
                                             sort_field='name',
                                             sort_order='ASC', take=1,
                                             skip=1)
    assert network.name == options[1]['name']
    [test_network.remove() for test_network in test_networks]


def test_get_network(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    name = test.generate_id('g-n', test.NETWORK_ENTITY)
    description = '%s-description' % name
    network = device_hive_api.create_network(name, description)
    network = device_hive_api.get_network(network.id)
    assert isinstance(network.id, int)
    assert network.name == name
    assert network.description == description
    network_id = network.id
    network.remove()
    try:
        device_hive_api.get_network(network_id)
        assert False
    except ApiResponseError as api_response_error:
        assert api_response_error.code == 404


def test_create_network(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    name = test.generate_id('c-n', test.NETWORK_ENTITY)
    description = '%s-description' % name
    network = device_hive_api.create_network(name, description)
    assert isinstance(network.id, int)
    assert network.name == name
    assert network.description == description
    try:
        device_hive_api.create_network(name, description)
        assert False
    except ApiResponseError as api_response_error:
        assert api_response_error.code == 403
    network.remove()


def test_list_device_types(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    test_id, device_type_ids = test.generate_ids('l-dt',
                                                 test.DEVICE_TYPE_ENTITY, 2)
    options = [{'name': device_type_id,
                'description': '%s-description' % device_type_id}
               for device_type_id in device_type_ids]
    test_device_types = [device_hive_api.create_device_type(**option)
                         for option in options]
    device_types = device_hive_api.list_device_types()
    assert len(device_types) >= len(options)
    name = options[0]['name']
    device_type, = device_hive_api.list_device_types(name=name)
    assert device_type.name == name
    name_pattern = test.generate_id('l-dt-n-e')
    assert not device_hive_api.list_device_types(name_pattern=name_pattern)
    name_pattern = test_id + '%'
    device_types = device_hive_api.list_device_types(name_pattern=name_pattern)
    assert len(device_types) == len(options)
    device_type_0, device_type_1 = device_hive_api.list_device_types(
        name_pattern=name_pattern, sort_field='name', sort_order='ASC')
    assert device_type_0.name == options[0]['name']
    assert device_type_1.name == options[1]['name']
    device_type_0, device_type_1 = device_hive_api.list_device_types(
        name_pattern=name_pattern, sort_field='name', sort_order='DESC')
    assert device_type_0.name == options[1]['name']
    assert device_type_1.name == options[0]['name']
    device_type, = device_hive_api.list_device_types(name_pattern=name_pattern,
                                                     sort_field='name',
                                                     sort_order='ASC', take=1)
    assert device_type.name == options[0]['name']
    device_type, = device_hive_api.list_device_types(name_pattern=name_pattern,
                                                     sort_field='name',
                                                     sort_order='ASC', take=1,
                                                     skip=1)
    assert device_type.name == options[1]['name']
    [test_device_type.remove() for test_device_type in test_device_types]


def test_get_device_type(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    name = test.generate_id('g-dt', test.DEVICE_TYPE_ENTITY)
    description = '%s-description' % name
    device_type = device_hive_api.create_device_type(name, description)
    device_type = device_hive_api.get_device_type(device_type.id)
    assert isinstance(device_type.id, int)
    assert device_type.name == name
    assert device_type.description == description
    device_type_id = device_type.id
    device_type.remove()
    try:
        device_hive_api.get_device_type(device_type_id)
        assert False
    except ApiResponseError as api_response_error:
        assert api_response_error.code == 404


def test_create_device_type(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    name = test.generate_id('c-dt', test.DEVICE_TYPE_ENTITY)
    description = '%s-description' % name
    device_type = device_hive_api.create_device_type(name, description)
    assert isinstance(device_type.id, int)
    assert device_type.name == name
    assert device_type.description == description
    try:
        device_hive_api.create_device_type(name, description)
        assert False
    except ApiResponseError as api_response_error:
        assert api_response_error.code == 403
    device_type.remove()


def test_list_users(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    test_id, user_ids = test.generate_ids('l-u', test.USER_ENTITY, 2)
    role = User.ADMINISTRATOR_ROLE
    options = [{'login': user_id,
                'password': '%s-password' % user_id,
                'role': role, 'data': {str(i): i}}
               for i, user_id in enumerate(user_ids)]
    test_users = [device_hive_api.create_user(**option) for option in options]
    users = device_hive_api.list_users()
    assert len(users) >= len(options)
    login = options[0]['login']
    user, = device_hive_api.list_users(login=login)
    assert user.login == login
    login_pattern = test.generate_id('l-u-n-e')
    assert not device_hive_api.list_users(login_pattern=login_pattern)
    login_pattern = test_id + '%'
    users = device_hive_api.list_users(login_pattern=login_pattern)
    assert len(users) == len(options)
    users = device_hive_api.list_users(role=role)
    assert len(users) >= len(options)
    status = User.ACTIVE_STATUS
    users = device_hive_api.list_users(status=status)
    assert len(users) >= len(options)
    user_0, user_1 = device_hive_api.list_users(login_pattern=login_pattern,
                                                sort_field='login',
                                                sort_order='ASC')
    assert user_0.login == options[0]['login']
    assert user_1.login == options[1]['login']
    user_0, user_1 = device_hive_api.list_users(login_pattern=login_pattern,
                                                sort_field='login',
                                                sort_order='DESC')
    assert user_0.login == options[1]['login']
    assert user_1.login == options[0]['login']
    user, = device_hive_api.list_users(login_pattern=login_pattern,
                                       sort_field='login', sort_order='ASC',
                                       take=1)
    assert user.login == options[0]['login']
    user, = device_hive_api.list_users(login_pattern=login_pattern,
                                       sort_field='login', sort_order='ASC',
                                       take=1, skip=1)
    assert user.login == options[1]['login']
    [test_user.remove() for test_user in test_users]


def test_get_current_user(test):
    device_hive_api = test.device_hive_api()
    user = device_hive_api.get_current_user()
    assert isinstance(user.id, int)


def test_get_user(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    login = test.generate_id('g-u', test.USER_ENTITY)
    password = test.generate_id('g-u')
    role = User.ADMINISTRATOR_ROLE
    data = {'k': 'v'}
    user = device_hive_api.create_user(login, password, role, data)
    user = device_hive_api.get_user(user.id)
    assert isinstance(user.id, int)
    assert user.login == login
    assert not user.last_login
    assert not user.intro_reviewed
    assert user.role == role
    assert user.status == User.ACTIVE_STATUS
    assert user.data == data
    user_id = user.id
    user.remove()
    try:
        device_hive_api.get_user(user_id)
        assert False
    except ApiResponseError as api_response_error:
        assert api_response_error.code == 404


def test_create_user(test):
    test.only_admin_implementation()
    device_hive_api = test.device_hive_api()
    login = test.generate_id('c-u', test.USER_ENTITY)
    password = test.generate_id('c-u')
    role = User.ADMINISTRATOR_ROLE
    data = {'k': 'v'}
    user = device_hive_api.create_user(login, password, role, data)
    assert isinstance(user.id, int)
    assert user.login == login
    assert not user.last_login
    assert not user.intro_reviewed
    assert user.role == role
    assert user.status == User.ACTIVE_STATUS
    assert user.data == data
    try:
        device_hive_api.create_user(login, password, role, data)
        assert False
    except ApiResponseError as api_response_error:
        assert api_response_error.code == 403
    user.remove()
