TRAINING_MARKETPLACE_ABI = [
    {
        "inputs": [],
        "name": "nextJobId",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [{"internalType": "uint256", "name": "jobId", "type": "uint256"}],
        "name": "getJob",
        "outputs": [
            {
                "components": [
                    {"internalType": "address", "name": "requester", "type": "address"},
                    {"internalType": "address", "name": "provider", "type": "address"},
                    {"internalType": "address", "name": "attestor", "type": "address"},
                    {"internalType": "uint256", "name": "targetEscrow", "type": "uint256"},
                    {"internalType": "uint256", "name": "escrowBalance", "type": "uint256"},
                    {"internalType": "bytes32", "name": "jobSpecHash", "type": "bytes32"},
                    {"internalType": "bytes32", "name": "attestationHash", "type": "bytes32"},
                    {"internalType": "bytes32", "name": "settlementHash", "type": "bytes32"},
                    {"internalType": "uint256", "name": "providerPayout", "type": "uint256"},
                    {"internalType": "uint256", "name": "requesterRefund", "type": "uint256"},
                    {"internalType": "enum JobStatus", "name": "status", "type": "uint8"},
                ],
                "internalType": "struct Job",
                "name": "job",
                "type": "tuple",
            }
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "requester", "type": "address"},
            {"indexed": True, "internalType": "address", "name": "provider", "type": "address"},
            {"indexed": False, "internalType": "address", "name": "attestor", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "targetEscrow", "type": "uint256"},
            {"indexed": False, "internalType": "bytes32", "name": "jobSpecHash", "type": "bytes32"},
        ],
        "name": "JobCreated",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "funder", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "escrowBalance", "type": "uint256"},
        ],
        "name": "JobFunded",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "escrowBalance", "type": "uint256"},
        ],
        "name": "JobFullyFunded",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "attestor", "type": "address"},
            {"indexed": False, "internalType": "bytes32", "name": "attestationHash", "type": "bytes32"},
        ],
        "name": "AttestationSubmitted",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "finalizer", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "providerPayout", "type": "uint256"},
            {"indexed": False, "internalType": "uint256", "name": "requesterRefund", "type": "uint256"},
            {"indexed": False, "internalType": "bytes32", "name": "settlementHash", "type": "bytes32"},
        ],
        "name": "JobFinalized",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "recipient", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "PayoutWithdrawn",
        "type": "event",
    },
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "internalType": "uint256", "name": "jobId", "type": "uint256"},
            {"indexed": True, "internalType": "address", "name": "recipient", "type": "address"},
            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
        ],
        "name": "RefundWithdrawn",
        "type": "event",
    },
]
