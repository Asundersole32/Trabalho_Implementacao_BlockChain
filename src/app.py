import json
import os
import time
from web3 import Web3
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template_string, session

load_dotenv()

app = Flask(__name__)
app.secret_key = 'blockchain_demo_secret_key_2024'

class BlockchainApp:
    def __init__(self):
        self.connect_to_blockchain()
    
    def connect_to_blockchain(self):
        """Conecta à rede blockchain com retry automático"""
        ganache_url = os.getenv('GANACHE_URL', 'http://ganache:8545')
        max_retries = 10
        retry_delay = 3
        
        for i in range(max_retries):
            try:
                print(f"Tentativa {i+1} de conexão com {ganache_url}")
                self.w3 = Web3(Web3.HTTPProvider(ganache_url))
                
                if self.w3.is_connected():
                    print("✅ Conectado à blockchain Ethereum local")
                    print(f"📊 Saldo total da rede: {self.w3.eth.get_balance(self.w3.eth.accounts[0]) / 10**18} ETH")
                    print(f"🔗 Chain ID: {self.w3.eth.chain_id}")
                    print(f"⛽ Gas Price: {self.w3.eth.gas_price / 10**9} Gwei")
                    return
                else:
                    print("❌ Conexão falhou")
            
            except Exception as e:
                print(f"⚠️ Erro na conexão: {str(e)}")
            
            if i < max_retries - 1:
                print(f"🕒 Aguardando {retry_delay} segundos antes da próxima tentativa...")
                time.sleep(retry_delay)
        
        raise Exception("❌ Não foi possível conectar à blockchain após várias tentativas")

    def criar_nova_conta(self, saldo_inicial=10):
        """Cria uma nova conta Ethereum com saldo inicial"""
        try:
            # Gerar nova conta
            nova_conta = self.w3.eth.account.create()
            endereco = nova_conta.address
            chave_privada = nova_conta.key.hex()
            
            # Creditar saldo inicial da conta principal
            conta_principal = self.w3.eth.accounts[0]
            saldo_wei = self.w3.to_wei(saldo_inicial, 'ether')
            
            # Verificar saldo da conta principal
            saldo_principal = self.w3.eth.get_balance(conta_principal)
            if saldo_principal < saldo_wei:
                return False, "Saldo insuficiente na conta principal para criar nova conta"
            
            # Obter nonce da conta principal
            nonce = self.w3.eth.get_transaction_count(conta_principal)
            
            transacao = {
                'nonce': nonce,
                'from': conta_principal,
                'to': endereco,
                'value': saldo_wei,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            }
            
            # Usar a chave privada do Ganache (determinística)
            private_key = os.getenv('PRIVATE_KEY', '0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d')
            
            transacao_assinada = self.w3.eth.account.sign_transaction(transacao, private_key)
            
            # CORREÇÃO: Usar raw_transaction em vez de rawTransaction
            tx_hash = self.w3.eth.send_raw_transaction(transacao_assinada.raw_transaction)
            recibo = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return True, {
                'endereco': endereco,
                'chave_privada': chave_privada,
                'saldo_inicial': saldo_inicial,
                'transaction_hash': tx_hash.hex(),
                'block_number': recibo.blockNumber
            }
            
        except Exception as e:
            return False, f"Erro ao criar nova conta: {str(e)}"

    def get_accounts(self):
        """Retorna todas as contas disponíveis"""
        try:
            return self.w3.eth.accounts
        except Exception as e:
            print(f"Erro ao obter contas: {e}")
            return []

    def get_accounts_with_balances(self):
        """Retorna contas com seus saldos"""
        accounts = self.get_accounts()
        accounts_info = []
        for account in accounts:
            try:
                balance = self.w3.eth.get_balance(account)
                accounts_info.append({
                    'address': account,
                    'balance_ether': balance / 10**18,
                    'balance_wei': balance
                })
            except Exception as e:
                print(f"Erro ao obter saldo para {account}: {e}")
                accounts_info.append({
                    'address': account,
                    'balance_ether': 0,
                    'balance_wei': 0
                })
        return accounts_info

    def cadastrar_usuario(self, endereco, saldo_inicial=10):
        """Cadastra um novo usuário com saldo inicial"""
        try:
            if not self.w3.is_address(endereco):
                return False, "Endereço inválido"
            
            # Verificar se já tem saldo
            saldo_atual = self.w3.eth.get_balance(endereco)
            if saldo_atual > 0:
                return False, "Usuário já possui saldo"
            
            saldo_wei = self.w3.to_wei(saldo_inicial, 'ether')
            conta_principal = self.w3.eth.accounts[0]
            
            # Verificar saldo da conta principal
            saldo_principal = self.w3.eth.get_balance(conta_principal)
            if saldo_principal < saldo_wei:
                return False, "Saldo insuficiente na conta principal"
            
            # Obter nonce da conta principal
            nonce = self.w3.eth.get_transaction_count(conta_principal)
            
            transacao = {
                'nonce': nonce,
                'from': conta_principal,
                'to': endereco,
                'value': saldo_wei,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            }
            
            # Usar a chave privada do Ganache (determinística)
            private_key = os.getenv('PRIVATE_KEY', '0x4f3edf983ac636a65a842ce7c78d9aa706d3b113bce9c46f30d7d21715b23b1d')
            
            transacao_assinada = self.w3.eth.account.sign_transaction(transacao, private_key)
            
            # CORREÇÃO: Usar raw_transaction em vez de rawTransaction
            tx_hash = self.w3.eth.send_raw_transaction(transacao_assinada.raw_transaction)
            recibo = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return True, {
                'message': 'Usuário cadastrado com sucesso!',
                'transaction_hash': tx_hash.hex(),
                'block_number': recibo.blockNumber,
                'balance_ether': saldo_inicial
            }
            
        except Exception as e:
            return False, f"Erro no cadastro: {str(e)}"

    
    def login(self, endereco):
        """Verifica se o endereço existe e retorna informações"""
        if not self.w3.is_address(endereco):
            return False, "Endereço inválido"
        
        try:
            saldo = self.w3.eth.get_balance(endereco)
            transacao_count = self.w3.eth.get_transaction_count(endereco)
            
            return True, {
                'endereco': endereco,
                'saldo_ether': saldo / 10**18,
                'saldo_wei': saldo,
                'nonce': transacao_count,
                'is_contract': len(self.w3.eth.get_code(endereco)) > 2  # '0x' + bytes
            }
        except Exception as e:
            return False, f"Erro no login: {str(e)}"
    
    def transferir(self, remetente_privada, destinatario, valor_ether):
        """Realiza transferência entre contas"""
        try:
            if not self.w3.is_address(destinatario):
                return False, "Endereço do destinatário inválido"
            
            conta_remetente = self.w3.eth.account.from_key(remetente_privada).address
            valor_wei = self.w3.to_wei(valor_ether, 'ether')
            
            # Verificar saldo do remetente
            saldo_remetente = self.w3.eth.get_balance(conta_remetente)
            custo_gas = 21000 * self.w3.eth.gas_price
            
            if saldo_remetente < (valor_wei + custo_gas):
                return False, "Saldo insuficiente para transferência + gas"
            
            nonce = self.w3.eth.get_transaction_count(conta_remetente)
            
            transacao = {
                'nonce': nonce,
                'to': destinatario,
                'value': valor_wei,
                'gas': 21000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            }
            
            transacao_assinada = self.w3.eth.account.sign_transaction(transacao, remetente_privada)
            
            # CORREÇÃO: Usar raw_transaction em vez de rawTransaction
            tx_hash = self.w3.eth.send_raw_transaction(transacao_assinada.raw_transaction)
            recibo = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return True, {
                'hash_transacao': tx_hash.hex(),
                'bloco': recibo.blockNumber,
                'status': 'sucesso',
                'from': conta_remetente,
                'to': destinatario,
                'value_ether': valor_ether,
                'gas_used': recibo.gasUsed,
                'transaction_index': recibo.transactionIndex
            }
            
        except Exception as e:
            return False, f"Erro na transferência: {str(e)}"
    
    def obter_info_bloco(self, numero_bloco='latest'):
        """Obtém informações sobre um bloco"""
        try:
            bloco = self.w3.eth.get_block(numero_bloco)
            return {
                'numero': bloco.number,
                'hash': bloco.hash.hex() if bloco.hash else None,
                'hash_anterior': bloco.parentHash.hex() if bloco.parentHash else None,
                'transacoes': len(bloco.transactions),
                'timestamp': bloco.timestamp,
                'dificuldade': bloco.difficulty,
                'gas_used': bloco.gasUsed,
                'gas_limit': bloco.gasLimit,
                'miner': bloco.miner,
                'size': bloco.size
            }
        except Exception as e:
            return {'error': f"Erro ao obter bloco: {str(e)}"}
    
    def obter_transacao(self, hash_transacao):
        """Obtém detalhes de uma transação"""
        try:
            transacao = self.w3.eth.get_transaction(hash_transacao)
            recibo = self.w3.eth.get_transaction_receipt(hash_transacao)
            
            return {
                'hash': transacao.hash.hex(),
                'bloco': transacao.blockNumber,
                'de': transacao['from'],
                'para': transacao.to,
                'valor_ether': transacao.value / 10**18,
                'valor_wei': transacao.value,
                'gas': transacao.gas,
                'gas_price': transacao.gasPrice,
                'nonce': transacao.nonce,
                'status': 'sucesso' if recibo and recibo.status == 1 else 'falha',
                'gas_used': recibo.gasUsed if recibo else 0
            }
        except Exception as e:
            return {'error': f"Erro ao obter transação: {str(e)}"}
    
    def obter_estatisticas(self):
        """Retorna estatísticas da rede"""
        try:
            ultimo_bloco = self.w3.eth.get_block('latest')
            return {
                'block_number': ultimo_bloco.number,
                'total_accounts': len(self.w3.eth.accounts),
                'gas_price': self.w3.eth.gas_price,
                'chain_id': self.w3.eth.chain_id,
                'is_mining': True,  # Ganache sempre está minerando
                'latest_block_timestamp': ultimo_bloco.timestamp,
                'gas_limit': ultimo_bloco.gasLimit
            }
        except Exception as e:
            return {'error': f"Erro ao obter estatísticas: {str(e)}"}

# Inicializar a aplicação blockchain
try:
    blockchain = BlockchainApp()
    print("✅ BlockchainApp inicializado com sucesso!")
except Exception as e:
    print(f"❌ Erro ao inicializar BlockchainApp: {e}")
    blockchain = None

# Template HTML atualizado com criação de conta e indicador de usuário
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Mini Blockchain App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f0f2f5; }
        .container { max-width: 1000px; margin: 0 auto; }
        .card { background: white; padding: 20px; margin: 15px 0; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #2c3e50; text-align: center; }
        h2 { color: #3498db; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
        button { background: #3498db; color: white; padding: 12px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; margin: 5px; }
        button:hover { background: #2980b9; }
        button.secondary { background: #95a5a6; }
        button.secondary:hover { background: #7f8c8d; }
        button.success { background: #27ae60; }
        button.success:hover { background: #219653; }
        input, textarea { width: 100%; padding: 10px; margin: 8px 0; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; }
        .success { color: #27ae60; background: #d5f4e6; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .error { color: #e74c3c; background: #fadbd8; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .warning { color: #f39c12; background: #fef5e7; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .info { color: #3498db; background: #d6eaf8; padding: 10px; border-radius: 5px; margin: 10px 0; }
        .account-list { max-height: 200px; overflow-y: auto; }
        .account-item { padding: 8px; border-bottom: 1px solid #eee; }
        .user-info { background: #2c3e50; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
        .private-key-warning { background: #fff3cd; border: 1px solid #ffeaa7; color: #856404; padding: 15px; border-radius: 5px; margin: 10px 0; }
        .hidden { display: none; }
        .flex { display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
    <div class="container">
        <div class="flex">
            <h1>🔗 Mini Blockchain App</h1>
            {% if session.get('usuario_logado') %}
            <div>
                <button onclick="logout()" class="secondary">🚪 Sair</button>
            </div>
            {% endif %}
        </div>
        
        <!-- Indicador de Usuário Logado -->
        {% if session.get('usuario_logado') %}
        <div class="user-info">
            <h2>👤 Usuário Logado</h2>
            <p><strong>Endereço:</strong> {{ session.get('usuario_endereco') }}</p>
            <p><strong>Saldo:</strong> {{ "%.6f"|format(session.get('usuario_saldo', 0)) }} ETH</p>
            <p><strong>Nonce:</strong> {{ session.get('usuario_nonce', 0) }}</p>
        </div>
        {% else %}
        <div class="warning">
            <p>⚠️ Nenhum usuário logado. Faça login ou crie uma nova conta para começar.</p>
        </div>
        {% endif %}
        
        {% if blockchain %}
        <div class="card">
            <h2>📊 Estatísticas da Rede</h2>
            <pre>{{ estatisticas | tojson(indent=2) }}</pre>
        </div>

        <div class="card">
            <h2>👥 Contas do Sistema</h2>
            <div class="account-list">
                {% for account in accounts %}
                <div class="account-item">
                    <strong>{{ account.address }}</strong><br>
                    Saldo: {{ "%.6f"|format(account.balance_ether) }} ETH
                    {% if session.get('usuario_endereco') == account.address %}
                    <span style="color: #27ae60;"> ← VOCÊ ESTÁ AQUI</span>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>

        <!-- Seção de Criação de Nova Conta -->
        <div class="card">
            <h2>🆕 Criar Nova Conta</h2>
            <p>Crie uma nova conta Ethereum com saldo inicial de 10 ETH:</p>
            <button onclick="criarNovaConta()" class="success">🎯 Criar Nova Conta</button>
            <div id="nova-conta-resultado"></div>
        </div>

        <div class="card">
            <h2>🔐 Login</h2>
            <form onsubmit="fazerLogin(event)">
                <input type="text" id="login-endereco" placeholder="0x..." required>
                <button type="submit">🔑 Fazer Login</button>
            </form>
            <div id="login-resultado"></div>
        </div>

        {% if session.get('usuario_logado') %}
        <div class="card">
            <h2>💸 Transferir ETH</h2>
            <form onsubmit="fazerTransferencia(event)">
                <textarea name="remetente_privada" placeholder="Chave privada do remetente (0x...)" required rows="3"></textarea>
                <input type="text" name="destinatario" placeholder="Endereço do destinatário (0x...)" required>
                <input type="number" name="valor" placeholder="Valor em ETH" step="0.001" min="0.001" required>
                <button type="submit" class="success">🚀 Realizar Transferência</button>
            </form>
            <div id="transferencia-resultado"></div>
        </div>
        {% endif %}

        <div class="card">
            <h2>📦 Informações do Bloco</h2>
            <form onsubmit="consultarBloco(event)">
                <input type="text" name="numero_bloco" placeholder="Número do bloco ou 'latest'" value="latest">
                <button type="submit">🔍 Consultar Bloco</button>
            </form>
            <div id="bloco-resultado"></div>
        </div>

        {% else %}
        <div class="card error">
            <h2>❌ Erro de Conexão</h2>
            <p>Não foi possível conectar à blockchain. Verifique se o Ganache está rodando.</p>
        </div>
        {% endif %}
    </div>

    <script>
        // Função para criar nova conta
        async function criarNovaConta() {
            const resultadoDiv = document.getElementById('nova-conta-resultado');
            resultadoDiv.innerHTML = '<div class="info">⏳ Criando nova conta...</div>';
            
            try {
                const response = await fetch('/criar_conta', { method: 'POST' });
                const data = await response.json();
                
                if (data.success) {
                    resultadoDiv.innerHTML = `
                        <div class="success">
                            <h3>✅ Nova Conta Criada com Sucesso!</h3>
                            <p><strong>Endereço:</strong> ${data.result.endereco}</p>
                            <p><strong>Saldo Inicial:</strong> ${data.result.saldo_inicial} ETH</p>
                            <p><strong>Transação:</strong> ${data.result.transaction_hash}</p>
                            <div class="private-key-warning">
                                <h4>⚠️ ATENÇÃO: SALVE SUA CHAVE PRIVADA!</h4>
                                <p><strong>Chave Privada:</strong> ${data.result.chave_privada}</p>
                                <p>Esta é a única vez que você verá esta chave. Salve-a em um local seguro!</p>
                            </div>
                            <button onclick="fazerLoginComEndereco('${data.result.endereco}')" class="success">
                                🔑 Fazer Login com Esta Conta
                            </button>
                        </div>
                    `;
                } else {
                    resultadoDiv.innerHTML = `<div class="error">❌ ${data.result}</div>`;
                }
            } catch (error) {
                resultadoDiv.innerHTML = `<div class="error">❌ Erro: ${error.message}</div>`;
            }
        }

        // Função para fazer login
        async function fazerLogin(event) {
            event.preventDefault();
            const endereco = document.getElementById('login-endereco').value;
            await fazerLoginComEndereco(endereco);
        }

        // Função auxiliar para login com endereço
        async function fazerLoginComEndereco(endereco) {
            const resultadoDiv = document.getElementById('login-resultado');
            resultadoDiv.innerHTML = '<div class="info">⏳ Fazendo login...</div>';
            
            try {
                const formData = new FormData();
                formData.append('endereco', endereco);
                
                const response = await fetch('/login', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    resultadoDiv.innerHTML = `<div class="success">✅ Login realizado com sucesso!</div>`;
                    // Recarregar a página para atualizar a interface
                    setTimeout(() => {
                        window.location.reload();
                    }, 1000);
                } else {
                    resultadoDiv.innerHTML = `<div class="error">❌ ${data.result}</div>`;
                }
            } catch (error) {
                resultadoDiv.innerHTML = `<div class="error">❌ Erro: ${error.message}</div>`;
            }
        }

        // Função para fazer transferência
        async function fazerTransferencia(event) {
            event.preventDefault();
            const resultadoDiv = document.getElementById('transferencia-resultado');
            resultadoDiv.innerHTML = '<div class="info">⏳ Processando transferência...</div>';
            
            const formData = new FormData(event.target);
            
            try {
                const response = await fetch('/transferir', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.success) {
                    resultadoDiv.innerHTML = `
                        <div class="success">
                            <h3>✅ Transferência Realizada com Sucesso!</h3>
                            <p><strong>Hash:</strong> ${data.result.hash_transacao}</p>
                            <p><strong>Bloco:</strong> ${data.result.bloco}</p>
                            <p><strong>De:</strong> ${data.result.from}</p>
                            <p><strong>Para:</strong> ${data.result.to}</p>
                            <p><strong>Valor:</strong> ${data.result.value_ether} ETH</p>
                        </div>
                    `;
                    // Limpar formulário
                    event.target.reset();
                    // Recarregar para atualizar saldo
                    setTimeout(() => {
                        window.location.reload();
                    }, 2000);
                } else {
                    resultadoDiv.innerHTML = `<div class="error">❌ ${data.result}</div>`;
                }
            } catch (error) {
                resultadoDiv.innerHTML = `<div class="error">❌ Erro: ${error.message}</div>`;
            }
        }

        // Função para consultar bloco
        async function consultarBloco(event) {
            event.preventDefault();
            const resultadoDiv = document.getElementById('bloco-resultado');
            resultadoDiv.innerHTML = '<div class="info">⏳ Consultando bloco...</div>';
            
            const formData = new FormData(event.target);
            
            try {
                const response = await fetch('/bloco', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                
                if (data.error) {
                    resultadoDiv.innerHTML = `<div class="error">❌ ${data.error}</div>`;
                } else {
                    resultadoDiv.innerHTML = `
                        <div class="success">
                            <h3>📦 Informações do Bloco</h3>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        </div>
                    `;
                }
            } catch (error) {
                resultadoDiv.innerHTML = `<div class="error">❌ Erro: ${error.message}</div>`;
            }
        }

        // Função para logout
        async function logout() {
            try {
                const response = await fetch('/logout');
                const data = await response.json();
                
                if (data.success) {
                    window.location.reload();
                }
            } catch (error) {
                console.error('Erro no logout:', error);
            }
        }

        // Adicionar feedback visual para os formulários
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                const button = this.querySelector('button');
                const originalText = button.textContent;
                button.textContent = '⏳ Processando...';
                button.disabled = true;
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.disabled = false;
                }, 3000);
            });
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    if not blockchain:
        return render_template_string(HTML_TEMPLATE, blockchain=False)
    
    try:
        estatisticas = blockchain.obter_estatisticas()
        accounts = blockchain.get_accounts_with_balances()
        
        # Atualizar informações da sessão se o usuário estiver logado
        if session.get('usuario_logado'):
            sucesso, info_usuario = blockchain.login(session['usuario_endereco'])
            if sucesso:
                session['usuario_saldo'] = info_usuario['saldo_ether']
                session['usuario_nonce'] = info_usuario['nonce']
        
        return render_template_string(HTML_TEMPLATE, 
                                   estatisticas=estatisticas, 
                                   accounts=accounts, 
                                   blockchain=True,
                                   session=session)
    except Exception as e:
        return render_template_string(HTML_TEMPLATE, blockchain=False)

@app.route('/criar_conta', methods=['POST'])
def criar_conta():
    if not blockchain:
        return jsonify({'success': False, 'result': 'Blockchain não disponível'})
    
    sucesso, resultado = blockchain.criar_nova_conta()
    return jsonify({'success': sucesso, 'result': resultado})

@app.route('/login', methods=['POST'])
def login():
    if not blockchain:
        return jsonify({'success': False, 'result': 'Blockchain não disponível'})
    
    endereco = request.form['endereco']
    sucesso, resultado = blockchain.login(endereco)
    
    if sucesso:
        # Armazenar informações na sessão
        session['usuario_logado'] = True
        session['usuario_endereco'] = endereco
        session['usuario_saldo'] = resultado['saldo_ether']
        session['usuario_nonce'] = resultado['nonce']
    
    return jsonify({'success': sucesso, 'result': resultado})

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})

@app.route('/transferir', methods=['POST'])
def transferir():
    if not blockchain:
        return jsonify({'success': False, 'result': 'Blockchain não disponível'})
    
    remetente_privada = request.form['remetente_privada']
    destinatario = request.form['destinatario']
    valor = float(request.form['valor'])
    sucesso, resultado = blockchain.transferir(remetente_privada, destinatario, valor)
    return jsonify({'success': sucesso, 'result': resultado})

@app.route('/bloco', methods=['POST'])
def bloco():
    if not blockchain:
        return jsonify({'error': 'Blockchain não disponível'})
    
    numero_bloco = request.form['numero_bloco']
    if numero_bloco == 'latest':
        info = blockchain.obter_info_bloco()
    else:
        try:
            info = blockchain.obter_info_bloco(int(numero_bloco))
        except ValueError:
            info = {'error': 'Número do bloco inválido'}
    return jsonify(info)

@app.route('/estatisticas')
def estatisticas():
    if not blockchain:
        return jsonify({'error': 'Blockchain não disponível'})
    return jsonify(blockchain.obter_estatisticas())

@app.route('/contas')
def contas():
    if not blockchain:
        return jsonify({'error': 'Blockchain não disponível'})
    return jsonify(blockchain.get_accounts_with_balances())

@app.route('/health')
def health():
    if blockchain and blockchain.w3.is_connected():
        return jsonify({'status': 'healthy', 'connected': True})
    return jsonify({'status': 'unhealthy', 'connected': False}), 503

if __name__ == "__main__":
    print("🌐 Iniciando Mini Blockchain App (Interface Web)")
    print("📖 Acesse: http://localhost:5000")
    print("🔍 Health check: http://localhost:5000/health")
    app.run(host='0.0.0.0', port=5000, debug=False)