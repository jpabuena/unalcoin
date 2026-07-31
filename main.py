from pathlib import Path
import sys
import time
from hashlib import sha256
from json import dumps
from dataclasses import asdict

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from blockchain.blockchain import Blockchain
from blockchain.block_builder import BlockBuilder
from blockchain.block import Block
from blockchain.coinbase import CoinbaseTransaction
from blockchain.transaction import Transaction
from crypto.hash import calculate_hash
from crypto.signature import verify_signature
from system.wallet import Wallet


def main():
    print("UNALCOIN — Demostración Criptográfica\n")

    print("SECCIÓN 1 — Criptografía Asimétrica: Generación de Claves\n")

    print("Cada usuario tiene un par de claves generadas con el algoritmo Ed25519:\n")
    print("  • Clave privada (sk): secreta. Se usa para FIRMAR transacciones.")
    print("  • Clave pública  (pk): pública. Actúa como dirección e identidad.\n")
    print("  La seguridad se basa en la dificultad del problema del logaritmo")
    print("  discreto sobre la curva elíptica Curve25519.")
    print()

    alice = Wallet()
    bob   = Wallet()
    eve   = Wallet()

    alice_addr = alice.pk.public_bytes_raw().hex()
    bob_addr   = bob.pk.public_bytes_raw().hex()
    eve_addr   = eve.pk.public_bytes_raw().hex()

    print(f"Alice  pk (dirección): {alice_addr[:40]}...")
    print(f"Bob    pk (dirección): {bob_addr[:40]}...")
    print(f"Eve    pk (dirección): {eve_addr[:40]}...")

    print("\nSECCIÓN 2 — Proof of Work: Resistencia a la Preimagen de SHA-256\n")

    chain = Blockchain(difficulty=3, mining_reward=50.0)

    print(f"Dificultad configurada: {chain.difficulty}")
    print(f"El hash válido debe comenzar con: '{'0' * chain.difficulty}'")
    print()
    print("SHA-256 tiene la propiedad de resistencia a la preimagen:")
    print("  dado un hash objetivo H, es computacionalmente inviable encontrar")
    print("  un mensaje m tal que SHA-256(m) = H.")
    print("Por eso el minero debe iterar el campo 'nonce' hasta encontrar un")
    print(f"  hash que empiece con {chain.difficulty} ceros — no existe atajo matemático.")
    print()

    print("Ilustración del proceso (datos simplificados):")
    sample = {"bloque": 1, "prev": chain.last_block.hash[:12], "nonce": 0}
    target_str = "0" * chain.difficulty
    shown = 0
    n = 0
    while shown < 5 or not sha256(dumps(sample, sort_keys=True).encode()).hexdigest().startswith(target_str):
        h = sha256(dumps(sample, sort_keys=True).encode()).hexdigest()
        if shown < 5 or h.startswith(target_str):
            valid = h.startswith(target_str)
            marker = "✓  ← ENCONTRADO" if valid else "✗"
            print(f"  nonce {n:>6}  →  {h[:36]}...  {marker}")
            shown += 1
            if valid:
                break
        n += 1
        sample["nonce"] = n
    print()

    print("Minando bloque 1 real para Alice (recompensa: 50 monedas):")
    builder1 = BlockBuilder(index=chain.length, previous_hash=chain.last_block.hash)
    builder1.set_coinbase(alice_addr, chain.mining_reward)
    t0 = time.time()
    block1 = builder1.mine(chain.difficulty)
    elapsed = time.time() - t0
    chain.add_block(block1)

    print(f"Nonce encontrado: {block1.nonce}  ({elapsed:.3f}s)")
    print(f"Hash válido:      {block1.hash}")
    print(f"Alice recibe {chain.mining_reward:.0f} monedas. Balance: {chain.get_balance(alice_addr):.1f}")

    print("\nSECCIÓN 3 — Firmas Digitales: Autenticidad e Integridad\n")

    print("Una firma digital (Ed25519) garantiza dos propiedades:")
    print("  1. AUTENTICIDAD:  solo quien posee sk puede producir una firma válida.")
    print("  2. INTEGRIDAD:    cualquier modificación al mensaje invalida la firma.")
    print()

    # 3a. Firma válida
    print("3a. Transacción legítima: Alice firma con su clave privada")
    tx_alice_bob = alice.create_transaction(bob_addr, 20.0)
    alice.sign(tx_alice_bob)
    valid = verify_signature(tx_alice_bob, alice.pk)
    print(f"Firma generada:  {tx_alice_bob.signature[:48]}...")
    print(f"Verificación con pk de Alice: {'VÁLIDA' if valid else 'INVÁLIDA'}")

    # 3b. Intento de forja (Eve firma con su propia clave)
    print("\n3b. Intento de forja: Eve usa su propia sk para firmar como Alice")
    print("  Eve construye una tx desde la dirección de Alice pero la firma con su sk:")
    impostor_tx = Transaction(alice_addr, eve_addr, 20.0, 0)
    impostor_tx.assign_sign(eve.sk.sign(impostor_tx.to_bytes()).hex())
    forgery_valid = verify_signature(impostor_tx, alice.pk)
    if not forgery_valid:
        print(f"Verificación con pk de Alice: INVÁLIDA")
        print("  La firma de Eve es matemáticamente inconsistente con pk_Alice.")
        print("  Ed25519: solo sk_Alice produce firmas verificables con pk_Alice.")
    valid_chain = chain.validate_transaction(impostor_tx)
    print(f"validate_transaction() = {valid_chain}  → rechazada por la blockchain")

    # 3c. Manipulación del mensaje (integridad)
    print("\n3c. Manipulación del mensaje: Eve modifica el monto de una tx firmada")
    demo_tx = Transaction(alice_addr, bob_addr, 20.0, 99)
    demo_tx.assign_sign(alice.sk.sign(demo_tx.to_bytes()).hex())
    print(f"  Firma original sobre monto=20:  {demo_tx.signature[:48]}...")
    object.__setattr__(demo_tx, "amount", 200.0)
    tampered_valid = verify_signature(demo_tx, alice.pk)
    if not tampered_valid:
        print(f"Verificación tras modificar monto 20 → 200: INVÁLIDA")
        print("  SHA-256 tiene efecto avalancha: un solo bit cambiado produce")
        print("  un hash completamente distinto, invalidando la firma.")

    print("\nSECCIÓN 4 — Doble Gasto: Cómo la Criptografía lo Previene\n")

    print(f"Balance de Alice: {chain.get_balance(alice_addr):.1f} monedas")
    print()

    # 4a. Impersonación
    print("4a. Impersonación: Eve intenta gastar fondos de Alice")
    print("  Eve firma una tx desde la dirección de Alice con su propia sk:")
    eve_as_alice = Transaction(alice_addr, eve_addr, 30.0, 0)
    eve_as_alice.assign_sign(eve.sk.sign(eve_as_alice.to_bytes()).hex())
    result = chain.validate_transaction(eve_as_alice)
    print(f"validate_transaction() = {result}")
    print("  Sin sk_Alice, nadie puede autorizar gastos desde su dirección.")

    # 4b. Confirmar un bloque legítimo para que Alice tenga balance real
    print("\n4b. Alice confirma un pago legítimo a Bob")
    print("  Alice envía 20 monedas a Bob (bloque 2)...")
    builder2 = BlockBuilder(index=chain.length, previous_hash=chain.last_block.hash)
    builder2.add_transaction(tx_alice_bob)
    block2 = builder2.mine(chain.difficulty)
    chain.add_block(block2)
    print(f"Bloque 2 añadido. Balance de Alice: {chain.get_balance(alice_addr):.1f} monedas.")

    # 4c. Doble gasto clásico: mismo saldo gastado dos veces en el mismo bloque
    print("\n4c. Doble gasto clásico: gastar el mismo saldo dos veces en un bloque")
    balance_alice = chain.get_balance(alice_addr)
    print(f"  Alice tiene {balance_alice:.1f} monedas.")
    print(f"  Intenta incluir en el mismo bloque dos transacciones:")
    print(f"    tx1: Alice → Bob   {balance_alice * 0.8:.0f} monedas")
    print(f"    tx2: Alice → Eve   {balance_alice * 0.8:.0f} monedas")
    print(f"  Total intentado: {balance_alice * 1.6:.0f} monedas (más del saldo disponible)")
    print()

    tx_ds1 = alice.create_transaction(bob_addr,  balance_alice * 0.8)
    tx_ds2 = alice.create_transaction(eve_addr,  balance_alice * 0.8)
    alice.sign(tx_ds1)
    alice.sign(tx_ds2)

    builder_ds = BlockBuilder(index=chain.length, previous_hash=chain.last_block.hash)
    builder_ds.add_transaction(tx_ds1)
    builder_ds.add_transaction(tx_ds2)
    ds_block = builder_ds.mine(chain.difficulty)

    ds_valid = chain.validate_transactions_lot(ds_block)
    print(f"validate_transactions_lot() = {ds_valid}  → bloque rechazado")
    print("  La blockchain acumula el gasto pendiente dentro del mismo lote:")
    print("  después de tx1, el saldo disponible de Alice se reduce; tx2")
    print("  excede ese saldo reducido y el bloque completo es descartado.")

    # 4d. Fondos insuficientes
    print("\n4d. Gasto mayor al balance disponible")
    print(f"  Alice intenta enviar {balance_alice + 10:.0f} monedas a Eve (solo tiene {balance_alice:.1f}):")
    tx_overdraft = alice.create_transaction(eve_addr, balance_alice + 10)
    alice.sign(tx_overdraft)
    builder_bad = BlockBuilder(index=chain.length, previous_hash=chain.last_block.hash)
    builder_bad.add_transaction(tx_overdraft)
    bad_block = builder_bad.mine(chain.difficulty)
    lot_valid = chain.validate_transactions_lot(bad_block)
    print(f"validate_transactions_lot() = {lot_valid}")
    print("  El libro mayor registra cada gasto confirmado. Cualquier intento")
    print("  de gastar más de lo disponible queda expuesto al validar el bloque.")

    print("\nSECCIÓN 5 — Inmutabilidad: Efecto Cascada de SHA-256\n")

    print("Estado actual de la cadena:")
    for b in chain.chain:
        label = "(genesis)" if b.index == 0 else ""
        print(f"  Bloque {b.index}  {label}  hash: {b.hash}")
    print()
    print(f"verify_chain() = {chain.verify_chain()}  → cadena íntegra")
    print()

    print("Ataque: modificamos el monto de la coinbase del bloque 1 (50 → 9999).")
    print("El atacante mantiene el hash original para intentar pasar desapercibido.")
    print()

    target_block  = chain._chain[1]
    original_cb   = target_block.transactions[0]
    tampered_cb   = CoinbaseTransaction(recipient=alice_addr, amount=9999.0)
    object.__setattr__(tampered_cb, "timestamp", original_cb.timestamp)

    tampered_block = Block(
        target_block.index,
        (tampered_cb,) + target_block.transactions[1:],
        target_block.previous_hash,
        target_block.nonce,
        target_block.timestamp,
        target_block.hash,      # el atacante conserva el hash viejo
    )
    chain._chain[1] = tampered_block

    data_check = asdict(tampered_block)
    del data_check["hash"]
    recalculated = calculate_hash(data_check)

    print(f"  Hash almacenado  (bloque 1): {target_block.hash}")
    print(f"  Hash recalculado (bloque 1): {recalculated}")
    match = target_block.hash == recalculated
    print(f"  ¿Coinciden? {'SÍ' if match else 'NO — MANIPULACIÓN DETECTADA'}")
    print()
    print(f"verify_chain() = {chain.verify_chain()}  → cadena CORRUPTA")
    print()
    print("SHA-256 tiene efecto avalancha: cambiar cualquier byte del contenido")
    print("produce un hash completamente distinto. Para ocultar la manipulación,")
    print("el atacante tendría que re-minar todos los bloques siguientes, lo cual")
    print("requeriría superar el poder computacional acumulado de la red honesta.")

    # Resumen
    print("\nRESUMEN — Conceptos Criptográficos Demostrados\n")
    print("- Criptografía asimétrica Ed25519: par de claves pública/privada")
    print("- Proof of Work: resistencia a la preimagen de SHA-256 como puzzle")
    print("- Efecto avalancha: un cambio mínimo altera completamente el hash")
    print("- Firmas digitales: autenticidad (forja imposible) e integridad")
    print("- Prevención de doble gasto: impersonación + balance en cadena")
    print("- Inmutabilidad: modificar un bloque invalida toda la cadena")
    print()


if __name__ == "__main__":
    main()
