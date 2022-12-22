import torch
import torch.nn as nn
import torch.nn.functional as F


class BasicBlock2(nn.Module):
    def __init__(self, in_planes, out_planes, stride=1):
        super(BasicBlock2, self).__init__()

        self.bn1 = nn.BatchNorm2d(in_planes)
        self.conv1 = nn.Conv2d(in_planes, out_planes,
                               kernel_size=3, stride=1, padding=1, bias=False)
        self.bn2 = nn.BatchNorm2d(out_planes)
        self.conv2 = nn.Conv2d(out_planes, out_planes,
                               kernel_size=3, stride=1, padding=1, bias=False)

    def foward(self, x):
        residual = x
        x = F.leaky_relu(self.bn1)
        x = F.leaky_relu(self.bn2(self.conv1(x)))
        x = self.conv2(x)
        return x + residual


class PuyoResNet(nn.Module):
    def __init__(self, layers):
        super(PuyoResNet, self).__init__()

        channel = 128

        # first layer. channel: 21 -> channel
        self.fi_conv = nn.Conv2d(
            21, channel, kernel_size=3, stride=1, padding=1)
        self.fi_bn = nn.BatchNorm2d(channel, layers)

        # resnet blocks
        self.blocks = self._make_layer(channel, layers)

        # For PolicyNet
        self.policy_conv = nn.Conv2d(channel, 256, kernel_size=1)
        self.policy_bn = nn.BatchNorm2d(256)
        self.policy_fc = nn.Linear(256*14*6, 22)

        # For ValueNet
        self.value_conv = nn.Conv2d(channel, channel, kernel_size=1, padding=0)
        self.value_bn = nn.BatchNorm2d(channel)
        self.value_fc1 = nn.Linear(channel*14*6, 256)
        self.value_bn1 = nn.BatchNorm1d(256)
        self.value_fc2 = nn.Linear(256, 1)

        for m in self.modules():
            if isinstance(m, nn.Conv2d):
                nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)


    def _make_layer(self, planes, blocks):
        layers = []
        for i in range(blocks):
            layers.append(BasicBlock2(planes, planes))

        return nn.Sequential(*layers)
    
    def forward(self, x):
        # for full pre-activation, choose this
        x = self.fi_conv(x)
        x = self.blocks(x)
        x = F.leaky_relu(self.fi_bn(x))

        # policy head
        p = x
        p = F.leaky_relu(self.policy_bn(self.policy_conv(p)))
        p = p.view(p.size(0), -1)
        p = self.policy_fc(p)

        # value head
        q = x
        q = F.leaky_relu(self.value_bn(self.value_conv(q)))
        q = q.view(q.size(0), -1)
        q = self.value_fc2(q)

        return p, q

    def define():
        return PuyoResNet(5)
