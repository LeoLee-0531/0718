# SSE Streaming Contract

`POST /v1/chat/completions` supports OpenAI-compatible Server-Sent Events when
the JSON request contains `"stream": true`. Omitting `stream`, or setting it to
`false`, keeps the existing JSON response.

## Request

```json
{
  "model": "mock-echo-1",
  "messages": [{"role": "user", "content": "Hello"}],
  "stream": true
}
```

The same Bearer authentication and payload validation rules apply to both
modes. Authentication and validation errors are returned as regular JSON with
their existing `400` or `401` status before an event stream is opened.

## Response

A successful streaming response uses `Content-Type: text/event-stream` and
disables intermediary buffering. Each event is separated by a blank line:

```text
data: {"id":"chatcmpl_...","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"role":"assistant"},"finish_reason":null}]}

data: {"id":"chatcmpl_...","object":"chat.completion.chunk","choices":[{"index":0,"delta":{"content":"Echo: Hello"},"finish_reason":null}]}

data: {"id":"chatcmpl_...","object":"chat.completion.chunk","choices":[{"index":0,"delta":{},"finish_reason":"stop"}],"usage":{"prompt_tokens":2,"completion_tokens":3,"total_tokens":5}}

data: [DONE]

```

All JSON chunks share one completion ID, creation timestamp, and model. They
also include the service fields `success: true` and `message: {}`. Clients
reconstruct the assistant response by concatenating each `delta.content`.

The final JSON chunk contains the complete usage object, and `total_tokens`
equals `prompt_tokens + completion_tokens`. Per-key usage is incremented once
when the stream reaches this successful completion event. A stream disconnected
before completion is not counted.

## curl

Use `--no-buffer` so curl prints events as they arrive:

```sh
curl --no-buffer -X POST http://127.0.0.1:8000/v1/chat/completions \
  -H 'Content-Type: application/json' \
  -H 'Authorization: Bearer llm_live_REPLACE_ME' \
  -d '{"model":"mock-echo-1","messages":[{"role":"user","content":"Hello"}],"stream":true}'
```
