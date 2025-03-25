# Blockchain-based File Storage

## How to Run the Application

1. Install required libraries:
   ```bash
   pip install -r requirements.txt
   ```
2. Open one terminal and start the server/peer:
   ```bash
   python peer.py
   ```
3. Open another terminal and start the client:
   ```bash
   python run_app.py
   ```
4. Copy the link from the client terminal and paste it in any browser.
5. To experiment with different Proof of Work concepts:
   ```bash
   python POW_Comparison.py
   ```

## Project Overview

This project creates a web-based decentralized file storage application using blockchain technology. Users can upload as many files as they like (one at a time), and others, as well as the uploader, can download and access the files. Files can be of any type and size. The project ensures that files are immutable, meaning they cannot be deleted or altered.

When a peer uploads a file, it's stored in a block, which includes the username, file size, and file data. These blocks are added to the blockchain, making them secure and tamper-proof. The blockchain prevents modification or deletion of files, ensuring the integrity of the stored data.

## Importance of Blockchain

Blockchain provides a secure, decentralized way to store digital information. It acts as an open ledger, allowing multiple parties to access and validate data simultaneously. In this project, we store file-related data in a blockchain, allowing users to upload and download files securely. The blockchain uses the SHA256 cryptographic algorithm for security, and a Proof of Work (PoW) consensus algorithm to validate new blocks. Miners must solve a cryptographic puzzle to add a block to the blockchain. In this project, miners must find a hash value that starts with three zeros.

## Proof of Work Algorithm

Proof of Work (PoW) is a consensus mechanism used in blockchain to maintain decentralization. It requires miners to solve cryptographic puzzles before they can add a new block to the blockchain. Miners who solve these puzzles more quickly can add a new block.

Two different Proof of Work algorithms are implemented in this project. Both algorithms solve the same puzzle, but in different ways. In the first algorithm, the nonce is randomly generated, while in the second one, the nonce is incremented by one. We analyze the performance and behavior of both algorithms in the `POW_Comparison.py` file.

## Proof of Work Algorithm Comparison

### Difference:

1. First algorithm: `Nonce = random.randint(0, 99999999)`
2. Second algorithm: `Nonce += 1`

### Running time of the first algorithm:

|               | Attempt #1 | Attempt #2 | Attempt #3 | Attempt #4 |
|---------------|------------|------------|------------|------------|
| Difficulty #2 | 0.00018    | 0.00281    | 0.00102    | 0.00039    |            
| Difficulty #3 | 0.00069    | 0.03207    | 0.00485    | 0.00356    |            
| Difficulty #4 | 0.13479    | 0.22688    | 0.34565    | 0.19841    |            
| Difficulty #5 | 4.06034    | 2.08288    | 0.58391    | 0.2094     |            

### Running time of the second algorithm:

|               | Attempt #1 | Attempt #2 | Attempt #3 | Attempt #4 |
|---------------|------------|------------|------------|------------|
| Difficulty #2 | 0.00035    | 0.00080    | 0.00062    | 0.00108    |            
| Difficulty #3 | 0.02190    | 0.02463    | 0.02104    | 0.01625    |            
| Difficulty #4 | 0.00366    | 0.03813    | 0.32095    | 0.02145    |            
| Difficulty #5 | 0.04403    | 3.10820    | 1.53688    | 1.50288    |            

### Why the First Algorithm is Better:

#### Probability of Valid Output & Running Time

For lower difficulty levels, the running time doesn't differ much. However, for higher difficulty levels, the first algorithm (random nonce) tends to be faster. This is because, in the second algorithm (incremental nonce), the chances of getting the correct nonce decrease as transactions are added while PoW is running. In the first algorithm, since the nonce is chosen randomly, it has a higher probability of finding the correct value faster.

#### Security

The second algorithm is less secure because the nonce value can be estimated based on the running time. If someone knows the running time and can estimate the range of the nonce, they could potentially break the blockchain system, which relies on the integrity of all connected blocks.

## Issues with the First Algorithm

Calculating random values can be expensive. To improve efficiency, we might use random functions with constant or faster running times, such as `random.random()` instead of `random.randint()`.

Proof of Work is computationally expensive, requiring significant resources. An alternative is Proof of Stake (PoS), where validators are chosen based on the amount of cryptocurrency they hold. PoS is more resource-efficient but still effective for maintaining a decentralized network.

## On-Chain vs Off-Chain Blockchain

Blockchain can be classified into two types: On-chain and Off-chain.

### On-chain Blockchain

On-chain blockchain stores all data within the blocks. It is more secure because the data is encapsulated in secure blocks. However, it can be slower and more resource-intensive.

### Off-chain Blockchain

Off-chain blockchain stores only metadata in the blocks, with the actual data stored elsewhere. This is less resource-heavy and faster but may be less secure.

### Advantages of On-chain Blockchain:

- More secure, as the data is encapsulated in secure blocks.
- Data recovery is easier in case of a system breach.

### Disadvantages of On-chain Blockchain:

- Slower due to the large amount of data processed.
- More expensive and resource-intensive to maintain.

For this project, we implemented an on-chain blockchain, where the entire file data, including the file size and name, is stored in each block.
