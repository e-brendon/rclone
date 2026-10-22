#!/usr/bin/env python3
"""
Sincroniza um diretório local com o Google Drive usando rclone.

Uso:
    python sync.py /diretorio gdrive:/Diretorio
    python sync.py /diretorio gdrive:/Diretorio --dry-run
    python sync.py /diretorio gdrive:/Diretorio --modo copy
    python sync.py /diretorio gdrive:/Diretorio --log /var/log/gdrive_sync.log

Logs gerados:
    Sincronizado ...
    Erro: <mensagem do erro>
    Aviso: <mensagem do aviso>
"""

import argparse
import json
import logging
import shutil
import subprocess
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Mensagens do rclone (nível info) que indicam que um arquivo foi sincronizado
MSGS_SINCRONIZADO = ("Copied", "Updated", "Moved", "Deleted", "Made directory", "Removing directory")


def configurar_log(caminho_log: Path) -> logging.Logger:
    logger = logging.getLogger("gdrive_sync")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formato = logging.Formatter("%(asctime)s | %(message)s", "%Y-%m-%d %H:%M:%S")

    arquivo = RotatingFileHandler(
        caminho_log, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    arquivo.setFormatter(formato)
    logger.addHandler(arquivo)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formato)
    logger.addHandler(console)

    return logger


def processar_linha(linha: str, log: logging.Logger, contadores: dict) -> None:
    """Interpreta uma linha de log (JSON) do rclone e grava no log."""
    linha = linha.strip()
    if not linha:
        return

    try:
        dados = json.loads(linha)
    except json.JSONDecodeError:
        # Linha fora do formato JSON: registra como aviso para não perder informação
        log.warning(f"Aviso: {linha}")
        contadores["avisos"] += 1
        return

    nivel = str(dados.get("level", "")).lower()
    msg = str(dados.get("msg", "")).strip()
    objeto = dados.get("object")
    texto = f"{objeto}: {msg}" if objeto else msg

    if nivel in ("error", "critical", "alert", "emergency"):
        log.error(f"Erro: {texto}")
        contadores["erros"] += 1
    elif nivel in ("warning", "notice"):
        log.warning(f"Aviso: {texto}")
        contadores["avisos"] += 1
    elif nivel == "info" and objeto and msg.startswith(MSGS_SINCRONIZADO):
        log.info(f"Sincronizado: {objeto} ({msg})")
        contadores["arquivos"] += 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sincroniza um diretório local com o Google Drive via rclone."
    )
    parser.add_argument("origem", help="Diretório local (ex: /dados/fotos)")
    parser.add_argument("destino", help="Destino rclone (ex: gdrive:/Fotos)")
    parser.add_argument(
        "--modo",
        choices=("sync", "copy"),
        default="sync",
        help="sync = espelha (apaga no destino o que não existe na origem); "
        "copy = só copia/atualiza, nunca apaga (padrão: sync)",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Simula, sem alterar nada no destino"
    )
    parser.add_argument(
        "--log",
        default=str(Path(__file__).resolve().with_name("sync.log")),
        help="Arquivo de log (padrão: sync.log ao lado do script)",
    )
    args = parser.parse_args()

    log = configurar_log(Path(args.log))

    # Validações
    if shutil.which("rclone") is None:
        log.error("Erro: rclone não encontrado no PATH. Instale em https://rclone.org/install/")
        return 1

    origem = Path(args.origem).expanduser()
    if not origem.is_dir():
        log.error(f"Erro: diretório de origem não existe ou não é um diretório: {origem}")
        return 1

    if ":" not in args.destino:
        log.error(
            f"Erro: destino inválido '{args.destino}'. Use o formato remoto:caminho (ex: gdrive:/Diretorio)"
        )
        return 1

    comando = [
        "rclone",
        args.modo,
        str(origem),
        args.destino,
        "-v",
        "--use-json-log",
        "--stats",
        "0",
    ]
    if args.dry_run:
        comando.append("--dry-run")

    log.info(f"Aviso: iniciando {args.modo}{' (dry-run)' if args.dry_run else ''}: {origem} -> {args.destino}")

    contadores = {"erros": 0, "avisos": 0, "arquivos": 0}

    try:
        proc = subprocess.Popen(
            comando,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,  # com --use-json-log o rclone escreve os logs em stderr
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        for linha in proc.stderr:
            processar_linha(linha, log, contadores)
        codigo = proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        log.error("Erro: sincronização interrompida pelo usuário")
        return 130
    except OSError as e:
        log.error(f"Erro: falha ao executar o rclone: {e}")
        return 1

    if codigo == 0 and contadores["erros"] == 0:
        log.info(
            f"Sincronizado: {origem} -> {args.destino} "
            f"({contadores['arquivos']} item(ns) alterado(s), {contadores['avisos']} aviso(s))"
        )
        return 0

    log.error(
        f"Erro: rclone terminou com código {codigo} "
        f"({contadores['erros']} erro(s), {contadores['avisos']} aviso(s))"
    )
    return codigo or 1


if __name__ == "__main__":
    sys.exit(main())
