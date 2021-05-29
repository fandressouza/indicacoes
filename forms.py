from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, FileField, BooleanField, SelectField
from wtforms.fields.html5 import TelField
from wtforms.widgets import TextArea
from wtforms.validators import InputRequired, Length, EqualTo, NoneOf, Email
from flask_bootstrap import Bootstrap

category_main = ("", "Alimentação", "Serviços construtivos", "Transportes", "Entregas (Motoboy)", "Imóveis",  "Serviços outros")

category_choices = ("", "Doces", "Salgados", "Bebidas", "Pizzas", "Bolos", "Esfihas"
 "Cuidados Pessoais", "Locação de casas", "Locação de veículos", "Faxina", "Pintura de casas", "Reformas"
 "Empreiteiras", "Moveis Planejados", "Vidros", "Mecânica", "Passeios", "Organização de festas"
 "Gesso", "Pets (cuidados animais)", "Jardinagem", "Piscineiro",
 "Câmeras segurança", "Alarme segurança", "Chaveiro", "Caçamba", "Contratacao de Seguros",
 "Farmácia", "Xerox", "Eletricista", "Montador de móveis", "Dedetização", "Cursos", "Venda de Gas", "Higienizacao de estofados", "Outros")

class LoginForm(FlaskForm):
    email    = StringField('E-mail', validators=[InputRequired(), Email("Precisamos do seu emaiL!")])
    password = PasswordField('Senha', validators=[InputRequired(), Length(min=5, max=15, message="A senha deve ser entre 5 e 15 letras!")])


class RegisterForm(FlaskForm):
    email    = StringField('E-mail', validators=[InputRequired(), Email("Precisamos do seu E-mail")])
    name    = StringField('Nome Completo', validators=[InputRequired()])
    password = PasswordField('Senha', [InputRequired(), EqualTo('repeat_password', message='As senhas devem ser iguais'), NoneOf(["password", "Password1234"], message="This password is too common", values_formatter=None)])
    repeat_password  = PasswordField('Repetir Senha')


class AddForm(FlaskForm):
    #name = StringField('Nome Completo', validators=[InputRequired()], render_kw={"placeholder": "Ex: Silvio Eduardo Vasconcelos"})
    offer = StringField('Nome da oferta', validators=[InputRequired()], render_kw={"placeholder": "Ex: \"Delicias de chocolate da Ju\""})
    phone = TelField('Numero de telefone', validators=[InputRequired()], render_kw={"placeholder": "Ex: 11000012222"})
    delivery = BooleanField('Faco entregas dentro do Ninho Verde 2')
    house_number = StringField('Lote e quadra se morar no Ninho Verde', render_kw={"placeholder": "Ex: JF14"})
    price = IntegerField("Valor por pessoa ou porção",validators=[InputRequired()] ,render_kw={"placeholder": "Ex: 25"})
    image_upload = FileField('')
    category_one = SelectField('Selecionar a categoria principal', choices=category_main, validators=[InputRequired()])
    category_two = SelectField('Selecionar a sub categoria', choices=category_choices, validators=[InputRequired()])
    description = StringField('Descrição do seu produto ou serviço', validators=[InputRequired()], widget=TextArea(), render_kw={'class': 'form-control', 'rows': 10})