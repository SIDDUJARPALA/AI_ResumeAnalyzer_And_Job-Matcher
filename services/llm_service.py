import json

import requests
from flask import current_app


class LLMServiceError(RuntimeError):
    pass


PROVIDERS = {
    "groq": {
        "api_key_config": "GROQ_API_KEY",
        "model_config": "GROQ_MODEL",
        "endpoint": "https://api.groq.com/openai/v1/chat/completions",
        "key_name": "GROQ_API_KEY",
    },
}


def generate_json(system_prompt, user_prompt):
    provider_name = current_app.config["LLM_PROVIDER"]
    provider = PROVIDERS.get(provider_name)
    if provider is None:
        raise LLMServiceError(
            "LLM_PROVIDER must be set to 'groq' in your .env file."
        )

    api_key = current_app.config[provider["api_key_config"]]
    if not api_key:
        raise LLMServiceError(
            f"{provider['key_name']} is not configured. Add it to your .env file "
            f"and set LLM_PROVIDER={provider_name}."
        )

    payload = {
        "model": current_app.config[provider["model_config"]],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
    try:
        response = requests.post(
            provider["endpoint"],
            headers={"Authorization": f"Bearer {api_key}"},
            json=payload,
            timeout=(10, 90),
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        data = json.loads(content)
    except requests.Timeout as error:
        raise LLMServiceError(
            f"The {provider_name} API request timed out. Please try again."
        ) from error
    except requests.HTTPError as error:
        response = error.response
        if response is None:
            raise LLMServiceError(
                f"No HTTP response was received from the {provider_name} API. "
                "Check your internet connection, VPN/proxy, firewall, or TLS inspection, "
                "then restart the application and try again."
            ) from error

        status = response.status_code
        detail = _api_error_detail(response, api_key)
        if status == 401:
            explanation = (
                "The API rejected the key. Check that it is an API key from the provider "
                "dashboard, has no extra spaces, and belongs to an account with API access."
            )
        elif status == 403:
            explanation = (
                "The account or project is not allowed to use this API or model. "
                "Check project permissions and model access."
            )
        elif status == 429:
            explanation = (
                "The API account is rate-limited or has no available API quota. "
                "Check API billing, usage limits, and rate limits."
            )
        elif status == 400:
            explanation = (
                "The API rejected the request. Check that the selected model is available "
                "to your account and supports JSON response mode."
            )
        elif status == 404:
            explanation = (
                "The requested model or endpoint was not found. Verify the model ID in your "
                "Groq Console and update GROQ_MODEL in .env."
            )
        else:
            explanation = "Check the provider status and API settings."

        message = f"The {provider_name} API returned HTTP {status}. {explanation}"
        if detail:
            message += f" Provider detail: {detail}"
        raise LLMServiceError(message) from error
    except requests.ConnectionError as error:
        raise LLMServiceError(
            f"Could not connect to the {provider_name} API. Check your internet connection, "
            "VPN/proxy, firewall, or TLS inspection, then try again."
        ) from error
    except (requests.RequestException, KeyError, IndexError, TypeError, ValueError) as error:
        raise LLMServiceError(
            f"The {provider_name} API response was unavailable or malformed. Please try again."
        ) from error

    if not isinstance(data, dict):
        raise LLMServiceError(f"The {provider_name} API returned JSON in an unexpected format.")
    return data


def _api_error_detail(response, api_key):
    try:
        error_data = response.json().get("error")
    except (ValueError, AttributeError):
        return ""
    if not isinstance(error_data, dict):
        return ""

    detail = error_data.get("message") or error_data.get("code") or error_data.get("type")
    if not isinstance(detail, str):
        return ""
    detail = detail.replace(api_key, "[redacted]").strip()
    return detail[:300]
