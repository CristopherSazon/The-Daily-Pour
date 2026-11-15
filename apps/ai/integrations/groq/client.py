import json

from django.conf import settings


class GroqError(Exception):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class GroqClient:
    def complete(self, instructions, messages, *, schema, name, model):
        if not settings.GROQ_API_KEY:
            raise GroqError('missing_key')
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=settings.GROQ_API_KEY,
                base_url=settings.GROQ_BASE_URL,
                timeout=20,
            )
            response = client.chat.completions.create(
                model=model,
                messages=[{'role': 'system', 'content': instructions}, *messages],
                response_format={
                    'type': 'json_schema',
                    'json_schema': {
                        'name': name,
                        'strict': True,
                        'schema': schema,
                    },
                },
            )
            parsed = json.loads(response.choices[0].message.content or '')
        except GroqError:
            raise
        except Exception as exc:
            raise GroqError(error_code(exc)) from exc
        if not isinstance(parsed, dict):
            raise GroqError('unavailable')
        return parsed


def error_code(exc):
    body = getattr(exc, 'body', None)
    if isinstance(body, dict) and isinstance(body.get('error'), dict):
        body = body['error']
    if not isinstance(body, dict):
        body = {}
    code = str(body.get('code') or '')
    kind = str(body.get('type') or '')
    if code in {'credit_balance_exhausted', 'rate_limit_exceeded'} or kind in {'insufficient_quota', 'rate_limit_exceeded'}:
        return 'rate_limit'
    return 'unavailable'
