import json
import os
import time
from web3 import Web3
from dotenv import load_dotenv
from flask import Flask, jsonify, request, render_template_string

load_dotenv()

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

    def get_accounts(self):
        """Retorna todas as contas disponíveis"""
        return self.w3.eth.accounts

    def cadastrar_usuario(self, endereco, saldo_inicial=10):
        """Cadastra um novo usuário com saldo inicial"""
        try:
            if not self.w3.is_address(endereco):
                return False, "Endereço inválido"
            
            saldo_wei = self.w3.to_wei(saldo_inicial, 'ether')
            conta_principal = self.w3.eth.accounts[0]
            
            transacao = {
                'from': conta_principal,
                'to': endereco,
                'value': saldo_wei,
                'gas': 21000,
                'gasPrice': self.w3.to_wei('50', 'gwei')
            }
            
            transacao_assinada = self.w3.eth.account.sign_transaction(
                transacao, 
                os.getenv('PRIVATE_KEY')
            )
            tx_hash = self.w3.eth.send_raw_transaction(transacao_assinada.rawTransaction)
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
        
        saldo = self.w3.eth.get_balance(endereco)
        transacao_count = self.w3.eth.get_transaction_count(endereco)
        
        return True, {
            'endereco': endereco,
            'saldo_ether': saldo / 10**18,
            'saldo_wei': saldo,
            'nonce': transacao_count,
            'is_contract': self.w3.eth.get_code(endereco) != b''
        }
    
    def transferir(self, remetente_privada, destinatario, valor_ether):
        """Realiza transferência entre contas"""
        try:
            conta_remetente = self.w3.eth.account.from_key(remetente_privada).address
            valor_wei = self.w3.to_wei(valor_ether, 'ether')
            nonce = self.w3.eth.get_transaction_count(conta_remetente)
            
            transacao = {
                'nonce': nonce,
                'to': destinatario,
                'value': valor_wei,
                'gas': 21000,
                'gasPrice': self.w3.to_wei('50', 'gwei'),
                'chainId': self.w3.eth.chain_id
            }
            
            transacao_assinada = self.w3.eth.account.sign_transaction(transacao, remetente_privada)
            tx_hash = self.w3.eth.send_raw_transaction(transacao_assinada.rawTransaction)
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
        bloco = self.w3.eth.get_block(numero_bloco)
        return {
            'numero': bloco.number,
            'hash': bloco.hash.hex(),
            'hash_anterior': bloco.parentHash.hex(),
            'transacoes': len(bloco.transactions),
            'timestamp': bloco.timestamp,
            'dificuldade': bloco.difficulty,
            'gas_used': bloco.gasUsed,
            'gas_limit': bloco.gasLimit,
            'miner': bloco.miner,
            'size': bloco.size
        }
    
    def obter_transacao(self, hash_transacao):
        """Obtém detalhes de uma transação"""
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
    
    def obter_estatisticas(self):
        """Retorna estatísticas da rede"""
        ultimo_bloco = self.w3.eth.get_block('latest')
        return {
            'block_number': ultimo_bloco.number,
            'total_accounts': len(self.w3.eth.accounts),
            'gas_price': self.w3.eth.gas_price,
            'chain_id': self.w3.eth.chain_id,
            'is_mining': self.w3.eth.mining,
            'protocol_version': self.w3.eth.protocol_version
        }

# Interface Web com Flask
app = Flask(__name__)
blockchain = BlockchainApp()

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Mini Blockchain App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .card { background: #f5f5f5; padding: 20px; margin: 10px 0; border-radius: 8px; }
        button { background: #007bff; color: white; padding: 10px 15px; border: none; border-radius: 4px; cursor: pointer; }
        input, textarea { width: 100%; padding: 8px; margin: 5px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔗 Mini Blockchain App</h1>
        
        <div class="card">
            <h2>Estatísticas da Rede</h2>
            <pre>{{ estatisticas | tojson(indent=2) }}</pre>
        </div>

        <div class="card">
            <h2>Contas Disponíveis</h2>
            <ul>
                {% for account in accounts %}
                <li>{{ account }} - Saldo: {{ blockchain.login(account)[1].saldo_ether }} ETH</li>
                {% endfor %}
            </ul>
        </div>

        <div class="card">
            <h2>Cadastrar Usuário</h2>
            <form action="/cadastrar" method="post">
                <input type="text" name="endereco" placeholder="Endereço Ethereum" required>
                <input type="number" name="saldo" placeholder="Saldo inicial (ETH)" value="10" step="0.1">
                <button type="submit">Cadastrar</button>
            </form>
        </div>

        <div class="card">
            <h2>Login</h2>
            <form action="/login" method="post">
                <input type="text" name="endereco" placeholder="Endereço Ethereum" required>
                <button type="submit">Login</button>
            </form>
        </div>

        <div class="card">
            <h2>Transferir</h2>
            <form action="/transferir" method="post">
                <textarea name="remetente_privada" placeholder="Chave privada do remetente" required></textarea>
                <input type="text" name="destinatario" placeholder="Endereço do destinatário" required>
                <input type="number" name="valor" placeholder="Valor em ETH" step="0.001" required>
                <button type="submit">Transferir</button>
            </form>
        </div>

        <div class="card">
            <h2>Informações do Bloco</h2>
            <form action="/bloco" method="post">
                <input type="text" name="numero_bloco" placeholder="Número do bloco (ou 'latest')" value="latest">
                <button type="submit">Consultar</button>
            </form>
        </div>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    estatisticas = blockchain.obter_estatisticas()
    accounts = blockchain.get_accounts()
    return render_template_string(HTML_TEMPLATE, estatisticas=estatisticas, accounts=accounts, blockchain=blockchain)

@app.route('/cadastrar', methods=['POST'])
def cadastrar():
    endereco = request.form['endereco']
    saldo = float(request.form.get('saldo', 10))
    sucesso, resultado = blockchain.cadastrar_usuario(endereco, saldo)
    return jsonify({'success': sucesso, 'result': resultado})

@app.route('/login', methods=['POST'])
def login():
    endereco = request.form['endereco']
    sucesso, resultado = blockchain.login(endereco)
    return jsonify({'success': sucesso, 'result': resultado})

@app.route('/transferir', methods=['POST'])
def transferir():
    remetente_privada = request.form['remetente_privada']
    destinatario = request.form['destinatario']
    valor = float(request.form['valor'])
    sucesso, resultado = blockchain.transferir(remetente_privada, destinatario, valor)
    return jsonify({'success': sucesso, 'result': resultado})

@app.route('/bloco', methods=['POST'])
def bloco():
    numero_bloco = request.form['numero_bloco']
    if numero_bloco == 'latest':
        info = blockchain.obter_info_bloco()
    else:
        info = blockchain.obter_info_bloco(int(numero_bloco))
    return jsonify(info)

@app.route('/estatisticas')
def estatisticas():
    return jsonify(blockchain.obter_estatisticas())

# Interface de linha de comando
def main_cli():
    print("🔗 Inicializando Mini Blockchain App...")
    blockchain_app = BlockchainApp()
    
    while True:
        print("\n" + "="*50)
        print("           MINI BLOCKCHAIN APP")
        print("="*50)
        print("1. 📝 Cadastrar usuário")
        print("2. 🔐 Login")
        print("3. 💸 Transferir")
        print("4. 📦 Informações do bloco")
        print("5. 📊 Estatísticas da rede")
        print("6. 📋 Listar contas")
        print("7. 🌐 Iniciar interface web")
        print("8. 🚪 Sair")
        print("="*50)
        
        opcao = input("Escolha uma opção: ").strip()
        
        if opcao == '1':
            endereco = input("Endereço do novo usuário: ").strip()
            saldo = input("Saldo inicial (padrão 10 ETH): ").strip()
            saldo = float(saldo) if saldo else 10.0
            sucesso, mensagem = blockchain_app.cadastrar_usuario(endereco, saldo)
            print("✅" if sucesso else "❌", mensagem)
        
        elif opcao == '2':
            endereco = input("Endereço para login: ").strip()
            sucesso, resultado = blockchain_app.login(endereco)
            if sucesso:
                print("✅ Login bem-sucedido!")
                for key, value in resultado.items():
                    print(f"   {key}: {value}")
            else:
                print("❌", resultado)
        
        elif opcao == '3':
            privada = input("Chave privada do remetente: ").strip()
            destinatario = input("Endereço do destinatário: ").strip()
            valor = float(input("Valor em ETH: ").strip())
            sucesso, resultado = blockchain_app.transferir(privada, destinatario, valor)
            print("✅" if sucesso else "❌", resultado)
        
        elif opcao == '4':
            bloco_input = input("Número do bloco (ou 'latest'): ").strip()
            info_bloco = blockchain_app.obter_info_bloco(bloco_input if bloco_input != 'latest' else 'latest')
            for key, value in info_bloco.items():
                print(f"   {key}: {value}")
        
        elif opcao == '5':
            stats = blockchain_app.obter_estatisticas()
            for key, value in stats.items():
                print(f"   {key}: {value}")
        
        elif opcao == '6':
            accounts = blockchain_app.get_accounts()
            print("📋 Contas disponíveis:")
            for i, account in enumerate(accounts):
                saldo = blockchain_app.w3.eth.get_balance(account) / 10**18
                print(f"   {i+1}. {account} - {saldo} ETH")
        
        elif opcao == '7':
            print("🌐 Iniciando interface web na porta 5000...")
            print("📖 Acesse: http://localhost:5000")
            app.run(host='0.0.0.0', port=5000, debug=False)
        
        elif opcao == '8':
            print("👋 Saindo...")
            break
        
        else:
            print("❌ Opção inválida!")

if __name__ == "__main__":
    # Executar interface CLI por padrão
    main_cli()