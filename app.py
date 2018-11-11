from flask import Flask, request, render_template
import requests
import json
import uuid

from forms import PaymentForm

import os
import hashlib
import logging
import logging.handlers

app = Flask(__name__)

available_currencies = {'USD': '840', 'EUR': '978'}

handler = logging.StreamHandler()

log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)

formatter = logging.Formatter(\
"%(asctime)s - %(levelname)s - %(name)s: \t%(message)s")
handler.setFormatter(formatter)

log.addHandler(handler)

def get_paytrio_secret():
    
    return os.environ['PAYTRIO_SECRET']


def get_shop_id():

    return os.environ['PAYTRIO_SHOP_ID']


def get_shop_invoice_id():

    invoice_id = uuid.uuid4().hex

    return invoice_id

def generate_sign(amount, currency, shop_id, shop_invoice_id, payway=None, description=None):

    if shop_invoice_id is None:
        shop_invoice_id = get_shop_invoice_id()

    secret = get_paytrio_secret()

    sign_string = '{0}:{1}{2}:{3}:{4}{5}'.format(amount,
                                   currency,
                                   (':{}').format(payway) if payway else '',
                                   shop_id,
                                   shop_invoice_id,
                                   secret)

    sign = hashlib.new('md5', sign_string.encode()).hexdigest()

    return sign



@app.route('/')
def homepage():

    return render_template('payform.html', available_currencies=available_currencies)

@app.route('/submit', methods=['POST'])
def submit():

    form = PaymentForm(request.form)

    if form.validate():
        payment_data = {'amount' : str(form.data['amount']),
                        'currency' : form.data['currency'],
                        'shop_id' : get_shop_id(),
                        'shop_invoice_id' : get_shop_invoice_id(),
                        'description': form.data['description']}

        log.info('Incoming payment. Details:')
        log.info(payment_data)


        if form.data['currency'] == available_currencies['USD']:

            payment_data['sign'] = generate_sign(**payment_data)

            log.info('Signed and rendering TIP payment button')

            return render_template('payform_tip.html', **payment_data)

        elif form.data['currency'] == available_currencies['EUR']:

            payment_data['payway'] = 'payeer_eur'
            payment_data['sign'] = generate_sign(**payment_data)

            log.info('Signed and and sending API invoice request')

            h = {'Content-Type': 'application/json'}
            r = requests.post('https://central.pay-trio.com/invoice', data=json.dumps(payment_data), headers=h)

            if r.json()['result'] == 'ok':

                log.info('Request success. Rendering API payment button')
                return render_template('payform_invoice.html', data=r.json()['data'])

            else:
                log.error('Request failure. Details:')
                log.error(r.json())
                return 'Malformed request', 403

    else:
        return 'Malformed request', 403

    
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
