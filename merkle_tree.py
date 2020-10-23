from typing import List, Tuple
import random
import hashlib


class Transaction:
    def __init__(self, txid: str, value: float):
        self.txid = txid
        self.value = value

    def __repr__(self) -> str:
        return "(txid: {}, value: {})".format(self.txid, self.value)

    def __hash__(self) -> int:
        return hash((self.txid, self.value))


class BaseNode:
    def get_hash(self, value: str) -> str:
        return hashlib.sha256(value.encode()).hexdigest()

    def get_transaction_hash(self, tx:Transaction) -> str:
        return self.get_hash(tx.txid + str(tx.value))


class Node(BaseNode):
    def __init__(self):
        self.merkle_root: str = None
        self.transactions: List[Transaction] = []

    def add_transaction(self, tx: Transaction) -> None:
        self.transactions.append(tx)

    def build_merkle_root(self):
        def make(txs: List[Transaction]) -> str:
            if len(txs) == 1:
                tx_hash = self.get_transaction_hash(txs[0])
                print("tx->", txs[0].txid, tx_hash)
                return tx_hash
            else:
                half_pointer = int(len(txs) / 2)
                left_hash = make(txs[half_pointer:])
                right_hash = make(txs[:half_pointer])
                root_hash = self.get_hash(left_hash + right_hash)
                print(root_hash)
                return root_hash

        self.merkle_root = make(self.transactions)

    def get_merkle_path(self, txid: str) -> List[str]:
        def make(txs: List[Transaction]) -> Tuple[str, bool, List[str]]:
            if len(txs) == 1:
                tx_hash = self.get_transaction_hash(txs[0])
                if txs[0].txid == txid:
                    return tx_hash, True, []
                else:
                    return tx_hash, False, []
            else:
                half_pointer = int(len(txs) / 2)
                left_hash, left_exists, left_path = make(txs[half_pointer:])
                right_hash, right_exists, right_path = make(txs[:half_pointer])
                root_hash = self.get_hash(left_hash + right_hash)

                if left_exists == True:
                    left_path += ["R"+right_hash]
                    return root_hash, True, left_path

                if right_exists == True:
                    right_path += ["L"+left_hash]
                    return root_hash, True, right_path

                return root_hash, False, []

        _, _, merkle_path = make(self.transactions)
        return merkle_path


class ThinNode(BaseNode):
    def __init__(self, full_node: Node):
        self.full_node = full_node

    def verify_transaction(self, tx: Transaction) -> str:
        merkle_path = self.full_node.get_merkle_path(tx.txid)
        accum_hash = self.get_transaction_hash(tx)
        for _hash in merkle_path:
            if _hash[0] == "L":
                accum_hash = self.get_hash(_hash[1:] + accum_hash)
            elif _hash[0] == "R":
                accum_hash = self.get_hash(accum_hash + _hash[1:])
        return accum_hash

    def is_valid_transaction(self, tx: Transaction) -> bool:
        return self.full_node.merkle_root == self.verify_transaction(tx)


if __name__ == "__main__":
    full_node = Node()
    thin_node = ThinNode(full_node)

    random_transactions = [
        Transaction(str(i), round(random.uniform(1, 100), 2))
        for i in range(1, 9)
    ]

    for tx in random_transactions:
        full_node.add_transaction(tx)

    full_node.build_merkle_root()

    print("Transactions:", full_node.transactions)

    print("Merkle Root:", full_node.merkle_root)

    valid_transaction = random.choice(random_transactions)
    print(
        "Merkle Path of a valid transaction:",
        full_node.get_merkle_path(valid_transaction.txid)
    )

    print("Valid Transaction:", valid_transaction)
    verification_hash = thin_node.verify_transaction(valid_transaction)
    print(verification_hash, full_node.merkle_root == verification_hash)

    fake_transaction = Transaction("9999", round(random.uniform(1, 100), 2))
    print("Fake Transaction:", fake_transaction)
    verification_hash = thin_node.verify_transaction(fake_transaction)
    print(verification_hash, full_node.merkle_root == verification_hash)