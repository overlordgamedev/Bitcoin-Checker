import random
import aiofiles
import aiohttp


# Асинхронная функция для получения прокси из текстового файла
async def load_proxies(proxy_file_path):
    try:
        # Используем асинхронное чтение файла
        async with aiofiles.open(proxy_file_path, mode="r") as file:
            proxies = [line.strip() async for line in file if line.strip()]
        return proxies
    except Exception as e:
        print(f"Ошибка загрузки прокси: {e}")
        return []


# Асинхронная функция для выбора рандомной прокси из списка
async def get_next_proxy(proxies):
    # Если список пустой
    if not proxies:
        print("Нет доступных прокси.")
        return None

    # Берем случайную прокси
    proxy_info = random.choice(proxies)
    # Разделяем прокси на части по знаку ":"
    parts = proxy_info.split(":")

    # Если частей не 4
    if len(parts) != 4:
        print(f"Неверный формат прокси: {proxy_info}")
        return None

    # Записываем каждую часть в отдельную переменную
    ip, port, username, password = parts

    # Собираем первые две части в виде ссылки
    proxy = f"http://{username}:{password}@{ip}:{port}"
    return proxy


# Асинхронная функция для проверки IP через httpbin
async def check_ip(proxy):
    url = "http://httpbin.org/ip"
    try:
        async with aiohttp.ClientSession() as session:
            # Делаем запрос через прокси
            async with session.get(url, proxy=proxy) as response:
                if response.status == 200:
                    data = await response.json()
                    ip = data.get("origin")
                    print(f"Прокси IP: {ip}")
                    return ip
                else:
                    print(f"Ошибка при проверке IP с прокси: {response.status}")
                    return None
    except Exception as e:
        print(f"Ошибка при проверке IP с прокси: {e}")
        return None