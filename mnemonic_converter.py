import asyncio
import aiofiles
from bip_utils import Bip39SeedGenerator, Bip44, Bip49, Bip84, Bip44Coins, Bip49Coins, Bip84Coins, Bip44Changes
import hashlib
import base58
from check_balances import check_balance
from transactions import get_utxos


async def private_key_to_wif(private_key_hex):
    # Префикс, означающий, что ключ будет для монеты Bitcoin
    prefix = b'\x80'

    # Конвертирует ключ из хекса в байты
    key_bytes = bytes.fromhex(private_key_hex)

    # Добавляем префикс для компрессированного ключа
    key_bytes += b'\x01'

    # Добавляем префикс к ключу
    extended_key = prefix + key_bytes

    # Хешируем корневой ключ с помощью SHA256
    first_hash = hashlib.sha256(extended_key).digest()

    # Хешируем хешированный ранее ключ
    second_hash = hashlib.sha256(first_hash).digest()

    # Контрольная сумма: первые 4 байта результата второго хеша
    checksum = second_hash[:4]

    # Добавляем к ключу контрольную сумму
    extended_key_with_checksum = extended_key + checksum

    # Преобразуем получившийся ключ с контрольной суммой в формат base58
    encoded_key = base58.b58encode(extended_key_with_checksum)

    # Декодируем результат в строку
    wif_key = encoded_key.decode()

    return wif_key


# Генерация приватных ключей и адресов из мнемонической фразы
async def mnemonic_to_wallet(mnemonic):
    # Создаем пустой массив для хранения всех данных, полученных из мнемонической фразы
    wallets = []
    try:
        # Конвертация мнемонической фразы в её байтовое представление (seed)
        seed_bytes = Bip39SeedGenerator(mnemonic).Generate("")

        # Цикл, выполняющийся столько раз, сколько указано в depth
        for i in range(depth):
            # BIP44: Генерация внешних и внутренних адресов
            bip44 = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)

            # Внешние адреса (для приема монет)
            bip44_ctx_ext = bip44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
            bip44_address_ext = bip44_ctx_ext.PublicKey().ToAddress()
            bip44_private_key_ext = await private_key_to_wif(bip44_ctx_ext.PrivateKey().Raw().ToHex())

            # Внутренние адреса (для сдачи монет)
            bip44_ctx_int = bip44.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_INT).AddressIndex(i)
            bip44_address_int = bip44_ctx_int.PublicKey().ToAddress()
            bip44_private_key_int = await private_key_to_wif(bip44_ctx_int.PrivateKey().Raw().ToHex())

            # Добавляем оба типа адресов в список
            wallets.append((bip44_address_ext, bip44_private_key_ext, mnemonic))
            wallets.append((bip44_address_int, bip44_private_key_int, mnemonic))

            # BIP49: Генерация внешних и внутренних адресов
            bip49 = Bip49.FromSeed(seed_bytes, Bip49Coins.BITCOIN)

            # Внешние адреса (для приема монет)
            bip49_ctx_ext = bip49.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
            bip49_address_ext = bip49_ctx_ext.PublicKey().ToAddress()
            bip49_private_key_ext = await private_key_to_wif(bip49_ctx_ext.PrivateKey().Raw().ToHex())

            # Внутренние адреса (для сдачи монет)
            bip49_ctx_int = bip49.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_INT).AddressIndex(i)
            bip49_address_int = bip49_ctx_int.PublicKey().ToAddress()
            bip49_private_key_int = await private_key_to_wif(bip49_ctx_int.PrivateKey().Raw().ToHex())

            # Добавляем оба типа адресов в список
            wallets.append((bip49_address_ext, bip49_private_key_ext, mnemonic))
            wallets.append((bip49_address_int, bip49_private_key_int, mnemonic))

            # BIP84: Генерация внешних и внутренних адресов
            bip84 = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)

            # Внешние адреса (для приема монет)
            bip84_ctx_ext = bip84.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(i)
            bip84_address_ext = bip84_ctx_ext.PublicKey().ToAddress()
            bip84_private_key_ext = await private_key_to_wif(bip84_ctx_ext.PrivateKey().Raw().ToHex())

            # Внутренние адреса (для сдачи монет)
            bip84_ctx_int = bip84.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_INT).AddressIndex(i)
            bip84_address_int = bip84_ctx_int.PublicKey().ToAddress()
            bip84_private_key_int = await private_key_to_wif(bip84_ctx_int.PrivateKey().Raw().ToHex())

            # Добавляем оба типа адресов в список
            wallets.append((bip84_address_ext, bip84_private_key_ext, mnemonic))
            wallets.append((bip84_address_int, bip84_private_key_int, mnemonic))

        return wallets
    except Exception as e:
        print(f"Ошибка при генерации адресов: {e}")
        return []


# Асинхронная обработка одной мнемонической фразы
async def process_mnemonic(mnemonic_phrase):
    async with aiofiles.open(output_file_path, "a", encoding="utf-8") as output_file:
        # Убирает пробелы в начале и в конце мнемонической фразы если они есть
        mnemonic_phrase = mnemonic_phrase.strip()
        # Если мнемоническая фраза есть
        if mnemonic_phrase:
            # Вызываем функцию для генерации приватных ключей и адресов передавая в функцию мнемоническую фразу
            # В переменную записываются данные из функции генерации приватных ключей и адресов
            wallets = await mnemonic_to_wallet(mnemonic_phrase)

            # Если переменная не пустая
            if wallets:
                for wallet in wallets:
                    # Данные из переменной разбиваются на отдельные переменные для адресов, приватных ключей и т.д
                    address, private_key_wif, mnemonic = wallet
                    balance = await check_balance(address)
                    if balance > 500:

                        # Вызов функции для получения utxo
                        transaction_info = await get_utxos(address, private_key_wif)

                        # Добавляем данные транзакции в результат
                        result = (
                            f"=========================================================\n"
                            f"{mnemonic}:{private_key_wif}:{address}:{balance} Satoshi\n"
                            f"Сумма отправки: {transaction_info['amount_sent']} Satoshi\n"
                            f"Комиссия: {transaction_info['total_fee']} Satoshi\n"
                            f"=========================================================\n\n"
                        )
                    else:
                        # Если баланс меньше 500, возвращаем только базовые данные
                        result = (
                            f"=========================================================\n"
                            f"{mnemonic}:{private_key_wif}:{address}:{balance} Satoshi\n"
                            f"=========================================================\n\n"
                        )
                    # Данные из переменной result записываются в текстовый файл
                    await output_file.write(result)
                    # Вывод данных в консоль
                    print(result)
            else:
                print(f"Не удалось обработать фразу: {mnemonic_phrase}")


# Основная асинхронная функция для обработки всех фраз
async def process_mnemonics():
    # Считывает каждую строку из текстового файла
    async with aiofiles.open(file_path, "r", encoding="utf-8") as file:
        mnemonics = await file.readlines()

    # Создаем задачи для всех мнемонических фраз
    # В цикле перебираются все мнемонические фразы, записываются в переменную mnemonic и передаются в функцию process_mnemonic
    tasks = [process_mnemonic(mnemonic) for mnemonic in mnemonics]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    file_path = "mnemonics.txt"  # Путь к файлу с мнемоническими фразами
    output_file_path = "output.txt"  # Путь к файлу для записи результата
    depth = 1  # Количество генерируемых адресов для каждой фразы

    asyncio.run(process_mnemonics())
