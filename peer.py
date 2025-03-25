import json
from flask import Flask, jsonify, request
from Block import Block
from hashlib import sha256
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
app.logger = logging.getLogger(__name__)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending = []
        self.create_genesis_block()

    def create_genesis_block(self):
        genesis_block = Block(0, [], "0")
        self.chain.append(genesis_block)

    @property
    def last_block(self):
        return self.chain[-1]

    def new_transaction(self, transaction):
        try:
            if not isinstance(transaction, dict):
                raise ValueError("Transaction must be a dictionary")
                
            required = ["user", "v_file", "file_data", "file_size"]
            if not all(k in transaction for k in required):
                missing = [k for k in required if k not in transaction]
                raise ValueError(f"Missing required fields: {missing}")
                
            if not isinstance(transaction["file_data"], str):
                raise ValueError("file_data must be a string (hex encoded)")
                
            try:
                bytes.fromhex(transaction["file_data"])
            except ValueError:
                raise ValueError("file_data must be valid hex string")

            if not isinstance(transaction["file_size"], int) or transaction["file_size"] < 0:
                raise ValueError("file_size must be a positive integer")

            self.pending.append(transaction)
            return self.last_block.index + 1
            
        except Exception as e:
            app.logger.error(f"Transaction validation failed: {str(e)}")
            raise

    def mine(self):
        if not self.pending:
            app.logger.info("No pending transactions to mine")
            return None

        try:
            last_block = self.last_block
            new_block = Block(
                index=last_block.index + 1,
                transactions=self.pending,
                previous_hash=last_block.hash
            )

            while not new_block.hash.startswith('00'):
                new_block.nonce += 1
                new_block.hash = new_block.compute_hash()

            self.chain.append(new_block)
            self.pending = []
            app.logger.info(f"Mined block #{new_block.index}")
            return new_block
            
        except Exception as e:
            app.logger.error(f"Mining failed: {str(e)}")
            return None

    def add_block(self, block):
        if not self.is_valid_block(block):
            return False
        self.chain.append(block)
        return True

    def is_valid_block(self, block):
        last_block = self.last_block
        if block.index != last_block.index + 1:
            return False
        if block.previous_hash != last_block.hash:
            return False
        if block.compute_hash() != block.hash:
            return False
        return True

blockchain = Blockchain()

@app.route("/new_transaction", methods=["POST"])
def new_transaction():
    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON"}), 400
            
        tx = request.get_json()
        app.logger.info(f"Received transaction: {tx}")
        
        index = blockchain.new_transaction(tx)
        return jsonify({
            "message": "Transaction added",
            "block_index": index,
            "transaction": {
                "user": tx["user"],
                "v_file": tx["v_file"],
                "file_size": tx["file_size"]
            }
        }), 201
        
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        app.logger.error(f"Transaction processing failed: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route("/mine", methods=["GET"])
def mine():
    mined_block = blockchain.mine()
    if not mined_block:
        return jsonify({
            "message": "No transactions to mine",
            "pending_count": len(blockchain.pending)
        }), 200
    
    return jsonify({
        "message": "New Block Forged",
        "index": mined_block.index,
        "transactions": len(mined_block.transactions),
        "previous_hash": mined_block.previous_hash,
        "hash": mined_block.hash,
        "nonce": mined_block.nonce,
        "timestamp": mined_block.timestamp
    }), 200

@app.route("/chain", methods=["GET"])
def get_chain():
    chain_data = []
    for block in blockchain.chain:
        block_data = {
            "index": block.index,
            "transactions": block.transactions,
            "nonce": block.nonce,
            "hash": block.hash,
            "previous_hash": block.previous_hash,
            "timestamp": block.timestamp
        }
        chain_data.append(block_data)
    
    return jsonify({
        "length": len(chain_data),
        "chain": chain_data
    })

@app.route("/pending_tx", methods=["GET"])
def get_pending_tx():
    return jsonify({
        "pending": [{
            "user": tx["user"],
            "v_file": tx["v_file"],
            "file_size": tx["file_size"]
        } for tx in blockchain.pending],
        "count": len(blockchain.pending)
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8800, debug=True)