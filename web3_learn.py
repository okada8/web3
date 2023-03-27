from web3 import Web3
from eth_account import Account
import json,time


#连接主网
def get_w3_by_network(baseurl):
    w3rpc = Web3(Web3.HTTPProvider(baseurl))
    if not w3rpc.is_connected():
        return "mainnet is not connected"
    return w3rpc

#查询eth余额
def eth_sumaccount(walletaddress,w3rpc):
    address = Web3.to_checksum_address(walletaddress)
    blancedata = w3rpc.eth.get_balance(address)
    blance = w3rpc.from_wei(blancedata,'ether')
    return blance

#创建钱包
def creatwallet(number):
    walletslist = []
    for id in range(number):
        account = Account.create('seed'+str(id))
        #私钥
        privatekey = account._key_obj
        #公钥
        publickey = privatekey.public_key
        #地址
        address = publickey.to_checksum_address()

        wallet = {
            "id":id,
            "address":address,
            "privatekey":str(privatekey),
            "publickey":str(publickey)
        }
        walletslist.append(wallet)
    with open("walletjson.json",'w') as file:
        json.dump(walletslist, file)

def get_wallet():
    with open("walletjson.json", 'r') as file:
        data = json.load(file)
    return data

#eth转账
def transfer_eth(w3,from_address,private_key,target_address,amount,gas_price=5,gas_limit=21000,chainId=4):
    from_address = Web3.toChecksumAddress(from_address)
    target_address = Web3.toChecksumAddress(target_address)
    nonce = w3.eth.getTransactionCount(from_address)  # 获取 nonce 值
    params = {
        'from': from_address,
        'nonce': nonce,
        'to': target_address,
        'value': w3.toWei(amount, 'ether'),
        'gas': gas_limit,
        'maxFeePerGas': w3.toWei(gas_price, 'gwei'),
        'maxPriorityFeePerGas': w3.toWei(gas_price, 'gwei'),
        'chainId': chainId,

    }
    try:
        signed_tx = w3.eth.account.signTransaction(params, private_key=private_key)
        txn = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
        return {'status': 'succeed', 'txn_hash': w3.toHex(txn), 'task': 'Transfer ETH'}
    except Exception as e:
        return {'status': 'failed', 'error': e, 'task': 'Transfer ETH'}

#zksync跨链转账
def bridge_zkSync_eth(w3, from_address, private_key, contract_address, amount_in_ether, chainId):
    from_address = Web3.toChecksumAddress(from_address)
    contract_address = Web3.toChecksumAddress(contract_address)
    ABI = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"anonymous":false,"inputs":[{"indexed":false,"internalType":"bytes","name":"pubkey","type":"bytes"},{"indexed":false,"internalType":"bytes","name":"withdrawal_credentials","type":"bytes"},{"indexed":false,"internalType":"bytes","name":"amount","type":"bytes"},{"indexed":false,"internalType":"bytes","name":"signature","type":"bytes"},{"indexed":false,"internalType":"bytes","name":"index","type":"bytes"}],"name":"DepositEvent","type":"event"},{"inputs":[{"internalType":"bytes","name":"pubkey","type":"bytes"},{"internalType":"bytes","name":"withdrawal_credentials","type":"bytes"},{"internalType":"bytes","name":"signature","type":"bytes"},{"internalType":"bytes32","name":"deposit_data_root","type":"bytes32"}],"name":"deposit","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[],"name":"get_deposit_count","outputs":[{"internalType":"bytes","name":"","type":"bytes"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"get_deposit_root","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"pure","type":"function"}]'
    amount_in_wei = w3.toWei(amount_in_ether, 'ether')
    nonce = w3.eth.getTransactionCount(from_address)

    tx_params = {
        'value': amount_in_wei,
        "nonce": nonce,
        'gas': 150000,
        'gasPrice': w3.toWei(2, 'gwei'),
        'maxFeePerGas': w3.toWei(8, 'gwei'),
        'maxPriorityFeePerGas': w3.toWei(2, 'gwei'),
        'chainId': chainId,
    }

    contract = w3.eth.contract(address=contract_address, abi=ABI)

    try:
        raw_txn = contract.functions.depositETH(amount_in_wei, from_address, 0, 0).buildTransaction(tx_params)
        signed_txn = w3.eth.account.sign_transaction(raw_txn, private_key=private_key)
        txn = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return {'status': 'succeed', 'txn_hash': w3.toHex(txn), 'task': 'zkSync Bridge ETH'}
    except Exception as e:
        return {'status': 'failed', 'error': e, 'task': 'zkSync Bridge ETH'}


if __name__ == "__main__":
    #Infura Project
    infura_web3_name = {
        1: "mainnet",
        2: "polygon-mainnet",
        3: "optimism-mainnet",
        4: "arbitrum-mainnet",
        5: "palm-mainnet",
        6: "avalanche-mainnet",
    }
    #1:组成infura_url
    INFURA_SECRET_KEY = ''
    infura_url = f'https://{infura_web3_name[1]}.infura.io/v3/{INFURA_SECRET_KEY}'
    #连接主网
    w3rpc = get_w3_by_network(baseurl=infura_url)
    #2:批量生成钱包，将信息存入文件
    creatwallet(number=100)
    #获取保存在文件中的钱包地址
    wallet_list = get_wallet()
    #批量转账
    #主钱包地址
    from_address = ''
    #著钱包私钥
    private_key = ''
    #转账数量
    amount = ''
    chainId = 1
    for i in wallet_list:
        blance = eth_sumaccount(walletaddress=from_address, w3rpc=w3rpc)
        if blance > amount:
            target_address = i.get('address')
            result = transfer_eth(w3=w3rpc,from_address=from_address,target_address=target_address,amount=amount,chainId=chainId)
            if result['status'] == 'succeed':
                print(result['txn_hash'])
                time.sleep(5)
            else:
                print(result)
        else:
            break
    #批量跨链zksync
    #要跨链eth的数量
    amount_in_ether = ''
    #zksync主网跨链合约
    contract_address = ''
    for i in wallet_list:
        from_address = i.get('address')
        blance = eth_sumaccount(walletaddress=from_address, w3rpc=w3rpc)
        if blance > amount_in_ether:
            private_key = i.get('privatekey')
            result = bridge_zkSync_eth(w3rpc, from_address, private_key, contract_address, amount_in_ether, chainId)
            if result['status'] == 'succeed':
                print(result['txn_hash'])
                time.sleep(5)
            else:
                print(result)
        else:
            break


