# Importando os módulos necessários do Flask e outras dependências
from flask import render_template, url_for, redirect, flash
from fakepinterest import app, database, bcrypt
from fakepinterest.models import Usuario, Foto
from flask_login import login_required, login_user, logout_user, current_user
from fakepinterest.forms import FormLogin, FormCriarConta, FormFoto
from werkzeug.utils import secure_filename
import os

# Rota para a página inicial ("homepage")
@app.route("/", methods=["GET", "POST"])
def homepage():
    # Instanciando o formulário de login
    form_login = FormLogin()
    # Verificando se o formulário foi submetido
    if form_login.validate_on_submit():
        # Verificando se o usuário existe no banco de dados e se a senha está correta
        usuario = Usuario.query.filter_by(email=form_login.email.data).first()
        if usuario and bcrypt.check_password_hash(usuario.senha, form_login.senha.data):
            # Realizando o login do usuário
            login_user(usuario)
            # Redirecionando para o perfil do usuário logado
            return redirect(url_for("perfil", id_usuario=usuario.id))
    # Renderizando o template da página inicial, passando o formulário como contexto
    return render_template("homepage.html", form=form_login)


# Rota para criar uma nova conta de usuário
@app.route("/criarconta", methods=["GET", "POST"])
def criar_conta():
    # Instanciando o formulário de criação de conta
    form_criarconta = FormCriarConta()
    
    # Verifica se o formulário de criação de conta foi submetido
    if form_criarconta.validate_on_submit():
        # Verifica se o email fornecido já existe no banco de dados
        if Usuario.query.filter_by(email=form_criarconta.email.data).first():
            # Se o email já existe, exibe uma mensagem de erro e redireciona para a página de criação de conta
            flash('Este email já existe. Por favor, faça o login.', 'error')
            return render_template("criarconta.html", form=form_criarconta)

    
    
    # Verificando se o formulário foi submetido
    if form_criarconta.validate_on_submit():
        # Gerando o hash da senha do usuário
        senha = bcrypt.generate_password_hash(form_criarconta.senha.data)
        # Criando um novo usuário com os dados fornecidos no formulário
        usuario = Usuario(username=form_criarconta.username.data,
                          senha=senha, email=form_criarconta.email.data)
        # Adicionando o usuário ao banco de dados
        database.session.add(usuario)
        # Commit das alterações no banco de dados
        database.session.commit()
        # Realizando o login do novo usuário
        login_user(usuario, remember=True)
        # Redirecionando para o perfil do novo usuário
        return redirect(url_for("perfil", id_usuario=usuario.id))
    
    # Renderizando o template de criação de conta, passando o formulário como contexto
    return render_template("criarconta.html", form=form_criarconta)


# Rota para o perfil do usuário
@app.route("/perfil/<id_usuario>", methods=["GET", "POST"])
@login_required
def perfil(id_usuario):
    # Verificando se o usuário está visualizando seu próprio perfil
    if int(id_usuario) == int(current_user.id):
        # Instanciando o formulário de upload de foto
        form_foto = FormFoto()
        # Verificando se o formulário foi submetido
        if form_foto.validate_on_submit():
            # Salvando o arquivo de imagem enviado pelo formulário
            arquivo = form_foto.foto.data
            nome_seguro = secure_filename(arquivo.filename)
            caminho = os.path.join(os.path.abspath(os.path.dirname(__file__)),
                                   app.config["UPLOAD_FOLDER"],
                                   nome_seguro)
            arquivo.save(caminho)
            # Criando uma nova foto no banco de dados associada ao usuário atual
            foto = Foto(imagem=nome_seguro, id_usuario=current_user.id)
            database.session.add(foto)
            database.session.commit()
        # Renderizando o template do perfil, passando o usuário atual e o formulário de upload como contexto
        return render_template("perfil.html", usuario=current_user, form=form_foto)
    else:
        # Obtendo o usuário correspondente ao ID fornecido na URL
        usuario = Usuario.query.get(int(id_usuario))
        # Renderizando o template do perfil do usuário correspondente
        return render_template("perfil.html", usuario=usuario, form=None)


# Rota para realizar o logout do usuário
@app.route("/logout")
@login_required
def logout():
    # Realizando o logout do usuário atual
    logout_user()
    # Redirecionando para a página inicial
    return redirect(url_for("homepage"))


# Rota para o feed de fotos
@app.route("/feed")
@login_required
def feed():
    # Obtendo todas as fotos ordenadas pela data de criação (da mais recente para a mais antiga)
    fotos = Foto.query.order_by(Foto.data_criacao.desc()).all()
    # Renderizando o template do feed de fotos, passando as fotos como contexto
    return render_template("feed.html", fotos=fotos)
