from pathlib import Path
import random
from datetime import timedelta, date
import shutil
import csv
import json
import gzip
import unicodedata

LANDING_DIR = Path("landing")
SEED = 42
BASE_DATE = date(2026, 10, 28)
N_DAYS = 10
N_PER_FILE = 20
PRODUCTS = {
    "SKU-001": 19.90,
    "SKU-002": 49.90,
    "SKU-003": 39.90,
    "SKU-004": 129.00,
    "SKU-005": 7.50
}
DEPOSITS = ["SP", "MG", "RJ"]
FIRST_NAMES = ["João", "Guilherme", "André", "Lucas", "Paulo", "Gabriel", "Maria", "Bruna", "Laura", "Letícia"]
LAST_NAMES = ["Silva", "Conceição", "Oliveira", "Souza", "Pereira", "Costa", "Rodrigues", "Villela", "Nascimento", "Carvalho"]
COLUMNS_VENDAS = ["id_venda", "data", "sku", "quantidade", "valor"]
COLUMNS_ESTOQUE = ["sku", "quantidade", "deposito"]
COLUMNS_CLIENTES = ["id_cliente", "nome", "email"]

def reset_dir(path: str):
    if Path(path).exists():
        shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    
    path.mkdir(parents=True, exist_ok=True)
    
def generate_dates(n: int) -> list[date]:
    dates = []
    
    for day in range(n):
        dates.append(BASE_DATE - timedelta(days=day))
    
    dates.reverse()
    return dates

def make_vendas_rows(dt: date, n: int) -> list[dict]:
    final_rows = []
    
    for v in range(n):
        sku = random.choice(list(PRODUCTS))
        qtt = random.randint(1, 10)
        final_rows.append({
            "id_venda": f"V{dt.isoformat()}-{v+1:03d}",
            "data": dt.strftime("%Y-%m-%d"),
            "sku": sku,
            "quantidade": qtt,
            "valor": round(PRODUCTS[sku]*qtt, 2)
        })
    
    return final_rows

def make_estoque_rows() -> list[dict]:
    final_rows = []
    
    for sku in PRODUCTS:
        for deposit in DEPOSITS:
            final_rows.append({
                        "sku": sku,
                        "quantidade": random.randint(0, 200),
                        "deposito": deposit
                    })
    
    return final_rows

def make_clientes(n: int) -> list[dict]:
    final_rows = []
    
    for c in range(n):
        client = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        client_clean = unicodedata.normalize("NFD", client)
        client_clean = client_clean.encode("ascii", "ignore").decode("utf-8")
        final_rows.append({
                "id_cliente": c+1,
                "nome": client,
                "email": f"{client_clean.lower().replace(' ', '')}{c+1}@exemplo.com.br"
            })
    
    return final_rows

def write_csv(path: str, fieldnames: list[str], rows: list[dict]) -> str:
    type_file = gzip.open(path, "wt", newline="", encoding="utf-8") if str(path).endswith(".gz") else open(path, "w", newline="", encoding="utf-8")
    with type_file as file:
        writer = csv.DictWriter(file, fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    return path

def write_json(path: str, data: list) -> str:
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)

    return path

def write_vendas(base: str, dt: date, compress: bool) -> str:
    tmp_path = (base).joinpath(f"vendas_{dt.isoformat()}.csv")
    final_path = Path(str(tmp_path) + ".gz") if compress else tmp_path
    registers = make_vendas_rows(dt, N_PER_FILE)
    destiny = write_csv(final_path, COLUMNS_VENDAS, registers)
    
    return destiny

def write_estoque(base: str, dt: date, compress: bool) -> str:
    tmp_path = (base).joinpath(f"estoque_{dt.isoformat()}.csv")
    final_path = Path(str(tmp_path) + ".gz") if compress else tmp_path
    registers = make_estoque_rows()
    destiny = write_csv(final_path, COLUMNS_ESTOQUE, registers)
    
    return destiny

def write_clientes(base: str, dt: date) -> str:
    
    final_path = (base).joinpath(f"clientes_{dt.isoformat()}.json")
    registers = make_clientes(N_PER_FILE)
    destiny = write_json(final_path, registers)
    
    return destiny

def write_edge_cases(base: Path) -> list[str]:
    edge_paths = []
    
    edge_clients = make_clientes(N_PER_FILE)
    edge_paths.append(write_json(base.joinpath("clientes_28-10-2026.json"), edge_clients))
    
    edge_vendas = make_vendas_rows(BASE_DATE, N_PER_FILE)
    edge_paths.append(write_csv(Path(base.joinpath("vendas_2026-02-31.csv")), COLUMNS_VENDAS, edge_vendas))
    
    edge_fornecedores = [
        {"id_fornecedor": 1, "nome": "BRFornecedor"},
        {"id_fornecedor": 2, "nome": "EUAFornecedor"},
        {"id_fornecedor": 3, "nome": "JAPFornecedor"}
    ]
    edge_paths.append(write_csv(Path(base.joinpath("fornecedores_2026-10-28.csv")), ["id_fornecedor", "nome"], edge_fornecedores))
    
    edge_estoque = make_estoque_rows()
    for item in edge_estoque:
        del item["sku"]
    edge_paths.append(write_csv(Path(base.joinpath("estoque_2026-10-17.csv")), ["quantidade", "deposito"], edge_estoque))
    
    edge_clients_2 = json.dumps(make_clientes(N_PER_FILE))
    base.joinpath("clientes_2026-10-17.json").write_text(edge_clients_2[:len(edge_clients_2) // 2], encoding="utf-8")
    edge_paths.append(base.joinpath("clientes_2026-10-17.json"))
    
    base.joinpath("vendas_2026-10-16.csv").touch()
    edge_paths.append(base.joinpath("vendas_2026-10-16.csv"))
    
    shutil.copy2(base.joinpath("vendas_2026-10-28.csv"), base.joinpath("vendas_2026-10-28 (1).csv"))
    edge_paths.append(base.joinpath("vendas_2026-10-28 (1).csv"))
    
    base.joinpath(".DS_Store").write_text("test", encoding="utf-8")
    edge_paths.append(base.joinpath(".DS_Store"))
    
    base.joinpath("~vendas.tmp").write_text("test", encoding="utf-8")
    edge_paths.append(base.joinpath("~vendas.tmp"))
    
    base.joinpath(Path("lote_extra")).mkdir(parents=True, exist_ok=True)
    edge_vendas_2 = write_vendas(base.joinpath(Path("lote_extra")), date(2026, 10, 18), False)
    edge_paths.append(edge_vendas_2)
    
    return edge_paths
    
def main(root_path: str):
    final_path = root_path.joinpath(LANDING_DIR)
    sales = []
    estoque = []
    clients = []
    random.seed(SEED)
    reset_dir(final_path)
    dates = generate_dates(N_DAYS)
    for pst, day in enumerate(dates):
        if pst < 3:
            sales.append(Path(write_vendas(final_path, day, True)).resolve())
        else:
            sales.append(Path(write_vendas(final_path, day, False)).resolve())
            
        estoque.append(Path(write_estoque(final_path, day, False)).resolve())
        clients.append(Path(write_clientes(final_path, day)).resolve())
    edges = write_edge_cases(final_path)
    print(f"vendas: {len(sales)} | estoque: {len(estoque)} | clientes: {len(clients)} | borda: {len(edges)} | total: {len(sales) + len(estoque) + len(clients) + len(edges)}")
    
if __name__ == "__main__":
    root_path = Path(__file__).resolve().parents[1]
    main(root_path)