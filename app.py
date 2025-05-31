from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_cors import CORS
import librouteros
from librouteros import connect
import matplotlib
matplotlib.use('Agg')  # Use o backend não-interativo
import matplotlib.pyplot as plt
import io
import base64
from datetime import datetime, timedelta, timezone
import pandas as pd
import numpy as np
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo
import os
import sys
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json
import uuid
import email_validator
import threading
import time
import schedule
from logger import logger, log_with_context

# Configuração de timezone
SYSTEM_TIMEZONE = datetime.now().astimezone().tzinfo

def get_current_datetime():
    """Retorna o datetime atual no timezone do sistema"""
    return datetime.now().astimezone(SYSTEM_TIMEZONE)

def convert_to_system_timezone(dt):
    """Converte um datetime para o timezone do sistema"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(SYSTEM_TIMEZONE)

app = Flask(__name__)
CORS(app)  # Habilitar CORS para comunicação com frontend

app.config['SECRET_KEY'] = 'mikrotik-dashboard-secret-key'

# Configurar banco de dados com caminho absoluto
db_path = os.path.abspath('instance/mikrotik_manager.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Certifique-se de que os diretórios necessários existem
for directory in ['static/css', 'logs', 'instance']:
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        print(f"Diretório criado: {directory}")

# Verificar permissões do diretório instance
instance_dir = 'instance'
if os.path.exists(instance_dir):
    print(f"Diretório instance existe: {os.path.abspath(instance_dir)}")
    print(f"Permissões do diretório instance: {oct(os.stat(instance_dir).st_mode)[-3:]}")
else:
    print(f"Criando diretório instance: {os.path.abspath(instance_dir)}")
    os.makedirs(instance_dir, exist_ok=True)

db = SQLAlchemy(app)

# Modelo para armazenar dados de uso
class UsageData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    bytes_in = db.Column(db.BigInteger, default=0)
    bytes_out = db.Column(db.BigInteger, default=0)
    timestamp = db.Column(db.DateTime, default=lambda: get_current_datetime())

    def __repr__(self):
        return f'<UsageData {self.username}>'

# Modelo para administradores do sistema
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user
    created_at = db.Column(db.DateTime, default=lambda: get_current_datetime())
    last_login = db.Column(db.DateTime)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Modelo para rastrear perfis originais dos usuários
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    original_profile = db.Column(db.String(100), nullable=False)
    current_profile = db.Column(db.String(100), nullable=False)
    last_reset = db.Column(db.DateTime, default=get_current_datetime)
    
    def __repr__(self):
        return f'<UserProfile {self.username}>'

# Configurações do MikroTik
MIKROTIK_HOST = os.environ.get('MIKROTIK_HOST', '192.168.1.1')
MIKROTIK_USER = os.environ.get('MIKROTIK_USER', 'admin')
MIKROTIK_PASSWORD = os.environ.get('MIKROTIK_PASSWORD', 'admin')

# Configurações para o controle de consumo
DAILY_LIMIT_MB = 512  # Limite diário em MB
LIMITED_PROFILE = "127k-Limitado"  # Perfil para usuários que atingiram o limite
DEFAULT_PROFILE = "500mb-dia"  # Perfil padrão para restaurar no início do dia

# Formulário para adicionar usuário hotspot
class HotspotUserForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    profile = StringField('Perfil', validators=[DataRequired()])
    submit = SubmitField('Cadastrar')

# Formulário para login
class LoginForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

# Formulário para registro de novo admin
class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar')

# Decorator para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Função para conectar ao MikroTik
def connect_to_mikrotik():
    try:
        api = connect(
            username=MIKROTIK_USER,
            password=MIKROTIK_PASSWORD,
            host=MIKROTIK_HOST,
            port=8728
        )
        return api
    except Exception as e:
        print(f"Erro ao conectar ao MikroTik: {e}")
        return None

# Health check endpoint
@app.route('/api/health')
def health_check():
    try:
        # Verificar conexão com banco de dados
        db.session.execute('SELECT 1')
        
        # Verificar conexão com MikroTik (opcional)
        mikrotik_status = "disconnected"
        try:
            api = connect_to_mikrotik()
            if api:
                api.close()
                mikrotik_status = "connected"
        except:
            pass
        
        return jsonify({
            'status': 'healthy',
            'timestamp': get_current_datetime().isoformat(),
            'database': 'connected',
            'mikrotik': mikrotik_status,
            'db_path': db_path
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': get_current_datetime().isoformat(),
            'db_path': db_path
        }), 500

# API Routes para o frontend
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and user.check_password(password):
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        
        user.last_login = get_current_datetime()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role
            }
        })
    else:
        return jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    # Dados de exemplo se não conseguir conectar ao MikroTik
    default_stats = {
        'online_users': 5,
        'total_users': 25,
        'total_today_gb': 2.5,
        'online_users_list': [
            {'user': 'user1', 'address': '192.168.1.100', 'uptime': '2h 30m'},
            {'user': 'user2', 'address': '192.168.1.101', 'uptime': '1h 15m'},
            {'user': 'user3', 'address': '192.168.1.102', 'uptime': '45m'},
        ]
    }
    
    # Tentar obter dados reais do MikroTik
    api = connect_to_mikrotik()
    if api:
        try:
            # Obter usuários ativos
            active_users = list(api.path('ip', 'hotspot', 'active'))
            
            # Obter todos os usuários
            all_users = list(api.path('ip', 'hotspot', 'user'))
            
            api.close()
            
            # Calcular consumo total hoje
            today = get_current_datetime().date()
            today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
            
            today_usage = UsageData.query.filter(UsageData.timestamp >= today_start).all()
            
            user_today_data = {}
            for usage in today_usage:
                if usage.username in user_today_data:
                    user_today_data[usage.username]['bytes_in'] += usage.bytes_in
                    user_today_data[usage.username]['bytes_out'] += usage.bytes_out
                else:
                    user_today_data[usage.username] = {
                        'bytes_in': usage.bytes_in,
                        'bytes_out': usage.bytes_out
                    }
            
            total_today = sum([(data['bytes_in'] + data['bytes_out']) for data in user_today_data.values()]) / (1024 * 1024 * 1024)  # GB
            
            return jsonify({
                'online_users': len(active_users),
                'total_users': len(all_users),
                'total_today_gb': round(total_today, 2),
                'online_users_list': active_users[:10]  # Limitar a 10 usuários
            })
            
        except Exception as e:
            print(f"Erro ao obter dados do MikroTik: {e}")
    
    # Retornar dados de exemplo se não conseguir conectar
    return jsonify(default_stats)

@app.route('/api/users')
def api_users():
    # Dados de exemplo se não conseguir conectar ao MikroTik
    default_users = [
        {
            'id': '1',
            'name': 'user1',
            'profile': 'default',
            'disabled': 'false',
            'daily_usage_mb': 150.5,
            'limit_reached': False
        },
        {
            'id': '2',
            'name': 'user2',
            'profile': 'premium',
            'disabled': 'false',
            'daily_usage_mb': 89.2,
            'limit_reached': False
        }
    ]
    
    api = connect_to_mikrotik()
    if api:
        try:
            users = list(api.path('ip', 'hotspot', 'user'))
            api.close()
            
            # Adicionar dados de consumo
            today = get_current_datetime().date()
            today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
            
            for user in users:
                username = user.get('name', '')
                
                today_usage = UsageData.query.filter(
                    UsageData.username == username,
                    UsageData.timestamp >= today_start
                ).all()
                
                total_bytes = sum(usage.bytes_in + usage.bytes_out for usage in today_usage)
                total_mb = total_bytes / (1024 * 1024)
                user['daily_usage_mb'] = round(total_mb, 2)
                user['limit_reached'] = total_mb >= DAILY_LIMIT_MB
            
            return jsonify(users)
            
        except Exception as e:
            print(f"Erro ao obter usuários: {e}")
    
    # Retornar dados de exemplo se não conseguir conectar
    return jsonify(default_users)

@app.route('/api/users', methods=['POST'])
def api_create_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    profile = data.get('profile', 'default')
    
    api = connect_to_mikrotik()
    if api:
        try:
            # Adicionar usuário
            api.path('ip', 'hotspot', 'user').add(
                name=username,
                password=password,
                profile=profile
            )
            
            api.close()
            
            # Registrar o perfil original do usuário
            user_profile = UserProfile(
                username=username,
                original_profile=profile,
                current_profile=profile
            )
            db.session.add(user_profile)
            db.session.commit()
            
            return jsonify({'success': True, 'message': f'Usuário {username} criado com sucesso'})
            
        except Exception as e:
            if api:
                api.close()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Não foi possível conectar ao MikroTik'}), 500

@app.route('/api/users/<username>', methods=['DELETE'])
def api_delete_user(username):
    api = connect_to_mikrotik()
    if api:
        try:
            # Encontrar e remover usuário
            users = list(api.path('ip', 'hotspot', 'user').select('name', username))
            
            if users:
                user_id = users[0]['id']
                api.path('ip', 'hotspot', 'user').remove(user_id)
                
                # Remover perfil do usuário do banco de dados
                user_profile = UserProfile.query.filter_by(username=username).first()
                if user_profile:
                    db.session.delete(user_profile)
                    db.session.commit()
                
                api.close()
                return jsonify({'success': True, 'message': f'Usuário {username} removido com sucesso'})
            else:
                api.close()
                return jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
                
        except Exception as e:
            if api:
                api.close()
            return jsonify({'success': False, 'message': str(e)}), 500
    
    return jsonify({'success': False, 'message': 'Não foi possível conectar ao MikroTik'}), 500

@app.route('/api/profiles')
def api_profiles():
    # Perfis padrão se não conseguir conectar ao MikroTik
    default_profiles = ['default', 'premium', '500mb-dia', '127k-Limitado']
    
    api = connect_to_mikrotik()
    if api:
        try:
            profiles_data = list(api.path('ip', 'hotspot', 'user', 'profile'))
            profiles = [profile.get('name') for profile in profiles_data if profile.get('name')]
            api.close()
            return jsonify(profiles)
        except Exception as e:
            print(f"Erro ao obter perfis: {e}")
            if api:
                api.close()
    
    return jsonify(default_profiles)

# Função para coletar dados de uso e armazenar no banco de dados
def collect_usage_data():
    log_with_context('info', "Iniciando coleta de dados de uso atual", task="collect_data")
    api = connect_to_mikrotik()
    if not api:
        log_with_context('error', "Não foi possível conectar ao MikroTik para coletar dados de uso", task="collect_data")
        return False
    
    try:
        active_users = list(api.path('ip', 'hotspot', 'active'))
        
        today = get_current_datetime().date()
        today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=SYSTEM_TIMEZONE)
        
        for user in active_users:
            try:
                username = user.get('user', 'unknown')
                bytes_in = int(user.get('bytes-in', 0))
                bytes_out = int(user.get('bytes-out', 0))
                
                usage = UsageData(
                    username=username,
                    bytes_in=bytes_in,
                    bytes_out=bytes_out
                )
                db.session.add(usage)
            except Exception as user_error:
                log_with_context('warning', f"Erro ao processar dados para usuário ativo {user.get('user', 'unknown')}: {str(user_error)}", 
                                task="collect_data", error=str(user_error))
        
        db.session.commit()
        api.close()
        return True
    except Exception as e:
        log_with_context('error', f"Erro ao coletar dados de uso: {str(e)}", task="collect_data", error=str(e))
        if api:
            api.close()
        return False

# Função para verificar limites
def check_daily_usage_limits():
    log_with_context('info', "Verificando limites de consumo diário", task="check_limits")
    today = get_current_datetime().date()
    today_start = datetime.combine(today, datetime.min.time()).replace(tzinfo=timezone.utc)
    
    api = connect_to_mikrotik()
    if not api:
        log_with_context('error', "Não foi possível conectar ao MikroTik para verificar limites", task="check_limits")
        return
    
    try:
        collect_usage_data()
        
        hotspot_users = list(api.path('ip', 'hotspot', 'user'))
        
        for user in hotspot_users:
            username = user.get('name')
            current_profile = user.get('profile')
            
            if current_profile == LIMITED_PROFILE:
                continue
            
            today_usage = UsageData.query.filter(
                UsageData.username == username,
                UsageData.timestamp >= today_start
            ).all()
            
            total_bytes = sum(usage.bytes_in + usage.bytes_out for usage in today_usage)
            total_mb = total_bytes / (1024 * 1024)
            
            if total_mb >= DAILY_LIMIT_MB and current_profile != LIMITED_PROFILE:
                log_with_context('warning', f"Usuário {username} atingiu o limite diário ({total_mb:.2f} MB)", 
                                task="check_limits", username=username, usage_mb=total_mb)
                
                # Atualizar perfil do usuário
                api.path('ip', 'hotspot', 'user').update(
                    **{'.id': user.get('.id'), 'profile': LIMITED_PROFILE}
                )
        
        api.close()
    except Exception as e:
        log_with_context('error', f"Erro ao verificar limites: {str(e)}", task="check_limits", error=str(e))
        if api:
            api.close()

# Função para resetar perfis
def reset_user_profiles():
    log_with_context('info', "Resetando perfis de usuários", task="reset_profiles")
    api = connect_to_mikrotik()
    if not api:
        return
    
    try:
        user_profiles = UserProfile.query.all()
        
        for profile in user_profiles:
            if profile.current_profile == LIMITED_PROFILE:
                try:
                    users = list(api.path('ip', 'hotspot', 'user').select('name', profile.username))
                    if users:
                        api.path('ip', 'hotspot', 'user').update(
                            **{'.id': users[0].get('.id'), 'profile': DEFAULT_PROFILE}
                        )
                        
                        profile.current_profile = DEFAULT_PROFILE
                        profile.last_reset = get_current_datetime()
                except Exception as e:
                    log_with_context('error', f"Erro ao restaurar perfil do usuário {profile.username}: {str(e)}", 
                                    task="reset_profiles", username=profile.username, error=str(e))
        
        db.session.commit()
        api.close()
    except Exception as e:
        log_with_context('error', f"Erro ao resetar perfis: {str(e)}", task="reset_profiles", error=str(e))
        if api:
            api.close()

# Agendador
def start_scheduler():
    def run_scheduler():
        schedule.every(5).minutes.do(lambda: app.app_context() and check_daily_usage_limits())
        schedule.every().day.at("00:00").do(lambda: app.app_context() and reset_user_profiles())
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except Exception as e:
                print(f"Erro no agendador: {e}")
                time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.daemon = True
    scheduler_thread.start()

# Função para inicializar o banco de dados
def init_database():
    try:
        print(f"Inicializando banco de dados em: {db_path}")
        
        # Verificar se o diretório pai existe
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            print(f"Diretório criado: {db_dir}")
        
        # Criar todas as tabelas
        db.create_all()
        print("Tabelas do banco de dados criadas com sucesso")
        
        # Criar usuário admin padrão se não existir
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@example.com',
                role='admin'
            )
            admin.set_password('admin')
            db.session.add(admin)
            db.session.commit()
            print("Usuário admin criado. Username: admin, Senha: admin")
        else:
            print("Usuário admin já existe")
            
        return True
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        return False

# Modificar a parte principal do script
if __name__ == '__main__':
    print("Iniciando aplicação...")
    print(f"Diretório de trabalho: {os.getcwd()}")
    print(f"Caminho do banco de dados: {db_path}")
    
    with app.app_context():
        if init_database():
            print("Banco de dados inicializado com sucesso")
        else:
            print("Erro ao inicializar banco de dados")
            sys.exit(1)
    
    print("Iniciando agendador...")
    start_scheduler()
    
    print("Iniciando servidor Flask...")
    app.run(debug=False, host='0.0.0.0', port=5000)
