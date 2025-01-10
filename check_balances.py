import aiohttp
from proxy_tools import load_proxies, get_next_proxy, check_ip


# Функция для проверки баланса на адресе
async def check_balance(address):
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

    url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, proxy=rnd_proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    balance = data.get('final_balance', 0)
                    return balance
                else:
                    print(f"Ошибка при получении баланса для {address}: {response.status}")
                    return None
    except Exception as e:
        print(f"Ошибка при запросе баланса для {address}: {e}")
        return None