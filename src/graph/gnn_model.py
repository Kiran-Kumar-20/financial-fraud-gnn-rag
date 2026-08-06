import torch
import torch.nn as nn
from torch_geometric.nn import GCNConv

class FraudGNN(torch.nn.Module):
    def __init__(self, in_channels=3, hidden_channels=16, out_channels=1):
        super(FraudGNN, self).__init__()
        self.conv1 = GCNConv(in_channels, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.fc = nn.Linear(hidden_channels, out_channels)
        self.sigmoid = nn.Sigmoid()

    def forward(self, data):
        x, edge_index = data.x, data.edge_index

        x = self.conv1(x, edge_index)
        x = torch.relu(x)
        x = self.conv2(x, edge_index)
        x = torch.relu(x)
        
        # We assume the first node is the transaction node
        x = self.fc(x[0])
        x = self.sigmoid(x)
        return x
