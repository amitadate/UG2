import torch
from torch.autograd import Variable
from torch.utils.data import Dataset, DataLoader
import torchvision.models as models
import torch.nn as nn
import numpy as np


def feat_ext():
	vgg16 = models.vgg16(pretrained=True).cuda()
	for param in vgg16.parameters():
		# print param.shape
		param.requires_grad = False

	# label_bat = Variable(torch.randn(64, 3, 200,200)).cuda()
	# print vgg16
	model = torch.nn.Sequential(*(vgg16.features[i] for i in range(9)))
	# print model(label_bat)[0,0,0,0]
	return model

def vgg16_classifier():
	vgg16 = models.vgg16(pretrained=True).cuda()
	for param in vgg16.parameters():
		# print param.shape
		param.requires_grad = False

	return vgg16

class Classifier(nn.Module):
	def __init__(self, classifier, size, mapping_list = None):
		super(Classifier, self).__init__()

		self.ups = nn.Upsample(size = size, mode = 'bilinear')
		self.classifier = classifier
		self.softmax = nn.Softmax(dim = 0)


	def forward(self, x):
		out = self.ups(x)
		out = self.classifier(out)
		out = self.softmax(out)

		if mapping_list is not None:
			mapped_output = []

			for i in range(len(mapping_list)):
				mapped_output.append(torch.sum(torch.index_select(out, 0, mapping_list[i])))

			out = torch.stack(mapped_output)

		return out

class ResBlock(nn.Module):
	def __init__(self,in_channels, out_channels, stride):
		super(ResBlock, self).__init__()
		self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size = 3, stride = stride, padding = 1, bias = False)
		self.bn1 = nn.BatchNorm2d(out_channels)
		self.relu1 = nn.ReLU(inplace = True)
		self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size = 3, stride = stride, padding = 1, bias = False)
		self.bn2 = nn.BatchNorm2d(out_channels)

	def forward(self, x):
		residual = x
		out = self.conv1(residual)
		out = self.bn1(out)
		out = self.relu1(out)
		out = self.conv2(out)
		out = self.bn2(out)

		out += x
		return out

class UpsBlock(nn.Module):
	def __init__(self, h_channel, scale_factor = None, size = None):
		super(UpsBlock, self).__init__()
		if size is None:
			self.ups = nn.Upsample(scale_factor = scale_factor, mode = 'bilinear')
		else:
			self.ups = nn.Upsample(size = size, mode = 'bilinear')

		self.conv = nn.Conv2d(h_channel, h_channel, kernel_size = 3, stride = 1, padding = 1, bias = False)
		self.bn = nn.BatchNorm2d(h_channel)
		self.relu = nn.ReLU(inplace = True)

	def forward(self, x):
		out = self.ups(x)
		out = self.conv(out)
		out = self.bn(out)
		out = self.relu(out)

		return out

class ConvBlock(nn.Module):
	def __init__(self, in_channel, out_channel):
		super(ConvBlock, self).__init__()

		self.conv = nn.Conv2d(in_channel, out_channel, kernel_size = 3, stride = 1, padding = 1, bias = False)
		self.bn = nn.BatchNorm2d(out_channel)
		self.relu = nn.ReLU(inplace = True)

	def forward(self, x):
		out = self.conv(x)
		out = self.bn(out)
		out = self.relu(out)

		return out


class SRNet(nn.Module):
	def __init__(self, h_channel = 64, num_resblock = 4):
		super(SRNet, self).__init__()

		self.conv1 = nn.Conv2d(3, h_channel, kernel_size = 9, stride = 1, padding = 4, bias = False)
		self.bn1 = nn.BatchNorm2d(h_channel)
		self.relu1 = nn.ReLU(inplace = True)

		self.res_blocks = []

		for i in range(num_resblock):
			self.res_blocks.append(ResBlock(h_channel,h_channel,1))

		self.conv3 = ConvBlock(h_channel, h_channel)

		self.conv4 = nn.Conv2d(h_channel, 3, kernel_size = 9, stride = 1, padding = 4, bias = False)
		self.bn4 = nn.BatchNorm2d(3)

	def forward(self,x):
		out = self.conv1(x)
		out = self.bn1(out)
		out = self.relu1(out)

		for res_block in self.res_blocks:
			out = res_block(out)

		out = self.conv3(out)

		out = self.conv4(out)
		out = self.bn4(out)

		return out




