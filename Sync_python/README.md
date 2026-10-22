# Python Rclone Sync

Um script em Python robusto e amigável projetado para automatizar a sincronização de diretórios locais com o Google Drive utilizando o **rclone**, com tratamento estruturado de logs e rastreio detalhado de eventos.

---

## Funcionalidades

- **Sincronização Flexível (`sync` ou `copy`):** Escolha se deseja espelhar diretórios (removendo arquivos órfãos no destino) ou apenas copiar e atualizar.
- **Modo de Simulação (`--dry-run`):** Permite testar o comportamento da sincronização sem alterar nenhum dado real.
- **Logs Inteligentes em JSON:** Lê e interpreta as saídas estruturadas em JSON do `rclone`, gerando logs limpos tanto no terminal quanto em arquivo rotativo (`RotatingFileHandler`).
- **Tratamento de Erros Robusto:** Captura interrupções manuais (`Ctrl+C`), valida a existência do executável do rclone e checa a integridade dos diretórios de origem.

---

##  Pré-requisitos

1. **Python 3.6+** instalado no sistema.
2. **Rclone** instalado e configurado (com um remoto válido, ex: `sync:` apontando para o seu Google Drive).

---

## Como Usar

A execução é feita diretamente via terminal passando o diretório de origem local e o destino do rclone.

```bash
python sync.py <DIRETORIO_ORIGEM> <DESTINO_RCLONE> [OPÇÕES]
```

### Exemplos Práticos:

* **Sincronização padrão (Modo `sync` espelhado):**
  ```bash
  python sync.py /var/www/html sync:/share_sync
  ```

* **Apenas copiar/atualizar arquivos (Modo `copy` - sem apagar nada no destino):**
  ```bash
  python sync.py /dados/backup sync:/share_sync --modo copy
  ```

* **Simular a sincronização sem alterar arquivos (Dry-run):**
  ```bash
  python sync.py /var/www/html sync:/share_sync --dry-run
  ```

* **Definir um caminho de log personalizado:**
  ```bash
  python sync.py /var/www/html sync:/share_sync --log /var/log/meu_sync.log
  ```

---

## Parâmetros Disponíveis

| Parâmetro | Descrição | Padrão |
| :--- | :--- | :--- |
| `origem` | Caminho do diretório local que será sincronizado. | *Obrigatório* |
| `destino` | Destino no formato `remoto:caminho` (ex: `sync:/pasta`). | *Obrigatório* |
| `--modo` | Modos aceitos: `sync` (espelha) ou `copy` (apenas adiciona/atualiza). | `sync` |
| `--dry-run` | Executa a simulação sem gravar modificações no destino. | `False` |
| `--log` | Caminho do arquivo de saída de logs. | `sync.log` (ao lado do script) |

---

## Formato de Saída dos Logs

O script gera entradas categorizadas padronizadas para facilitar monitoramentos e auditorias:

- `Sincronizado: ...` (para arquivos copiados, atualizados ou diretórios criados)
- `Aviso: ...` (para alertas informativos ou linhas fora do padrão JSON)
- `Erro: ...` (para falhas críticas de execução ou erros reportados pelo rclone)