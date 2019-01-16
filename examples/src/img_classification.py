from neural_pipeline.data_producer import DataProducer, AbstractDataset
from neural_pipeline.train_config import TrainConfig, TrainStage, ValidationStage
from neural_pipeline import Trainer
from neural_pipeline.utils.file_structure_manager import FileStructManager

import torch
from torch import nn
import torch.nn.functional as F
from torchvision import datasets, transforms


class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = nn.Conv2d(1, 20, 5, 1)
        self.conv2 = nn.Conv2d(20, 50, 5, 1)
        self.fc1 = nn.Linear(4 * 4 * 50, 500)
        self.fc2 = nn.Linear(500, 10)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.max_pool2d(x, 2, 2)
        x = F.relu(self.conv2(x))
        x = F.max_pool2d(x, 2, 2)
        x = x.view(-1, 4 * 4 * 50)
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return F.log_softmax(x, dim=1)


class NLLLoss(torch.nn.Module):
    def forward(self, output: torch.Tensor, target: torch.Tensor):
        return F.nll_loss(output, target)


class MNISTDataset(AbstractDataset):
    transforms = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])

    def __init__(self, data_dir: str, is_train: bool):
        self.dataset = datasets.MNIST(data_dir, train=is_train, download=True)

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, item):
        data, target = self.dataset[item]
        return {'data': self.transforms(data), 'target': target}


if __name__ == '__main__':
    checkpoints_dir, logdir = 'data/checkpoints', 'data/logs'

    fsm = FileStructManager(checkpoint_dir_path=checkpoints_dir, logdir_path=logdir, prefix=None)
    model = Net()

    train_dataset = DataProducer([MNISTDataset('data/dataset', True)], batch_size=4, num_workers=2)
    validation_dataset = DataProducer([MNISTDataset('data/dataset', False)], batch_size=4, num_workers=2)

    train_config = TrainConfig([TrainStage(train_dataset), ValidationStage(validation_dataset)], NLLLoss(),
                               torch.optim.SGD(model.parameters(), lr=1e-4, momentum=0.5), 'train_mnist')

    Trainer(model, train_config, fsm, is_cuda=True).set_epoch_num(50).train()
