import argparse
import json
import logging
import sys
import time
from dnslib import DNSRecord, RR, QTYPE, RCODE, A, AAAA, CNAME, PTR
from dnslib.server import DNSServer, BaseResolver, DNSLogger

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

DEFAULT_TTL = 300

def load_config(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
        norm = {}
        for name, rec in cfg.items():
            key = name.rstrip('.').lower()
            norm[key] = rec
        return norm
    except Exception as e:
        logging.exception("Ошибка загрузки конфига %s: %s", path, e)
        return {}

class JSONResolver(BaseResolver):
    def __init__(self, config, ttl=DEFAULT_TTL):
        self.config = config
        self.ttl = ttl

    def resolve(self, request, handler):
        reply = request.reply()
        try:
            q = request.q
            qname = str(q.qname).rstrip('.').lower()
            qtype = q.qtype
            try:
                qtype_name = QTYPE[qtype]
            except Exception:
                qtype_name = str(qtype)
            logging.info("Query %s type=%s from %s", qname, qtype_name, getattr(handler, 'client_address', None))
            zone = self.config.get(qname)
            if not zone:
                reply.header.rcode = RCODE.NXDOMAIN
                reply.header.set_aa(1)
                return reply

            def add_rr(rtype, rdata):
                reply.add_answer(RR(qname, rtype, ttl=self.ttl, rdata=rdata))

            if qtype == QTYPE.A or qtype == QTYPE.ANY:
                if 'A' in zone:
                    addrs = zone['A'] if isinstance(zone['A'], list) else [zone['A']]
                    for ip in addrs:
                        add_rr(QTYPE.A, A(ip))

            if qtype == QTYPE.AAAA or qtype == QTYPE.ANY:
                if 'AAAA' in zone:
                    addrs = zone['AAAA'] if isinstance(zone['AAAA'], list) else [zone['AAAA']]
                    for ip in addrs:
                        add_rr(QTYPE.AAAA, AAAA(ip))

            if qtype == QTYPE.CNAME or qtype == QTYPE.ANY:
                if 'CNAME' in zone:
                    target = zone['CNAME']
                    if not target.endswith('.'):
                        target = target + '.'
                    add_rr(QTYPE.CNAME, CNAME(target))

            if qtype == QTYPE.PTR or qtype == QTYPE.ANY:
                if 'PTR' in zone:
                    target = zone['PTR']
                    if not target.endswith('.'):
                        target = target + '.'
                    add_rr(QTYPE.PTR, PTR(target))

            if len(reply.rr) == 0:
                reply.header.rcode = RCODE.NOERROR

            reply.header.set_aa(1)
            return reply
        except Exception as e:
            logging.exception("Ошибка в резолвере: %s", e)
            reply.header.rcode = RCODE.SERVFAIL
            return reply

def main():
    parser = argparse.ArgumentParser(description="Простой DNS-сервер (JSON-config)")
    parser.add_argument('--host', default='127.0.0.1', help='адрес для прослушки')
    parser.add_argument('--port', type=int, default=5353, help='порт (по умолчанию 5353)')
    parser.add_argument('--config', default='config.json', help='путь к JSON конфигу')
    parser.add_argument('--ttl', type=int, default=DEFAULT_TTL, help='TTL для записей')
    parser.add_argument('--tcp', action='store_true', help='включить TCP')
    args = parser.parse_args()

    cfg = load_config(args.config)
    if not cfg:
        logging.warning("Конфиг пустой или не загружен: %s", args.config)
    else:
        logging.debug("Loaded config: %s", cfg)

    resolver = JSONResolver(cfg, ttl=args.ttl)
    logger = DNSLogger(log='request,reply,errors')

    try:
        server = DNSServer(resolver, port=args.port, address=args.host, logger=logger, tcp=args.tcp)
        logging.info("Created DNSServer object")
    except Exception as e:
        logging.exception("Ошибка при создании DNS-сервера (вероятно, порт занят): %s", e)
        sys.exit(1)

    try:
        logging.info("Запуск DNS-сервера на %s:%d (tcp=%s) с конфигом %s", args.host, args.port, args.tcp, args.config)
        server.start()
    except Exception as e:
        logging.exception("Ошибка при запуске DNS-сервера: %s", e)
        sys.exit(1)

if __name__ == '__main__':
    main()

