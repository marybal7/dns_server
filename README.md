# Простой DNS сервер

DNS-сервер на Python с использованием dnslib. Обслуживает A, AAAA, CNAME, PTR записи из JSON-конфига. Можно использовать как кастомный DNS для перехвата/замены доменов.

## Требования
- Python 3.6+
- dnslib: `pip install dnslib`

## Сборка/установка
- Склонировать репозиторий: `git clone https://github.com/marybal7/dns_server.git`
- Установить зависимости: `pip install -r requirements.txt` (создать файл с "dnslib")
- Создать config.json (пример в репозитории).

## Запуск
- `python3 dns_server.py --host 127.0.0.1 --port 5454 --config config.json`
- Для поддержки TCP: добавьте флаг --tcp.
- Убедитесь, что порт свободен. Проверьте: ss -uln | grep 5454.
- Логи сервера выводятся в консоль (запросы, ответы, ошибки).
  
## Тестирование:
- `dig @127.0.0.1 -p 5454 example.com A`
- `dig @127.0.0.1 -p 5454 example.com AAAA`
- `dig @127.0.0.1 -p 5454 www.example.com CNAME`
- `dig @127.0.0.1 -p 5454 -x 127.0.0.1`
