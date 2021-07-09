import requests
from flask import current_app


def translate(text, dest_language):
    if 'MS_TRANSLATOR_KEY' not in current_app.config or not current_app.config['MS_TRANSLATOR_KEY']:
        return 'Error: the translation service is not configured.'
    headers = {'Ocp-Apim-Subscription-Key': current_app.config['MS_TRANSLATOR_KEY'], 'Content-Type': 'application/json'}

    response = requests.post(
        f'https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to={dest_language}',
        headers=headers,
        json=text
    )

    if response.status_code != 200:
        return 'Error: the translation service failed.'

    return response.json()[0]['translations'][0]['text']
