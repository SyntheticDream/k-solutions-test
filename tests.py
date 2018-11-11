#! /usr/bin/python3

import unittest

from app import app, submit, generate_sign, get_shop_id

from forms import PaymentForm

class PaytrioTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True 

    def test_generate_sign(self):

        self.assertEqual(generate_sign(amount='1.00',
                                       currency='980',
                                       shop_id=get_shop_id(),
                                       shop_invoice_id='101'),
                         'e932ef00dcd0988c3015f44e344b184b')

    def test_validate_form(self):

        self.assertEqual(self.app.post('/submit?', data=dict(amount='1', currency='980', description='101')).data.decode(),
                         'Malformed request')

        self.assertEqual(self.app.post('/submit?', data=dict(amount='1.00', currency='1', description='101')).data.decode(),
                         'Malformed request')

        self.assertEqual(self.app.post('/submit?', data=dict(amount='1.00', currency='980', description='a'*9000)).data.decode(),
                         'Malformed request')


    def test_combobox_requests(self):
        self.assertTrue('TIP' in self.app.post('/submit?', data=dict(amount='1.00', currency='840', description='desc')).data.decode())

        # sends request to API
        self.assertTrue('API' in self.app.post('/submit?', data=dict(amount='1.00', currency='978', description='desc')).data.decode())

    
    def test_invoice_form(self):
        
        # sends request to API
        self.assertNotEqual(self.app.post('/submit?', data=dict(amount='1.00', currency='978', description='desc')).data.decode(),
                            'Malformed request')

if __name__ == '__main__':
    unittest.main()