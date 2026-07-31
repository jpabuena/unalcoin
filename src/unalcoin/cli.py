"""
CLI interactiva para UNALCOIN.

Permite crear wallets, crear y firmar transacciones, minar bloques,
consultar balances, verificar la integridad de la cadena y simular un
ataque de manipulación — todo reutilizando las clases ya existentes del
proyecto (Wallet, Blockchain, BlockBuilder). No agrega ninguna lógica
criptográfica nueva, solo una capa de interacción por menú.
"""

from .blockchain.blockchain import Blockchain
from .blockchain.block_builder import BlockBuilder
from .blockchain.coinbase import CoinbaseTransaction
from .blockchain.exceptions import BlockchainError, BlockBuilderError, TransactionError
from .system.wallet import Wallet
from .system.exceptions import WalletError


class CLIState:
    """Guarda el estado de la sesión: la cadena, las wallets creadas y el mempool."""

    def __init__(self, difficulty: int = 3, mining_reward: float = 50.0):
        self.chain = Blockchain(difficulty=difficulty, mining_reward=mining_reward)
        self.wallets: dict[str, Wallet] = {}
        self.mempool: list = []  # transacciones firmadas, pendientes de minar


def print_menu():
    print("\n" + "=" * 50)
    print("UNALCOIN — CLI interactiva")
    print("=" * 50)
    print("1. Crear wallet")
    print("2. Listar wallets y balances")
    print("3. Crear y firmar una transacción")
    print("4. Ver transacciones pendientes (mempool)")
    print("5. Minar un bloque")
    print("6. Ver la cadena de bloques")
    print("7. Verificar integridad de la cadena")
    print("8. Simular un ataque (manipular un bloque)")
    print("9. Salir")
    print()


def elegir_wallet(state: CLIState, prompt: str = "Nombre de la wallet: "):
    """Pide un nombre de wallet ya existente. Retorna (nombre, wallet) o (None, None)."""
    nombre = input(prompt).strip()
    wallet = state.wallets.get(nombre)
    if wallet is None:
        print(f"No existe ninguna wallet llamada '{nombre}'.")
        return None, None
    return nombre, wallet


def crear_wallet(state: CLIState):
    nombre = input("Nombre para la nueva wallet (ej: alice): ").strip()
    if not nombre:
        print("El nombre no puede estar vacío.")
        return
    if nombre in state.wallets:
        print(f"Ya existe una wallet llamada '{nombre}'.")
        return

    wallet = Wallet()
    state.wallets[nombre] = wallet
    address = wallet.pk.public_bytes_raw().hex()
    print(f"Wallet '{nombre}' creada.")
    print(f"Dirección (llave pública): {address}")


def listar_wallets(state: CLIState):
    if not state.wallets:
        print("No hay wallets creadas todavía. Usa la opción 1.")
        return

    print(f"\n{'Nombre':<12} {'Balance':>10}  Dirección")
    print("-" * 70)
    for nombre, wallet in state.wallets.items():
        address = wallet.pk.public_bytes_raw().hex()
        balance = state.chain.get_balance(address)
        print(f"{nombre:<12} {balance:>10.2f}  {address[:24]}...")


def crear_transaccion(state: CLIState):
    if len(state.wallets) < 2:
        print("Necesitas al menos 2 wallets para crear una transacción. Crea otra primero.")
        return

    print("Wallets disponibles:", ", ".join(state.wallets.keys()))
    emisor_nombre, emisor = elegir_wallet(state, "Wallet que envía: ")
    if emisor is None:
        return

    receptor_nombre = input("Wallet que recibe: ").strip()
    receptor = state.wallets.get(receptor_nombre)
    if receptor is None:
        print(f"No existe ninguna wallet llamada '{receptor_nombre}'.")
        return
    receptor_addr = receptor.pk.public_bytes_raw().hex()

    monto_str = input("Monto a enviar: ").strip()
    try:
        monto = float(monto_str)
    except ValueError:
        print("Monto inválido, debe ser un número.")
        return

    try:
        tx = emisor.create_transaction(receptor_addr, monto)
        emisor.sign(tx)
    except (TransactionError, WalletError) as e:
        print(f"No se pudo crear la transacción: {e.description}")
        return

    state.mempool.append(tx)
    print(f"Transacción creada y firmada: {emisor_nombre} -> {receptor_nombre}, monto={monto} (nonce={tx.nonce}).")
    print("Queda en el mempool hasta que se mine un bloque (opción 5).")


def ver_mempool(state: CLIState):
    if not state.mempool:
        print("El mempool está vacío.")
        return

    print(f"\nTransacciones pendientes ({len(state.mempool)}):")
    for i, tx in enumerate(state.mempool):
        print(f"  [{i}] {tx.sender[:12]}... -> {tx.recipient[:12]}...  monto={tx.amount}  nonce={tx.nonce}")


def minar_bloque(state: CLIState):
    if not state.wallets:
        print("Necesitas al menos una wallet para recibir la recompensa. Crea una primero.")
        return

    minero_nombre, minero = elegir_wallet(state, "¿Qué wallet mina el bloque (recibe la recompensa)? ")
    if minero is None:
        return
    minero_addr = minero.pk.public_bytes_raw().hex()

    builder = BlockBuilder(index=state.chain.length, previous_hash=state.chain.last_block.hash)
    builder.set_coinbase(minero_addr, state.chain.mining_reward)

    # pre-validamos economía (nonce esperado + balance disponible) con la misma
    # lógica que usa internamente validate_transactions_lot, para poder decirle
    # al usuario la razón específica de un descarte antes de minar en vano
    pending_spend: dict[str, float] = {}
    pending_next_nonce: dict[str, int] = {}
    incluidas = []

    for tx in state.mempool:
        try:
            builder.add_transaction(tx)  # valida la firma; lanza si es inválida
        except BlockBuilderError as e:
            print(f"Transacción descartada (firma inválida): {e.description}")
            continue

        last_nonce = state.chain.get_last_transactions_nonce(tx.sender)
        expected_nonce = pending_next_nonce.get(tx.sender, last_nonce + 1)
        if tx.nonce != expected_nonce:
            print(f"Transacción descartada: nonce {tx.nonce} fuera de secuencia (se esperaba {expected_nonce}).")
            builder.transactions.remove(tx)
            continue

        available = state.chain.get_balance(tx.sender) - pending_spend.get(tx.sender, 0.0)
        if tx.amount > available:
            print(f"Transacción descartada: fondos insuficientes (disponible={available:.2f}, monto={tx.amount}).")
            builder.transactions.remove(tx)
            continue

        pending_next_nonce[tx.sender] = expected_nonce + 1
        pending_spend[tx.sender] = pending_spend.get(tx.sender, 0.0) + tx.amount
        incluidas.append(tx)

    if not incluidas:
        print("No hay transacciones válidas en el mempool, se minará solo con la recompensa.")

    print(f"Minando bloque {builder.index} con dificultad {state.chain.difficulty}...")
    block = builder.mine(state.chain.difficulty)

    try:
        state.chain.add_block(block)
    except BlockchainError as e:
        print(f"El bloque fue rechazado por la blockchain: {e.description}")
        print("Las transacciones no se pierden, siguen en el mempool.")
        return

    # limpiar del mempool solo las transacciones que quedaron confirmadas
    for tx in incluidas:
        state.mempool.remove(tx)

    print(f"Bloque {block.index} añadido correctamente.")
    print(f"  hash:  {block.hash}")
    print(f"  nonce: {block.nonce}")
    print(f"'{minero_nombre}' recibió {state.chain.mining_reward} monedas de recompensa.")


def ver_cadena(state: CLIState):
    print(f"\nLa cadena tiene {state.chain.length} bloque(s):\n")
    for block in state.chain.chain:
        etiqueta = " (génesis)" if block.index == 0 else ""
        print(f"Bloque {block.index}{etiqueta}")
        print(f"  hash:          {block.hash}")
        print(f"  hash anterior: {block.previous_hash}")
        print(f"  nonce:         {block.nonce}")
        print(f"  transacciones: {len(block.transactions)}")
        for tx in block.transactions:
            if isinstance(tx, CoinbaseTransaction):
                print(f"    · COINBASE -> {tx.recipient[:16]}...  monto={tx.amount}")
            else:
                print(f"    · {tx.sender[:12]}... -> {tx.recipient[:12]}...  monto={tx.amount}  nonce={tx.nonce}")
        print()


def verificar_cadena(state: CLIState):
    valida = state.chain.verify_chain()
    if valida:
        print("La cadena es íntegra: todos los hashes y enlaces son consistentes.")
    else:
        print("¡La cadena está CORRUPTA! Algún bloque fue manipulado o no enlaza correctamente.")


def simular_ataque(state: CLIState):
    if state.chain.length < 2:
        print("Necesitas al menos un bloque además del génesis para este ejemplo. Mina uno primero (opción 5).")
        return

    print(f"La cadena tiene bloques con índice 0 a {state.chain.length - 1}.")
    idx_str = input("¿Qué bloque quieres manipular? (índice): ").strip()
    try:
        idx = int(idx_str)
        block = state.chain._chain[idx]
    except (ValueError, IndexError):
        print("Índice inválido.")
        return

    if not block.transactions:
        print("Ese bloque no tiene transacciones para manipular.")
        return

    print("Transacciones de ese bloque:")
    for i, tx in enumerate(block.transactions):
        tipo = "COINBASE" if isinstance(tx, CoinbaseTransaction) else "normal"
        print(f"  [{i}] ({tipo}) monto={tx.amount}")

    tx_idx_str = input("¿Qué transacción quieres modificar? (índice): ").strip()
    monto_str = input("Nuevo monto (el atacante lo cambia sin re-minar): ").strip()
    try:
        tx_idx = int(tx_idx_str)
        nuevo_monto = float(monto_str)
        tx = block.transactions[tx_idx]
    except (ValueError, IndexError):
        print("Entrada inválida.")
        return

    monto_original = tx.amount
    # el atacante modifica el contenido directamente, pero el hash guardado
    # en el bloque NO se recalcula — así se comporta una manipulación real
    object.__setattr__(tx, "amount", nuevo_monto)

    print(f"\nMonto modificado en bloque {block.index}: {monto_original} -> {nuevo_monto}")
    print("El hash almacenado en el bloque no cambió — el atacante lo dejó igual.")
    print("\nResultado de verify_chain() después del ataque:")
    verificar_cadena(state)
    print("\nEsto ocurre porque el hash guardado ya no coincide con el contenido real:")
    print("cualquier cambio, por mínimo que sea, produce un hash SHA-256 completamente")
    print("distinto al que quedó grabado, así que la manipulación queda expuesta.")


def main():
    print("Bienvenido a la CLI interactiva de UNALCOIN.\n")

    dif_str = input("Dificultad de minado (Enter para usar 3 por defecto): ").strip()
    try:
        difficulty = int(dif_str) if dif_str else 3
    except ValueError:
        print("Valor inválido, se usará dificultad 3.")
        difficulty = 3

    print("Creando el bloque génesis, un momento...")
    state = CLIState(difficulty=difficulty)
    print(f"Listo. Hash del génesis: {state.chain.last_block.hash}")

    acciones = {
        "1": crear_wallet,
        "2": listar_wallets,
        "3": crear_transaccion,
        "4": ver_mempool,
        "5": minar_bloque,
        "6": ver_cadena,
        "7": verificar_cadena,
        "8": simular_ataque,
    }

    while True:
        try:
            print_menu()
            opcion = input("Elige una opción: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n¡Hasta luego!")
            break

        if opcion == "9":
            print("¡Hasta luego!")
            break

        accion = acciones.get(opcion)
        if accion is None:
            print("Opción inválida, intenta de nuevo.")
            continue

        try:
            accion(state)
        except Exception as e:
            print(f"Ocurrió un error inesperado: {e}")


if __name__ == "__main__":
    main()
