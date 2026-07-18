from fastapi.testclient import TestClient


def test_home_and_manual_are_public(client: TestClient) -> None:
    home = client.get("/")
    manual = client.get("/manual")
    script = client.get("/static/app.js")

    assert home.status_code == 200
    assert "Relay LLM" in home.text
    assert "API Keys" in home.text
    assert '<table class="key-table">' in home.text
    assert '<tbody id="key-list"></tbody>' in home.text
    assert '<th scope="col">名稱</th>' in home.text
    assert '<th scope="col">用量</th>' in home.text
    assert '<th scope="col">操作</th>' in home.text
    assert 'id="icon-pencil"' in home.text
    assert 'id="icon-trash"' in home.text
    assert 'id="icon-log-out"' in home.text
    assert 'id="new-key" class="dialog"' in home.text
    assert 'id="remove-key-dialog"' in home.text
    nav_markup = home.text[home.text.index('<nav class="site-nav"') : home.text.index("</nav>")]
    assert 'id="account-menu" class="account-menu hidden"' in nav_markup
    assert 'id="avatar-button"' in nav_markup
    assert 'id="account-popper" class="account-popper hidden"' in nav_markup
    assert 'id="logout-button" class="account-menu-item"' in nav_markup
    assert home.text.count('id="logout-button"') == 1
    assert home.text.count('href="/manual"') == 1
    assert script.status_code == 200
    assert "window.confirm" not in script.text
    assert "openRemoveKeyDialog" in script.text
    assert "newKeyDialog.showModal()" in script.text
    assert "nameCell.dataset.label = '名稱'" in script.text
    assert "actionsCell.dataset.label = '操作'" in script.text
    assert "setAccountPopper" in script.text
    assert "event.key === 'Escape'" in script.text
    assert "accountMenu.contains(event.target)" in script.text
    assert manual.status_code == 200
    assert "註冊與登入" in manual.text
    assert "PATCH" in manual.text
    assert "DELETE" in manual.text
    assert "/api/keys/{key_id}" in manual.text
    assert "Token" in manual.text
    assert "http://127.0.0.1:8000/api/register" in manual.text
    assert "/v1/chat/completions" in manual.text
    assert "curl" in manual.text
    assert "SSE 串流" in manual.text
    assert 'href="#streaming"' in manual.text
    assert 'section id="streaming"' in manual.text
    assert '"stream": true' in manual.text
    assert "text/event-stream" in manual.text
    assert "chat.completion.chunk" in manual.text
    assert "choices[0].delta.content" in manual.text
    assert "data: [DONE]" in manual.text
    assert "--no-buffer" in manual.text


def test_unknown_api_route_is_json(client: TestClient) -> None:
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["success"] is False
    assert response.json()["message"]["code"] == "not_found"
