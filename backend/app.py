from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_cors import CORS
from librouteros import connect
from librouteros.login import plain
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
import sqlite3
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

# Função para verificar e corrigir banco de dados corrompido
def check_and_fix_database(db_path):
   """Verifica se o banco de dados está corrompido e o recria se necessário"""
   try:
       # Tentar conectar e fazer uma consulta simples
       conn = sqlite3.connect(db_path)
       cursor = conn.cursor()
       cursor.execute("PRAGMA integrity_check;")
       result = cursor.fetchone()
       conn.close()
       
       if result[0] != 'ok':
           print(f"Banco de dados corrompido detectado: {result[0]}")
           raise sqlite3.DatabaseError("Database corrupted")
           
       print("Verificação do banco de dados: OK")
       return True
       
   except (sqlite3.DatabaseError, sqlite3.OperationalError) as e:
       print(f"Erro no banco de dados detectado: {e}")
       print("Removendo banco de dados corrompido e criando novo...")
       
       # Fazer backup do banco corrompido
       if os.path.exists(db_path):
           backup_path = f"{db_path}.corrupted.{int(time.time())}"
           try:
               os.rename(db_path, backup_path)
               print(f"Backup do banco corrompido salvo em: {backup_path}")
           except Exception as backup_error:
               print(f"Erro ao fazer backup: {backup_error}")
               # Se não conseguir fazer backup, remove o arquivo
               try:
                   os.remove(db_path)
                   print("Banco corrompido removido")
               except:
                   pass
       
       return False

app = Flask(__name__)

# Configuração CORS - permitir todas as origens para debug
CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

# Configurar diretório para o banco de dados
db_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'instance')
if not os.path.exists(db_dir):
   os.makedirs(db_dir)
   print(f"Diretório instance criado: {db_dir}")

db_path = os.path.join(db_dir, "mikrotik_manager.db")
print(f"Caminho do banco de dados: {db_path}")

# Verificar e corrigir banco de dados se necessário
if os.path.exists(db_path):
   if not check_and_fix_database(db_path):
       print("Banco de dados será recriado...")

app.config['SECRET_KEY'] = 'mikrotik-dashboard-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Certifique-se de que o diretório static/css existe
if not os.path.exists('static/css'):
   os.makedirs('static/css')

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
MIKROTIK_HOST = os.environ.get('MIKROTIK_HOST', '10.10.0.2')
MIKROTIK_USER = os.environ.get('MIKROTIK_USER', 'API1')
MIKROTIK_PASSWORD = os.environ.get('MIKROTIK_PASSWORD', 'Blocked@@99')

# Configurações para o controle de consumo
DAILY_LIMIT_MB = 512  # Limite diário em MB
LIMITED_PROFILE = "127k-Limitado"  # Perfil para usuários que atingiram o limite
DEFAULT_PROFILE = "500mb-dia"  # Perfil padrão para restaurar no início do dia

# Função para conectar ao MikroTik usando librouteros
def connect_to_mikrotik():
   try:
       api = connect(
           host=MIKROTIK_HOST,
           username=MIKROTIK_USER,
           password=MIKROTIK_PASSWORD,
           login_method=plain
       )
       return api
   except Exception as e:
       log_with_context('error', f"Erro ao conectar ao MikroTik: {e}", error=str(e))
       return None

# Endpoint de saúde SIMPLIFICADO - sem SQLAlchemy
@app.route('/api/health')
def health_check():
   try:
       # Testar conexão com banco de dados usando SQLite diretamente
       conn = sqlite3.connect(db_path)
       cursor = conn.cursor()
       cursor.execute("SELECT 1")
       result = cursor.fetchone()
       conn.close()
       
       db_status = "connected" if result and result[0] == 1 else "error"
       
       response_data = {
           'status': 'healthy',
           'timestamp': get_current_datetime().isoformat(),
           'version': '1.0.0',
           'database': db_status,
           'db_path': db_path,
           'message': 'Backend funcionando perfeitamente!'
       }
       
       response = jsonify(response_data)
       response.headers.add('Access-Control-Allow-Origin', '*')
       return response
       
   except Exception as e:
       error_response = {
           'status': 'unhealthy',
           'timestamp': get_current_datetime().isoformat(),
           'error': str(e),
           'db_path': db_path,
           'message': 'Erro no backend'
       }
       
       response = jsonify(error_response), 500
       if isinstance(response, tuple):
           response[0].headers.add('Access-Control-Allow-Origin', '*')
       else:
           response.headers.add('Access-Control-Allow-Origin', '*')
       return response

# Endpoint de teste simples
@app.route('/api/test')
def test_endpoint():
   response = jsonify({
       'status': 'ok',
       'message': 'Backend está funcionando perfeitamente!',
       'timestamp': get_current_datetime().isoformat(),
       'version': '1.0.0'
   })
   response.headers.add('Access-Control-Allow-Origin', '*')
   return response

# API Routes para o frontend
@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def api_login():
   # Tratar preflight OPTIONS
   if request.method == 'OPTIONS':
       response = app.make_default_options_response()
       response.headers.add('Access-Control-Allow-Methods', 'POST')
       response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
       response.headers.add('Access-Control-Allow-Origin', '*')
       return response
       
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
       
       response = jsonify({
           'success': True,
           'user': {
               'id': user.id,
               'username': user.username,
               'role': user.role
           }
       })
       response.headers.add('Access-Control-Allow-Origin', '*')
       return response
   else:
       response = jsonify({'success': False, 'message': 'Credenciais inválidas'}), 401
       if isinstance(response, tuple):
           response[0].headers.add('Access-Control-Allow-Origin', '*')
       else:
           response.headers.add('Access-Control-Allow-Origin', '*')
       return response

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
def api_logout():
   # Tratar preflight OPTIONS
   if request.method == 'OPTIONS':
       response = app.make_default_options_response()
       response.headers.add('Access-Control-Allow-Methods', 'POST')
       response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
       response.headers.add('Access-Control-Allow-Origin', '*')
       return response
       
   session.clear()
   response = jsonify({'success': True})
   response.headers.add('Access-Control-Allow-Origin', '*')
   return response

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
   # Obter usuários online
   api = connect_to_mikrotik()
   online_users = []
   total_users = 0
   
   if api:
       try:
           # Obter usuários ativos
           online_users = list(api.path('/ip/hotspot/active').select('user', 'bytes-in', 'bytes-out').call())
           
           # Obter todos os usuários
           all_users = list(api.path('/ip/hotspot/user').select('name').call())
           total_users = len(all_users)
           
           api.close()
       except Exception as e:
           log_with_context('error', f"Erro ao obter dados do MikroTik: {e}", error=str(e))
           if api:
               try:
                   api.close()
               except:
                   pass
           
           # Dados de exemplo para quando o MikroTik não está disponível
           online_users = [
               {'user': 'exemplo1', 'bytes-in': '1048576', 'bytes-out': '524288'},
               {'user': 'exemplo2', 'bytes-in': '2097152', 'bytes-out': '1048576'}
           ]
           total_users = 5
   else:
       # Dados de exemplo para quando o MikroTik não está disponível
       online_users = [
           {'user': 'exemplo1', 'bytes-in': '1048576', 'bytes-out': '524288'},
           {'user': 'exemplo2', 'bytes-in': '2097152', 'bytes-out': '1048576'}
       ]
       total_users = 5
   
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
   
   response = jsonify({
       'online_users': len(online_users),
       'total_users': total_users,
       'total_today_gb': round(total_today, 2),
       'online_users_list': online_users
   })
   response.headers.add('Access-Control-Allow-Origin', '*')
   return response

@app.route('/api/users', methods=['GET', 'POST', 'OPTIONS'])
def api_users():
   # Tratar preflight OPTIONS
   if request.method == 'OPTIONS':
       response = app.make_default_options_response()
       response.headers.add('Access-Control-Allow-Methods', 'GET, POST')
       response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
       response.headers.add('Access-Control-Allow-Origin', '*')
       return response
   
   if request.method == 'GET':
       api = connect_to_mikrotik()
       users = []
       
       if api:
           try:
               # Obter usuários
               users_data = list(api.path('/ip/hotspot/user').select('name', 'profile', 'disabled', '.id').call())
               users = []
               
               for user in users_data:
                   user_dict = {
                       'id': user.get('.id', ''),
                       'name': user.get('name', ''),
                       'profile': user.get('profile', ''),
                       'disabled': user.get('disabled', 'false'),
                       'daily_usage_mb': 0,
                       'limit_reached': False
                   }
                   users.append(user_dict)
               
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
                   
           except Exception as e:
               log_with_context('error', f"Erro ao obter usuários: {e}", error=str(e))
               if api:
                   try:
                       api.close()
                   except:
                       pass
               
               # Dados de exemplo para quando o MikroTik não está disponível
               users = [
                   {'id': '1', 'name': 'exemplo1', 'profile': '500mb-dia', 'disabled': 'false', 'daily_usage_mb': 250, 'limit_reached': False},
                   {'id': '2', 'name': 'exemplo2', 'profile': '127k-Limitado', 'disabled': 'false', 'daily_usage_mb': 512, 'limit_reached': True}
               ]
       else:
           # Dados de exemplo para quando o MikroTik não está disponível
           users = [
               {'id': '1', 'name': 'exemplo1', 'profile': '500mb-dia', 'disabled': 'false', 'daily_usage_mb': 250, 'limit_reached': False},
               {'id': '2', 'name': 'exemplo2', 'profile': '127k-Limitado', 'disabled': 'false', 'daily_usage_mb': 512, 'limit_reached': True}
           ]
       
       response = jsonify(users)
       response.headers.add('Access-Control-Allow-Origin', '*')
       return response
   
   elif request.method == 'POST':
       data = request.get_json()
       username = data.get('username')
       password = data.get('password')
       profile = data.get('profile')
       
       api = connect_to_mikrotik()
       
       if api:
           try:
               # Adicionar usuário
               api.path('/ip/hotspot/user').add(
                   name=username,
                   password=password,
                   profile=profile
               )
               
               # Registrar o perfil original do usuário
               user_profile = UserProfile(
                   username=username,
                   original_profile=profile,
                   current_profile=profile
               )
               db.session.add(user_profile)
               db.session.commit()
               
               api.close()
               response = jsonify({'success': True, 'message': f'Usuário {username} criado com sucesso'})
               response.headers.add('Access-Control-Allow-Origin', '*')
               return response
           except Exception as e:
               log_with_context('error', f"Erro ao criar usuário: {e}", error=str(e))
               if api:
                   try:
                       api.close()
                   except:
                       pass
               response = jsonify({'success': False, 'message': str(e)}), 500
               if isinstance(response, tuple):
                   response[0].headers.add('Access-Control-Allow-Origin', '*')
               else:
                   response.headers.add('Access-Control-Allow-Origin', '*')
               return response
       
       response = jsonify({'success': False, 'message': 'Não foi possível conectar ao MikroTik'}), 500
       if isinstance(response, tuple):
           response[0].headers.add('Access-Control-Allow-Origin', '*')
       else:
           response.headers.add('Access-Control-Allow-Origin', '*')
       return response

@app.route('/api/users/<username>', methods=['DELETE', 'OPTIONS'])
def api_delete_user(username):
   # Tratar preflight OPTIONS
   if request.method == 'OPTIONS':
       response = app.make_default_options_response()
       response.headers.add('Access-Control-Allow-Methods', 'DELETE')
       response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
       response.headers.add('Access-Control-Allow-Origin', '*')
       return response
       
   api = connect_to_mikrotik()
   
   if api:
       try:
           # Encontrar usuário pelo nome
           users = list(api.path('/ip/hotspot/user').select('.id', 'name').where(name=username).call())
           
           if users:
               user_id = users[0].get('.id')
               # Remover usuário
               api.path('/ip/hotspot/user').remove(id=user_id)
               
               # Remover perfil do usuário do banco de dados
               user_profile = UserProfile.query.filter_by(username=username).first()
               if user_profile:
                   db.session.delete(user_profile)
                   db.session.commit()
               
               api.close()
               response = jsonify({'success': True, 'message': f'Usuário {username} removido com sucesso'})
               response.headers.add('Access-Control-Allow-Origin', '*')
               return response
           else:
               api.close()
               response = jsonify({'success': False, 'message': 'Usuário não encontrado'}), 404
               if isinstance(response, tuple):
                   response[0].headers.add('Access-Control-Allow-Origin', '*')
               else:
                   response.headers.add('Access-Control-Allow-Origin', '*')
               return response
               
       except Exception as e:
           log_with_context('error', f"Erro ao excluir usuário: {e}", error=str(e))
           if api:
               try:
                   api.close()
               except:
                   pass
           response = jsonify({'success': False, 'message': str(e)}), 500
           if isinstance(response, tuple):
               response[0].headers.add('Access-Control-Allow-Origin', '*')
           else:
               response.headers.add('Access-Control-Allow-Origin', '*')
           return response
   
   response = jsonify({'success': False, 'message': 'Não foi possível conectar ao MikroTik'}), 500
   if isinstance(response, tuple):
       response[0].headers.add('Access-Control-Allow-Origin', '*')
   else:
       response.headers.add('Access-Control-Allow-Origin', '*')
   return response

@app.route('/api/profiles', methods=['GET', 'OPTIONS'])
def api_profiles():
   # Tratar preflight OPTIONS
   if request.method == 'OPTIONS':
       response = app.make_default_options_response()
       response.headers.add('Access-Control-Allow-Methods', 'GET')
       response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
       response.headers.add('Access-Control-Allow-Origin', '*')
       return response
       
   api = connect_to_mikrotik()
   profiles = []
   
   if api:
       try:
           # Obter perfis
           profiles_data = list(api.path('/ip/hotspot/user/profile').select('name').call())
           profiles = [profile.get('name') for profile in profiles_data]
           api.close()
       except Exception as e:
           log_with_context('error', f"Erro ao obter perfis: {e}", error=str(e))
           if api:
               try:
                   api.close()
               except:
                   pass
           
           # Perfis de exemplo para quando o MikroTik não está disponível
           profiles = ['500mb-dia', '127k-Limitado', '1GB-dia', '2GB-dia']
   else:
       # Perfis de exemplo para quando o MikroTik não está disponível
       profiles = ['500mb-dia', '127k-Limitado', '1GB-dia', '2GB-dia']
   
   response = jsonify(profiles)
   response.headers.add('Access-Control-Allow-Origin', '*')
   return response

# Função para coletar dados de uso
def collect_usage_data():
   log_with_context('info', "Iniciando coleta de dados de uso atual", task="collect_data")
   api = connect_to_mikrotik()
   if not api:
       log_with_context('error', "Não foi possível conectar ao MikroTik para coletar dados de uso", task="collect_data")
       return False
   
   try:
       # Obter usuários ativos
       active_users = list(api.path('/ip/hotspot/active').select('user', 'bytes-in', 'bytes-out').call())
       
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
           try:
               api.close()
           except:
               pass
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
       
       # Obter usuários
       hotspot_users = list(api.path('/ip/hotspot/user').select('name', 'profile', '.id').call())
       
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
               
               # Alterar perfil do usuário
               api.path('/ip/hotspot/user').update(
                   id=user.get('.id'),
                   profile=LIMITED_PROFILE
               )
       
       api.close()
   except Exception as e:
       log_with_context('error', f"Erro ao verificar limites: {str(e)}", task="check_limits", error=str(e))
       if api:
           try:
               api.close()
           except:
               pass

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
                   # Encontrar usuário pelo nome
                   users = list(api.path('/ip/hotspot/user').select('.id', 'name').where(name=profile.username).call())
                   
                   if users:
                       # Alterar perfil do usuário
                       api.path('/ip/hotspot/user').update(
                           id=users[0].get('.id'),
                           profile=DEFAULT_PROFILE
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
           try:
               api.close()
           except:
               pass

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

def initialize_database():
   """Inicializa o banco de dados com tratamento de erros"""
   try:
       print(f"Inicializando banco de dados em: {db_path}")
       db.create_all()
       
       # Criar usuário admin padrão
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
       
       print("Banco de dados inicializado com sucesso!")
       return True
       
   except Exception as e:
       print(f"Erro ao inicializar banco de dados: {e}")
       return False

if __name__ == '__main__':
   print("Iniciando aplicação...")
   print(f"Diretório de trabalho: {os.getcwd()}")
   
   with app.app_context():
       if not initialize_database():
           print("Erro ao inicializar banco de dados")
           sys.exit(1)
   
   start_scheduler()
   print("Aplicação iniciada com sucesso!")
   app.run(debug=False, host='0.0.0.0', port=5000)
