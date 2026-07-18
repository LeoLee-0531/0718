import json

from fastapi.testclient import TestClient


def inference_payload() -> dict:
    return {
        "model": "mock-echo-1",
        "messages": [
            {"role": "system", "content": "Answer briefly."},
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "prior response"},
            {"role": "user", "content": "最後一則問題"},
        ],
    }


def test_inference_rejects_missing_and_invalid_keys_with_json(
    client: TestClient, api_key: str
) -> None:
    missing = client.post("/v1/chat/completions", json=inference_payload())
    assert missing.status_code == 401
    assert missing.headers["content-type"].startswith("application/json")
    assert missing.json()["message"]["code"] == "invalid_api_key"

    invalid = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer llm_live_invalid"},
        json=inference_payload(),
    )
    assert invalid.status_code == 401
    assert invalid.json()["success"] is False


def test_inference_echoes_last_user_message_and_has_consistent_usage(
    registered_client: TestClient, api_key: str
) -> None:
    response = registered_client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json=inference_payload(),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["message"] == {}
    assert body["object"] == "chat.completion"
    assert body["model"] == "mock-echo-1"
    assert "最後一則問題" in body["choices"][0]["message"]["content"]
    assert body["choices"][0]["message"]["role"] == "assistant"
    usage = body["usage"]
    assert usage["prompt_tokens"] > 0
    assert usage["completion_tokens"] > 0
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

    account = registered_client.get("/api/me").json()["message"]
    assert account["keys"][0]["last_used_at"] is not None
    assert account["keys"][0]["usage"] == {
        "requests": 1,
        "prompt_tokens": usage["prompt_tokens"],
        "completion_tokens": usage["completion_tokens"],
        "total_tokens": usage["total_tokens"],
    }


def test_usage_accumulates_per_key_for_successful_requests(
    registered_client: TestClient,
) -> None:
    first_key = registered_client.post("/api/keys").json()["message"]["api_key"]
    second_key = registered_client.post("/api/keys").json()["message"]["api_key"]

    first_response = registered_client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {first_key}"},
        json=inference_payload(),
    )
    assert first_response.status_code == 200
    registered_client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {first_key}"},
        json=inference_payload(),
    )
    registered_client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {second_key}"},
        json=inference_payload(),
    )
    registered_client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {first_key}"},
        json={"model": "mock-echo-1", "messages": [{"role": "system", "content": "Hi"}]},
    )

    keys = registered_client.get("/api/me").json()["message"]["keys"]
    usage_by_prefix = {key["display"][:-3]: key["usage"] for key in keys}
    request_usage = first_response.json()["usage"]
    assert usage_by_prefix[first_key[:17]] == {
        "requests": 2,
        "prompt_tokens": request_usage["prompt_tokens"] * 2,
        "completion_tokens": request_usage["completion_tokens"] * 2,
        "total_tokens": request_usage["total_tokens"] * 2,
    }
    assert usage_by_prefix[second_key[:17]] == {
        "requests": 1,
        "prompt_tokens": request_usage["prompt_tokens"],
        "completion_tokens": request_usage["completion_tokens"],
        "total_tokens": request_usage["total_tokens"],
    }


def test_inference_validates_payload(client: TestClient, api_key: str) -> None:
    no_user = client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"model": "mock-echo-1", "messages": [{"role": "system", "content": "Hi"}]},
    )
    assert no_user.status_code == 400
    assert no_user.json()["message"]["code"] == "invalid_request"

    malformed = client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        content="{bad json",
    )
    assert malformed.status_code == 400
    assert malformed.headers["content-type"].startswith("application/json")
    assert malformed.json()["success"] is False


def test_inference_streams_openai_compatible_sse_chunks(
    registered_client: TestClient, api_key: str
) -> None:
    payload = inference_payload()
    payload["stream"] = True

    with registered_client.stream(
        "POST",
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
    ) as response:
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["x-accel-buffering"] == "no"
        data_lines = [line.removeprefix("data: ") for line in response.iter_lines() if line]

    assert data_lines[-1] == "[DONE]"
    chunks = [json.loads(line) for line in data_lines[:-1]]
    assert chunks[0]["choices"][0] == {
        "index": 0,
        "delta": {"role": "assistant"},
        "finish_reason": None,
    }
    assert all(chunk["object"] == "chat.completion.chunk" for chunk in chunks)
    assert len({chunk["id"] for chunk in chunks}) == 1
    assert all(chunk["success"] is True and chunk["message"] == {} for chunk in chunks)

    streamed_content = "".join(chunk["choices"][0]["delta"].get("content", "") for chunk in chunks)
    assert streamed_content == "Echo: 最後一則問題"

    final_chunk = chunks[-1]
    assert final_chunk["choices"][0] == {
        "index": 0,
        "delta": {},
        "finish_reason": "stop",
    }
    usage = final_chunk["usage"]
    assert usage["total_tokens"] == usage["prompt_tokens"] + usage["completion_tokens"]

    account_usage = registered_client.get("/api/me").json()["message"]["keys"][0]["usage"]
    assert account_usage == {"requests": 1, **usage}


def test_streaming_errors_remain_json(client: TestClient) -> None:
    payload = inference_payload()
    payload["stream"] = True
    response = client.post("/v1/chat/completions", json=payload)

    assert response.status_code == 401
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["message"]["code"] == "invalid_api_key"


def test_stream_false_keeps_regular_json_response(client: TestClient, api_key: str) -> None:
    payload = inference_payload()
    payload["stream"] = False
    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json=payload,
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")
    assert response.json()["object"] == "chat.completion"
