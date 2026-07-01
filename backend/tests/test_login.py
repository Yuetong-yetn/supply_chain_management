def test_demo_login_with_valid_credentials(api_client):
    response = api_client.post(
        "/api/users/login",
        json={"username": "admin", "password": "admin123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "登录成功"
    assert body["data"]["username"] == "admin"
    assert body["data"]["role"] == "admin"
    assert "password_hash" not in body["data"]


def test_demo_login_rejects_invalid_password(api_client):
    response = api_client.post(
        "/api/users/login",
        json={"username": "admin", "password": "wrong-password", "role": "admin"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body == {
        "success": False,
        "message": "用户名或密码错误",
        "data": None,
    }


def test_demo_login_rejects_role_mismatch(api_client):
    response = api_client.post(
        "/api/users/login",
        json={"username": "buyer", "password": "buyer123", "role": "manager"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body == {
        "success": False,
        "message": "所选角色与账号身份不匹配",
        "data": None,
    }


def test_register_user_normalizes_role_and_defaults_location(api_client):
    response = api_client.post(
        "/api/users",
        json={
            "username": "new_store_user",
            "password": "secret123",
            "real_name": "门店新用户",
            "role": "store",
            "phone": "13800000000",
            "is_active": True,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["username"] == "new_store_user"
    assert body["data"]["role"] == "store_staff"
    assert body["data"]["location_type"] == "store"
    assert "password_hash" not in body["data"]


def test_register_user_rejects_duplicate_username(api_client):
    response = api_client.post(
        "/api/users",
        json={
            "username": "admin",
            "password": "secret123",
            "real_name": "重复用户",
            "role": "admin",
            "is_active": True,
        },
    )

    assert response.status_code == 400
    body = response.json()
    assert body == {
        "success": False,
        "message": "用户名已存在，请更换后重试",
        "data": None,
    }
