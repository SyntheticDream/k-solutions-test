from wtforms import Form, DecimalField, StringField, validators, ValidationError


def float_check(form, field):

    number = str(field.data)

    if not (len(number.split('.')) == 2 and len(number.split('.')[1]) == 2):
        raise ValidationError('Value is not a floating point number')


class PaymentForm(Form):
    amount = DecimalField('amount', [validators.InputRequired(),
                                    validators.NumberRange(min=0),
                                    float_check])

    currency = StringField('currency', [validators.AnyOf(['980', '840', '643', '978']),
                                        validators.InputRequired()])

    description = StringField('description', [validators.InputRequired(),
                                              validators.Length(min=0, max=1024)])