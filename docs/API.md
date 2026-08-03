# Eixora TTS Engine — API Reference

**Base URL (local):** `http://localhost:8100`  
**Base URL (production):** Your Railway service URL (e.g. `https://eixora-tts-engine.up.railway.app`)

All TTS and voice endpoints require authentication via the `X-API-Key` header. Health and metrics endpoints do not require authentication.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Request Schemas](#request-schemas)
3. [POST /api/v1/tts](#post-apiv1tts)
4. [POST /api/v1/tts/stream](#post-apiv1ttsstream)
5. [GET /api/v1/voices](#get-apiv1voices)
6. [GET /health](#get-health)
7. [GET /health/ready](#get-healthready)
8. [GET /metrics](#get-metrics)
9. [Supported Emotions](#supported-emotions)
10. [Inline Pause Tags](#inline-pause-tags)
11. [Error Responses](#error-responses)

---

## Authentication

Protected endpoints require an API key sent in the `X-API-Key` request header.

```
X-API-Key: your-secret-api-key
```

The server validates the key against the `TTS_API_KEYS` environment variable (a comma-separated list of valid keys). Requests with a missing or invalid key receive a `401 Unauthorized` response.

**Protected endpoints:** `POST /api/v1/tts`, `POST /api/v1/tts/stream`, `GET /api/v1/voices`  
**Unprotected endpoints:** `GET /health`, `GET /health/ready`, `GET /metrics`

---

## Request Schemas

### TTSRequest

Used by both `POST /api/v1/tts` and `POST /api/v1/tts/stream`.

| Field     | Type          | Constraints         | Default     | Description                                                       |
|-----------|---------------|---------------------|-------------|-------------------------------------------------------------------|
| `text`    | `string`      | `min_length=1`, required | —      | Text to synthesize. Supports inline `[pause:500ms]` tags.         |
| `voice`   | `string\|null` | —                  | `null`      | Voice ID (e.g. `af_heart`). Falls back to server default if null. |
| `lang`    | `string\|null` | —                  | `null`      | Kokoro language code (e.g. `a` for American English). Falls back to server default if null. |
| `emotion` | `string` (enum) | See [Supported Emotions](#supported-emotions) | `neutral` | Emotion/prosody modifier. |
| `speed`   | `float`       | `0.5 ≤ speed ≤ 2.0` | `1.0`      | Speaking rate multiplier. `0.5` = half speed, `2.0` = double speed. |

---

## POST /api/v1/tts

Synthesizes text to audio and returns a complete WAV file.

**Auth required:** Yes (`X-API-Key`)

### Request

- **Content-Type:** `application/json`
- **Body:** [TTSRequest](#ttsrequest)

### Response

- **Content-Type:** `audio/wav`
- **Body:** WAV audio (PCM 16-bit, mono)

**Response headers:**

| Header                 | Type    | Description                                              |
|------------------------|---------|----------------------------------------------------------|
| `X-Audio-Duration-S`   | `float` | Duration of synthesized audio in seconds (3 decimal places). |
| `X-Real-Time-Factor`   | `float` | `process_time / audio_duration` — lower is faster.      |
| `X-Segments`           | `int`   | Number of text segments synthesized.                     |

### Errors

| Status | Code              | Description                                            |
|--------|-------------------|--------------------------------------------------------|
| `401`  | `unauthorized`    | Missing or invalid `X-API-Key` header.                 |
| `400`  | `validation_error`| Request body failed validation (e.g. empty `text`).   |
| `429`  | `rate_limited`    | Too many requests — default limit is 60/minute.        |
| `503`  | `model_not_loaded`| Model is not yet loaded or failed to load.             |

### curl Example

```bash
curl -X POST http://localhost:8100/api/v1/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{
    "text": "Hello, world! Welcome to Eixora.",
    "voice": "af_heart",
    "emotion": "happy",
    "speed": 1.0
  }' \
  --output speech.wav
```

The response body is a WAV file written to `speech.wav`. Check the response headers for duration and performance metadata:

```bash
curl -X POST http://localhost:8100/api/v1/tts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{"text": "Hello, world!"}' \
  -D - \
  --output speech.wav
```

---

## POST /api/v1/tts/stream

Synthesizes text and streams audio segments in real time via NDJSON (newline-delimited JSON). Audio starts arriving before the full text is synthesized, giving low time-to-first-byte for long inputs.

**Auth required:** Yes (`X-API-Key`)

### Request

- **Content-Type:** `application/json`
- **Body:** [TTSRequest](#ttsrequest)

### Response

- **Content-Type:** `application/x-ndjson`
- **Transfer-Encoding:** `chunked`
- **Body:** A stream of newline-delimited JSON objects, one per line.

### NDJSON Event Types

Events are emitted in this order:

#### `start`

Emitted once at the beginning of the stream, before any audio data.

| Field         | Type     | Description                              |
|---------------|----------|------------------------------------------|
| `type`        | `string` | Always `"start"`.                        |
| `sample_rate` | `int`    | Audio sample rate in Hz (e.g. `24000`).  |
| `format`      | `string` | Always `"pcm_s16le"` (PCM 16-bit LE).   |
| `channels`    | `int`    | Always `1` (mono).                       |

```json
{"type": "start", "sample_rate": 24000, "format": "pcm_s16le", "channels": 1}
```

#### `audio_chunk`

Emitted once per synthesized text segment. Multiple `audio_chunk` events are sent for longer texts.

| Field           | Type      | Description                                                                 |
|-----------------|-----------|-----------------------------------------------------------------------------|
| `type`          | `string`  | Always `"audio_chunk"`.                                                     |
| `index`         | `int`     | Zero-based segment index.                                                   |
| `text`          | `string`  | The text that was synthesized for this segment.                             |
| `is_final`      | `boolean` | `true` if this is the last segment in the stream.                           |
| `pause_after_ms`| `int`     | Silence in milliseconds to insert after this chunk before the next one.     |
| `data`          | `string`  | Base64-encoded PCM16LE audio bytes. Decode and play in order.               |

```json
{"type": "audio_chunk", "index": 0, "text": "Hello, world!", "is_final": false, "pause_after_ms": 350, "data": "<base64-encoded-pcm16le>"}
```

#### `end`

Emitted once when all segments have been sent.

| Field                  | Type    | Description                              |
|------------------------|---------|------------------------------------------|
| `type`                 | `string`| Always `"end"`.                          |
| `total_segments`       | `int`   | Total number of `audio_chunk` events sent. |
| `total_process_time_ms`| `float` | Total synthesis processing time in milliseconds. |

```json
{"type": "end", "total_segments": 3, "total_process_time_ms": 412.3}
```

#### `error`

Emitted if synthesis fails mid-stream. The stream closes after this event.

| Field     | Type     | Description                    |
|-----------|----------|--------------------------------|
| `type`    | `string` | Always `"error"`.              |
| `message` | `string` | Human-readable error message.  |

```json
{"type": "error", "message": "Model inference failed: ..."}
```

### Errors

| Status | Code              | Description                                            |
|--------|-------------------|--------------------------------------------------------|
| `401`  | `unauthorized`    | Missing or invalid `X-API-Key` header.                 |
| `400`  | `validation_error`| Request body failed validation.                        |
| `429`  | `rate_limited`    | Too many requests — default limit is 60/minute.        |

> **Note:** Synthesis errors that occur after the stream has started are delivered as an `error` event inside the stream rather than as an HTTP error status.

### curl Example

```bash
curl -X POST http://localhost:8100/api/v1/tts/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{
    "text": "This is a long passage that will be streamed segment by segment.",
    "voice": "af_heart",
    "emotion": "neutral",
    "speed": 1.0
  }'
```

Each line of the response is a JSON event. To pretty-print each event:

```bash
curl -s -X POST http://localhost:8100/api/v1/tts/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-secret-api-key" \
  -d '{"text": "Hello. How are you?"}' \
  | while IFS= read -r line; do echo "$line" | python3 -m json.tool; done
```

---

## GET /api/v1/voices

Returns the list of available voice IDs and the server's default voice.

**Auth required:** Yes (`X-API-Key`)

### Response

- **Content-Type:** `application/json`

| Field           | Type            | Description                                   |
|-----------------|-----------------|-----------------------------------------------|
| `voices`        | `array[string]` | List of available voice IDs.                  |
| `default_voice` | `string`        | The server's configured default voice ID.     |

```json
{
  "voices": ["af_heart", "af_bella", "am_adam", "bf_emma"],
  "default_voice": "af_heart"
}
```

### Errors

| Status | Code           | Description                              |
|--------|----------------|------------------------------------------|
| `401`  | `unauthorized` | Missing or invalid `X-API-Key` header.   |

### curl Example

```bash
curl http://localhost:8100/api/v1/voices \
  -H "X-API-Key: your-secret-api-key"
```

---

## GET /health

Returns the current health status of the service, including model load state and uptime.

**Auth required:** No

### Response

- **Content-Type:** `application/json`

| Field          | Type      | Description                                                               |
|----------------|-----------|---------------------------------------------------------------------------|
| `status`       | `string`  | `"ok"` if the model is loaded and ready; `"degraded"` otherwise.         |
| `model_loaded` | `boolean` | Whether the Kokoro model is fully loaded.                                 |
| `device`       | `string`  | Inference device in use: `"cpu"`, `"cuda"`, etc.                         |
| `uptime_s`     | `float`   | Seconds since the server process started.                                 |

```json
{
  "status": "ok",
  "model_loaded": true,
  "device": "cpu",
  "uptime_s": 142.5
}
```

### curl Example

```bash
curl http://localhost:8100/health
```

---

## GET /health/ready

Lightweight readiness probe. Used by Railway and other orchestration infrastructure to determine if the service can accept traffic.

**Auth required:** No

### Response

- **Content-Type:** `application/json`

| Field   | Type      | Description                                       |
|---------|-----------|---------------------------------------------------|
| `ready` | `boolean` | `true` if the model is loaded; `false` otherwise. |

```json
{"ready": true}
```

### curl Example

```bash
curl http://localhost:8100/health/ready
```

---

## GET /metrics

Returns Prometheus-format metrics for scraping by a Prometheus server or compatible monitoring tool.

**Auth required:** No

### Response

- **Content-Type:** `text/plain; version=0.0.4; charset=utf-8`
- **Body:** Prometheus text exposition format

### Exposed Metrics

| Metric                       | Type      | Labels                      | Description                                                   |
|------------------------------|-----------|-----------------------------|---------------------------------------------------------------|
| `tts_requests_total`         | Counter   | `endpoint`, `status`        | Total number of TTS requests, labelled by endpoint and outcome (`success` or `error`). |
| `tts_characters_total`       | Counter   | —                           | Total number of characters submitted for synthesis.           |
| `tts_latency_seconds`        | Histogram | `endpoint`                  | End-to-end synthesis latency in seconds, labelled by endpoint. |
| `tts_real_time_factor`       | Histogram | —                           | Ratio of processing time to audio duration. Values below `1.0` mean faster-than-real-time. |

**`endpoint` label values:** `tts`, `tts_stream`  
**`status` label values:** `success`, `error`

### Example output

```
# HELP tts_requests_total Total TTS requests
# TYPE tts_requests_total counter
tts_requests_total{endpoint="tts",status="success"} 42.0
tts_requests_total{endpoint="tts",status="error"} 1.0
tts_requests_total{endpoint="tts_stream",status="success"} 17.0

# HELP tts_characters_total Total characters synthesized
# TYPE tts_characters_total counter
tts_characters_total_total 12543.0

# HELP tts_latency_seconds End-to-end synthesis latency in seconds
# TYPE tts_latency_seconds histogram
tts_latency_seconds_bucket{endpoint="tts",le="0.25"} 28.0
...

# HELP tts_real_time_factor process_time / audio_duration (lower is better)
# TYPE tts_real_time_factor histogram
tts_real_time_factor_bucket{le="0.5"} 55.0
...
```

### curl Example

```bash
curl http://localhost:8100/metrics
```

---

## Supported Emotions

The `emotion` field on `TTSRequest` accepts one of the following values. Emotion is approximated via prosody adjustments (speed multiplier, pitch shift, energy gain) applied on top of the base voice rendering.

| Value       | Speed Mult. | Pitch Shift  | Energy Gain | Character                                 |
|-------------|-------------|--------------|-------------|-------------------------------------------|
| `neutral`   | 1.00×       | 0.0 semitones| 0.0 dB      | Default, balanced delivery.               |
| `happy`     | 1.10×       | +1.5 semitones| +1.5 dB    | Upbeat, slightly faster.                  |
| `sad`       | 0.90×       | −2.0 semitones| −2.0 dB    | Slower, lower pitch, quieter.             |
| `angry`     | 1.05×       | +0.5 semitones| +3.5 dB    | Slightly faster, louder, more intense.    |
| `excited`   | 1.18×       | +2.5 semitones| +3.0 dB    | Fast, high-energy delivery.               |
| `calm`      | 0.92×       | −0.5 semitones| −1.0 dB    | Slightly slower, slightly quieter.        |

> **Note:** This is a v1 heuristic implementation. Kokoro-82M does not have native emotion conditioning — these adjustments are approximations. See `docs/ROADMAP.md` for the planned v2 upgrade.

---

## Inline Pause Tags

You can insert explicit pauses anywhere in the input `text` using the `[pause:Nms]` syntax, where `N` is the duration in milliseconds.

**Syntax:** `[pause:500ms]`

**Example:**

```json
{
  "text": "First sentence. [pause:1000ms] Second sentence after a one second pause."
}
```

Inline pause tags override the default inter-segment pause logic at that position. Supported units: `ms` (milliseconds) only.

---

## Error Responses

All error responses from protected and unprotected endpoints use the following JSON structure:

```json
{
  "error_code": "unauthorized",
  "message": "Invalid or missing API key."
}
```

| Field        | Type     | Description                          |
|--------------|----------|--------------------------------------|
| `error_code` | `string` | Machine-readable error identifier.   |
| `message`    | `string` | Human-readable error description.    |

### Common HTTP Status Codes

| Status | Meaning                                                                          |
|--------|----------------------------------------------------------------------------------|
| `400`  | Bad request — validation failed (e.g. empty `text`, `speed` out of range).       |
| `401`  | Unauthorized — `X-API-Key` header is missing or does not match a valid key.      |
| `429`  | Too many requests — rate limit exceeded (default: 60 requests/minute per IP).    |
| `503`  | Service unavailable — model is not loaded or the engine failed to initialize.    |
