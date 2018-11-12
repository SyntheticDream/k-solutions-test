import os
from hashlib import sha256
import logging.handlers
import json
import uuid

from flask import Flask, request, render_template, redirect
import requests

from forms import PaymentForm

app = Flask(__name__)

available_currencies = {
    'USD': '840',  # Bill Piastrix      straight redirect
    'EUR': '978',  # Pay                Pay form
    'RUB': '643'   # Invoice Payeer     Invoice form
}

handler = logging.StreamHandler()

log = logging.getLogger('werkzeug')
log.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s: \t"
                              "%(message)s")
handler.setFormatter(formatter)

log.addHandler(handler)


def get_secret():

    return os.environ['secretKey']


def get_shop_id():

    return os.environ['shop_id']


def get_shop_order_id():

    invoice_id = uuid.uuid4().hex

    return invoice_id


def generate_sign(**kwargs):
    if kwargs.get('description'):
        del kwargs['description']

    params = list(kwargs.keys())
    params.sort()

    string = ''

    for key in params:
        string += f':{kwargs[key]}'

    string = string[1:] + get_secret()

    sign = sha256(string.encode()).hexdigest()

    return sign


@app.route('/')
def homepage():

    return render_template('payform.html',
                           available_currencies=available_currencies)


@app.route('/submit', methods=['POST'])
def submit():

    form = PaymentForm(request.form)

    log.info('Incoming payment. Details:')

    if form.validate():
        amount = str(round(form.data['amount'], 2))  # 100 -> 100.00
        c = form.data['currency']

        payment_data = {
            'amount': amount,
            'currency': c,
            'shop_id': get_shop_id(),
            'shop_order_id': get_shop_order_id(),
            'description': form.data['description']
        }

        log.info(payment_data)

        if c == available_currencies['EUR']:

            payment_data['sign'] = generate_sign(**payment_data)

            log.info('Rendering "Pay method" form.')

            return render_template('payform_pay.html', **payment_data)

        elif c == available_currencies['RUB']:
            payment_data['payway'] = 'payeer_rub'
            payment_data['sign'] = generate_sign(**payment_data)

            log.info('Posting to Piastrix for confirmation')

            h = {'Content-Type': 'application/json'}
            r = requests.post('https://core.piastrix.com/invoice/create',
                              data=json.dumps(payment_data),
                              headers=h)
            res = r.json()
            data = res['data']

            if res['result'] is True and res['message'] == 'Ok':

                log.info(data)
                log.info('Request succeded. Rendering "Invoice method" button')
                return render_template('payform_invoice.html',
                                       data=data)

            else:
                log.error('Request failure. Details:')
                log.error(res)
                return 'Malformed request', 403

        elif c == available_currencies['USD']:

            payment_data['shop_amount'] = payment_data.pop('amount')
            payment_data['shop_currency'] = payment_data.pop('currency')
            payment_data['payer_currency'] = payment_data['shop_currency']

            payment_data['sign'] = generate_sign(**payment_data)

            log.info('Posting to Piastrix for confirmation')

            h = {'Content-Type': 'application/json'}
            r = requests.post('https://core.piastrix.com/bill/create',
                              data=json.dumps(payment_data),
                              headers=h)
            res = r.json()
            data = res['data']

            if res['result'] is True and res['message'] == 'Ok':

                log.info('Request succeeded. Redirecting via "Bill method"')
                return redirect(data['url'], code=302)

            else:
                log.error('Request failed. Details:')
                log.error(res)
                return f'Malformed request. Details:<br>{res}', 403

    else:
        errs = {}
        for f, e in form.errors.items():
            errs[f] = e

        log.error('Bad input:')
        log.error(errs)

        return f'Bad input<br>{errs}', 403

    
if __name__ == '__main__':
    app.run(debug=True, use_reloader=True)
