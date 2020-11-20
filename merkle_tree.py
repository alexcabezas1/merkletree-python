from typing import List, Tuple, Optional
import sys
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
        def make(txs: List[Transaction]) -> Tuple[str, str]:
            if len(txs) == 0:
                return "", ""
            elif len(txs) == 1:
                left_hash = self.get_transaction_hash(txs[0])
                return left_hash, left_hash
            elif len(txs) == 2:
                left_hash = self.get_transaction_hash(txs[0])
                right_hash = self.get_transaction_hash(txs[1])
                return left_hash, right_hash
            else:
                half_pointer = int(len(txs) / 2)
                left_hashes = make(txs[:half_pointer])
                right_hashes = make(txs[half_pointer:])

                left_hash = self.get_hash(left_hashes[0] + left_hashes[1])
                right_hash = self.get_hash(right_hashes[0] + right_hashes[1])
                return left_hash, right_hash

        left_hash, right_hash = make(self.transactions)
        self.merkle_root = self.get_hash(left_hash + right_hash)

    def get_merkle_path(self, txid: str) -> List[str]:
        def make(txs: List[Transaction]) -> Tuple[str, bool, List[str]]:
            if len(txs) == 0:
                return "", []
            elif len(txs) == 1:
                left_hash = self.get_transaction_hash(txs[0])
                root_hash = self.get_hash(left_hash + left_hash)
                if txs[0].txid == txid:
                    return root_hash, ["L" + left_hash]
                else:
                    return root_hash, []
            elif len(txs) == 2:
                left_hash = self.get_transaction_hash(txs[0])
                right_hash = self.get_transaction_hash(txs[1])
                root_hash = self.get_hash(left_hash + right_hash)
                if txs[0].txid == txid:
                    return root_hash, ["R" + right_hash]
                elif txs[1].txid == txid:
                    return root_hash, ["L" + left_hash]
                else:
                    return root_hash, []
            else:
                half_pointer = int(len(txs) / 2)
                left_hash, left_path = make(txs[:half_pointer])
                right_hash, right_path = make(txs[half_pointer:])
                root_hash = self.get_hash(left_hash + right_hash)

                if len(left_path) > 0:
                    left_path += ["R" + right_hash]
                    return root_hash, left_path
                elif len(right_path) > 0:
                    right_path += ["L" + left_hash]
                    return root_hash, right_path

                return root_hash, []

        _, merkle_path = make(self.transactions)

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
        for i in range(1, random.randint(5, 50))
    ]

    for tx in random_transactions:
        full_node.add_transaction(tx)

    full_node.build_merkle_root()

    print("Transactions:", full_node.transactions)

    print("Merkle Root:", full_node.merkle_root)

    try:
        valid_transaction = random.choice(random_transactions)
    except IndexError:
        sys.exit(1)

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
