def test_demo_login_with_valid_employee_no_credentials(api_client):
    response = api_client.post(
        "/api/users/login",
        json={"username": "A1001", "password": "admin123"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "登录成功"
    assert body["data"]["username"] == "admin"
    assert body["data"]["employee_no"] == "A1001"
    assert body["data"]["role"] == "admin"
    assert body["data"]["is_verified"] is True
    assert body["data"]["token_type"] == "bearer"
    assert body["data"]["access_token"]
    assert "password_hash" not in body["data"]


def test_business_api_requires_login(unauthenticated_client):
    response = unauthenticated_client.get("/api/inventory")
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_demo_login_rejects_invalid_password(api_client):
    response = api_client.post(
        "/api/users/login",
        json={"username": "A1001", "password": "wrong-password"},
    )

    assert response.status_code == 401
    body = response.json()
    assert body == {
        "success": False,
        "message": "工号或密码错误",
        "data": None,
    }


def test_demo_login_rejects_unverified_employee(api_client):
    response = api_client.post(
        "/api/users/login",
        json={"username": "S2001", "password": "pending123"},
    )

    assert response.status_code == 403
    body = response.json()
    assert body == {
        "success": False,
        "message": "该工号尚未完成账号激活，请先注册验证",
        "data": None,
    }


def test_get_user_identity_preview_by_employee_no(api_client):
    response = api_client.get("/api/users/identity/S2001")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["employee_no"] == "S2001"
    assert body["data"]["role"] == "store_staff"
    assert body["data"]["location_type"] == "store"
    assert body["data"]["is_verified"] is False
    assert body["data"]["store_id"] is not None


def test_register_user_activates_preloaded_employee(api_client):
    response = api_client.post(
        "/api/users/register",
        json={
            "employee_no": "S2001",
            "real_name": "王敏",
            "phone": "13000002001",
            "verification_code": "246810",
            "password": "secret123",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "注册成功"
    assert body["data"]["username"] == "store_pending_a"
    assert body["data"]["employee_no"] == "S2001"
    assert body["data"]["role"] == "store_staff"
    assert body["data"]["location_type"] == "store"
    assert body["data"]["is_verified"] is True
    assert "password_hash" not in body["data"]

    login_response = api_client.post(
        "/api/users/login",
        json={"username": "S2001", "password": "secret123"},
    )
    assert login_response.status_code == 200


def test_register_user_rejects_wrong_verification_code(api_client):
    response = api_client.post(
        "/api/users/register",
        json={
            "employee_no": "W2001",
            "real_name": "李峰",
            "phone": "13000002002",
            "verification_code": "000000",
            "password": "secret123",
        },
    )

    assert response.status_code == 403
    body = response.json()
    assert body == {
        "success": False,
        "message": "验证码错误，请联系管理员重新获取",
        "data": None,
    }


def test_send_registration_verification_code(api_client):
    response = api_client.post(
        "/api/users/verification-code",
        json={"employee_no": "W2001", "phone": "13000002002"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == "验证码已生成"
    assert body["data"]["masked_phone"] == "130****2002"
    assert body["data"]["verification_code"].isdigit()
    assert len(body["data"]["verification_code"]) == 6


def test_send_registration_verification_code_rejects_wrong_phone(api_client):
    response = api_client.post(
        "/api/users/verification-code",
        json={"employee_no": "W2001", "phone": "13000009999"},
    )

    assert response.status_code == 403
    assert response.json()["message"] == "手机号与工号档案不匹配"
