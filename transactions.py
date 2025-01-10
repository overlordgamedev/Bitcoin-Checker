import aiohttp
from bitcoinlib.transactions import Transaction
from bitcoinlib.networks import Network
from proxy_tools import load_proxies, get_next_proxy, check_ip

service_address = ""  # Укажите адрес биткойн-кошелька, на который нужно отправить монеты


# Асинхронная функция для отправки запросов на ноду
async def request_node(method, params):
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": 1
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                # Публичная нода
                "https://go.getblock.io/4fa66b9bad67415e9b8f5fb5bfb0f54b",
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status == 200:
                    # Если запрос удачный, возвращаем ответ с данными
                    return await response.json()
                else:
                    print(f"Ошибка: {response.status}, {await response.text()}")
                    return None
    except aiohttp.ClientError as e:
        print(f"Ошибка запроса: {e}")
        return None


# Асинхронная функция для получения всех UTXO с адреса через BlockCypher
async def get_utxos(address, private_key_wif):
    proxies = await load_proxies("proxy.txt")
    rnd_proxy = await get_next_proxy(proxies)

    if not rnd_proxy:
        print("Нет доступных прокси.")
        return None

    # Перед проверкой баланса проверим IP
    ip = await check_ip(rnd_proxy)

    if ip:
        print(f"Используем прокси с IP: {ip}")
    else:
        print("Не удалось проверить IP. Прокси может быть недоступен.")
        return None

    url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}?unspentOnly=true"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=rnd_proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    # Пустой список для записи всех UTXO
                    utxos = []
                    # Обрабатываем каждый UTXO
                    for txref in data.get("txrefs", []) + data.get("unconfirmed_txrefs", []):
                        # Извлекаем данные из UTXO
                        utxos.append({
                            "tx_hash": txref["tx_hash"],
                            "tx_output_n": txref["tx_output_n"],
                            "value": txref["value"]
                        })

                    if utxos:
                        # Создаем транзакцию и возвращаем сумму вывода и комиссию
                        transaction_info = await create_transaction(utxos, private_key_wif, address)
                        return transaction_info
                    else:
                        print(f"Нет доступных UTXO для адреса {address}")
                        return None
                else:
                    print(f"Ошибка при получении UTXO для {address}: {response.status}")
                    return None
    except Exception as e:
        print(f"Ошибка при запросе UTXO для {address}: {e}")
        return None


# Асинхронная функция для создания транзакции и подписания
async def create_transaction(utxos, private_key_wif, address):
    # Определяем тип witness в зависимости от формата адреса
    if address.startswith("1"):
        witness_type = 'legacy'
    elif address.startswith("bc1"):
        witness_type = 'segwit'
    else:
        raise ValueError("Неподдерживаемый формат адреса: адрес должен быть legacy или segwit")

    tx = Transaction(network=Network('bitcoin'), replace_by_fee=False, witness_type=witness_type)

    base_fee = 170  # Фиксированная базовая комиссия
    fee_per_input = 150  # Комиссия за каждый вход
    total_fee = base_fee
    total_amount = 0

    # Указываем входы транзакции
    for utxo in utxos:
        total_amount += utxo["value"]  # Общая сумма входов
        total_fee += fee_per_input  # Увеличиваем комиссию на каждый вход
        tx.add_input(
            prev_txid=utxo["tx_hash"],
            output_n=utxo["tx_output_n"],
            value=utxo["value"],
            address=address
        )

    # Вычисляем сумму для отправки после вычета комиссии
    amount_to_send = total_amount - total_fee

    # Добавление выхода с адресом и суммой
    tx.add_output(address=service_address, value=int(round(amount_to_send)))

    # Подписываем транзакцию
    tx.sign(private_key_wif)
    signed_tx = tx.as_hex()

    # Отправляем транзакцию
    await request_node("sendrawtransaction", [str(signed_tx)])

    # Возвращаем сумму вывода и комиссию
    return {
        "amount_sent": amount_to_send,
        "total_fee": total_fee
    }
