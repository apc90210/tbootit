import pytest

def test_repair_status_transition_matrix(client):
    r = client.post("/api/repairs/", json={
        "customer_name": "Тест Матрицы",
        "customer_phone": "+7 900 333-33-33",
        "device_type": "Ноутбук",
        "reported_issue": "Тест переходов"
    }).json()

    r_id = r["id"]

    # Valid transition: received -> diagnostics
    res1 = client.post(f"/api/repairs/{r_id}/status", json={"status": "diagnostics", "comment": "Передано на диагностику"})
    assert res1.status_code == 200
    assert res1.json()["status"] == "diagnostics"

    # Valid transition: diagnostics -> in_repair
    res2 = client.post(f"/api/repairs/{r_id}/status", json={"status": "in_repair", "comment": "В работе"})
    assert res2.status_code == 200
    assert res2.json()["status"] == "in_repair"

    # Invalid transition: in_repair -> issued (must go to ready or unrepairable first)
    res_inv = client.post(f"/api/repairs/{r_id}/status", json={"status": "issued"})
    assert res_inv.status_code == 409
    assert "Недопустимый переход" in res_inv.json()["detail"]

    # Valid transition: in_repair -> ready
    res3 = client.post(f"/api/repairs/{r_id}/status", json={"status": "ready"})
    assert res3.status_code == 200
    assert res3.json()["status"] == "ready"

    # Valid transition: ready -> issued
    res4 = client.post(f"/api/repairs/{r_id}/status", json={"status": "issued"})
    assert res4.status_code == 200
    data_issued = res4.json()
    assert data_issued["status"] == "issued"
    assert data_issued["issued_at"] is not None
    assert data_issued["closed_at"] is not None

    # History audit verification
    hist_res = client.get(f"/api/repairs/{r_id}/history")
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) == 5  # received + 4 transitions

def test_closed_repair_edit_blocked(client):
    r = client.post("/api/repairs/", json={
        "customer_name": "Тест Закрытого",
        "customer_phone": "+7 900 444-44-44",
        "device_type": "Принтер",
        "reported_issue": "Замятие бумаги"
    }).json()

    r_id = r["id"]
    # Cancel repair
    client.post(f"/api/repairs/{r_id}/status", json={"status": "canceled", "comment": "Отказ от ремонта"})

    # Attempt to edit cancelled repair
    res_edit = client.patch(f"/api/repairs/{r_id}", json={"customer_name": "Новое Имя"})
    assert res_edit.status_code == 409
    assert "Запрещено редактировать" in res_edit.json()["detail"]
