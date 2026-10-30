import io
import json
import unittest
from unittest.mock import patch
import urllib.error
from PIL import Image
from deepseek_player import validate, ask


class PlayerBoundaryTests(unittest.TestCase):
    def action(self, **extra):
        return dict(action='key', key='q', observation='技能就绪', reason='尝试技能', **extra)

    def test_allowed_inputs_and_invalid_provider_output(self):
        self.assertEqual(validate(self.action())['key'], 'q')
        for bad in [None, [], {}, {**self.action(), 'key': 'F11'},
                    {**self.action(), 'key': 'Alt+F4'},
                    {**self.action(), 'action': 'shell'},
                    {**self.action(), 'action': 'click', 'x': float('nan'), 'y': .5},
                    {**self.action(), 'action': 'click', 'x': -1, 'y': .5},
                    {**self.action(), 'action': 'wait', 'seconds': 900},
                    {**self.action(), 'observation': None}]:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                validate(bad)

    def test_request_contains_only_prompt_screenshot_and_recent_actions(self):
        reply = {'choices': [{'message': {'content': json.dumps(self.action())}}]}
        with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(reply).encode())) as request:
            result = ask('unit-test-secret', 'deepseek-flash', 'player rules', Image.new('RGB', (10, 10)), [])
        self.assertEqual(result['key'], 'q')
        req = request.call_args.args[0]
        self.assertEqual(req.full_url, 'https://api.deepseek.com/chat/completions')
        body = json.loads(req.data)
        self.assertNotIn('unit-test-secret', req.data.decode())
        self.assertEqual(len(body['messages']), 2)
        self.assertTrue(body['messages'][1]['content'][1]['image_url']['url'].startswith('data:image/png;base64,'))

    def test_http_error_does_not_expose_key_or_provider_body(self):
        error = urllib.error.HTTPError('https://api.deepseek.com', 401, 'secret-in-provider-error', {}, None)
        with patch('urllib.request.urlopen', side_effect=error), self.assertRaisesRegex(RuntimeError, 'HTTP 401') as caught:
            ask('unit-test-secret', 'deepseek-flash', 'rules', Image.new('RGB', (10, 10)), [])
        self.assertNotIn('secret-in-provider-error', str(caught.exception))

    def test_grok_uses_xai_endpoint_and_same_action_validation(self):
        reply = {'choices': [{'message': {'content': json.dumps(self.action())}}]}
        with patch('urllib.request.urlopen', return_value=io.BytesIO(json.dumps(reply).encode())) as request:
            result = ask('fake-xai-key', 'grok-4', 'Grok player rules', Image.new('RGB', (10, 10)), [], 'grok')
        req = request.call_args.args[0]
        self.assertEqual(req.full_url, 'https://api.x.ai/v1/chat/completions')
        self.assertEqual(json.loads(req.data)['model'], 'grok-4')
        self.assertNotIn('fake-xai-key', req.data.decode())
        self.assertEqual(result['key'], 'q')

    def test_unknown_provider_cannot_redirect_credentials(self):
        with patch('urllib.request.urlopen') as request, self.assertRaises(KeyError):
            ask('fake-key', 'model', 'rules', Image.new('RGB', (10, 10)), [], 'https://untrusted.invalid')
        request.assert_not_called()


if __name__ == '__main__':
    unittest.main()
