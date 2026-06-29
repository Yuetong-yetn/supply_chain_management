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
        json={"username": "admin", "password": "wrong-password"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body == {
        "success": False,
        "message": "用户名或密码错误",
        "data": None,
    }
