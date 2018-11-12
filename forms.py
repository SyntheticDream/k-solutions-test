from wtforms import Form, DecimalField, StringField, validators


class PaymentForm(Form):
    amount = DecimalField('amount',
                          [
                              validators.InputRequired(),
                              validators.NumberRange(min=0, max=1_000_000)
                          ])

    currency = StringField('currency',
                           [
                               validators.AnyOf(['978', '840', '643']),
                               validators.InputRequired()
                           ])

    description = StringField('description',
                              [
                                  validators.Length(min=0, max=1024)
                              ])
