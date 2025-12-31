# Executor Configuration Guide

This guide details the configuration and input requirements for each executor in the AI Agent Framework.

## 1. APICallerExecutor
**Identifier**: `APICallerExecutor`
**Description**: Makes HTTP requests to external APIs.

### Configuration (`config`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `url` | string | **Yes** | The full URL to call. |
| `method` | string | No | HTTP method (`GET`, `POST`, etc.). Default: `GET`. |
| `headers` | dict | No | HTTP headers. |
| `params` | dict | No | Query parameters. |
| `json` | dict | No | JSON body for the request. |

### Inputs (`inputs`)
*Not directly used by `execute` method, but keys in `config` can be templated using input values if using the `ToolExecutor` (wait, `APICallerExecutor` doesn't strictly support templating in `execute` natively based on the code check, but `ToolExecutor` does. Double check code: `APICallerExecutor` implementation uses values directly from config. `ToolExecutor` supports templating).*

**Note**: The current `APICallerExecutor` implementation reads `url`, `params` etc directly from `config`. If you need dynamic values, you should resolve them in the workflow engine before passing to the executor or use `ToolExecutor`.

---

## 2. DatabaseExecutor
**Identifier**: `DatabaseExecutor`
**Description**: Persists data to the database using SQLAlchemy models.

### Configuration (`config`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `model_class` | Type | **Yes** | The SQLAlchemy model class to instantiate. |

### Inputs (`inputs`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `payload` | dict | No | dictionary matching model fields. |

---

## 3. LLMExecutor
**Identifier**: `LLMExecutor`
**Description**: Handles LLM operations like completion, classification, and extraction.

### Configuration (`config`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `api_key` | string | No | OpenAI API Key. Defaults to env var `OPENAI_API_KEY`. |

### Inputs (`inputs`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `task_type` | string | **Yes** | One of: `classify`, `extract`, `completion`. |
| `text` | string | Conditional | Required for `classify` and `extract`. |
| `document_type` | string | Conditional | Required for `extract` (e.g., `aadhaar`, `pan`). |
| `messages` | list | Conditional | Required for `completion` (unless `prompt` is used). |
| `prompt` | string | Conditional | Alternative for `completion`. |
| `model` | string | No | Model name (e.g. `gpt-4o`). Default: `gpt-4o-mini`. |

---

## 4. OcrExecutor
**Identifier**: `OcrExecutor`
**Description**: Extracts text from images/documents.

### Configuration (`config`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `USE_OPENVINO` | bool | No | valid only if openvino installed. |
| `OPENVINO_MODEL_PATH`| string | No | path to xml model. |

### Inputs (`inputs`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `document` | string/bytes | **Yes** | Path or bytes of the image/document. |

---

## 5. RAGRetrieverExecutor
**Identifier**: `RAGRetrieverExecutor`
**Description**: Retrieves documents context.

### Configuration (`config`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `k` | int | No | Number of results to return. Default: 5. |

### Inputs (`inputs`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `query` | string | **Yes** | Search query string. |

---

## 6. ScriptExecutor
**Identifier**: `ScriptExecutor`
**Description**: Runs local scripts.

### Configuration (`config`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `mode` | string | No | `python_file`, `python_inline`, or `shell`. Default: `python_file`. |
| `path` | string | Conditional| Required if mode is `python_file`. |
| `code` | string | Conditional| Required if mode is `python_inline`. |
| `command_template`| string | Conditional| Required if mode is `shell`. |
| `args_template` | list | No | List of args for `python_file`. Support `{placeholder}`. |

### Inputs (`inputs`)
*Used to fill placeholders in `args_template`, `code`, or `command_template`.*

---

## 7. ToolExecutor
**Identifier**: `ToolExecutor`
**Description**: Generic tool execution (web requests, search).

### Configuration (`config`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `tool` | string | No | `web_request` (default), `google_search`. |
| `url` | string | Conditional| Required for `web_request`. Supports `{placeholder}` using inputs. |
| `method` | string | No | HTTP method. |

### Inputs (`inputs`)
*Various, depends on placeholders in config.*
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `query` | string | Conditional | Required for `google_search`. |

---

## 8. ValidationExecutor
**Identifier**: `ValidationExecutor`
**Description**: Validates structured data.

### Configuration (`config`)
*None specific.*

### Inputs (`inputs`)
| Key | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `data` | dict | **Yes** | The data to validate. |
| `rules` | dict | No | Custom regex rules {field: pattern}. |
