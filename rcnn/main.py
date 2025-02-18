import argparse
import torch
import torchtext.data as data
from torchtext.vocab import Vectors
import model,train
import os
from os.path import dirname,join as join_path
path_root = dirname(__file__)
import sys
from dataset import *

parser = argparse.ArgumentParser(description='TextCNN text classifier')
# learning
parser.add_argument('-lr',type=float,default=1e-3,help='initial learning rate [default:0.001]')
parser.add_argument('-epochs',type=int,default=256,help='number of epochs for train [default:256]')
parser.add_argument('-batch-size',type=int,default=128,help='batch size for training [default:128]')
parser.add_argument('-hidden-size',type=int,default=2,help='hidden size [default:2]')
parser.add_argument('-log-interval',type=int,default=100,help='how many steps to wait before logging training status [default:1]')
parser.add_argument('-test-interval',type=int,default=100,help='how many steps to wait before testing [default:100]')
parser.add_argument('-save-dir',type=str,default='snapshot',help='where to save the snapshot')
parser.add_argument('-early-stopping',type=int,default=1000,help='iteration numbers to stop without performance increasing')
parser.add_argument('-save-best', type=bool, default=True, help='whether to save when get best performance')

# model
parser.add_argument('-dropout',type=float,default=0.5,help='the probability for dropout [default:0.5]')
parser.add_argument('-embedding-dimension',type=int,default=128,help='number of embedding dimension [default:128]')
parser.add_argument('-static',type=bool,default=False,help='whether to use static pre-trained word vectors')
parser.add_argument('-non-static',type=bool,default=False,help='whether to fine-tune static pre-trained word vectors')
parser.add_argument('-pretrained-name',type=str,default='sgns.zhihu.word',help='filename of pre-trained word vectors')
parser.add_argument('-pretrained-path', type=str, default='pretrained', help='path of pre-trained word vectors')
parser.add_argument('-multichannel',type=bool,default=False,help='whether to use 2 channel of word vectors')

#device
parser.add_argument('-device',type=int,default=-1,help='device to use for iterable data,-1 mean cpu [default:-1]')

#option
parser.add_argument('-snapshot', type=str, default=None, help='filename of model snapshot [default: None]')
args = parser.parse_args()

def load_word_vectors(model_name,model_path):
    vectors= Vectors(name=model_name,cache=model_path)
    return vectors

def load_dataset(text_field,label_field,args,**kwargs):
    train_dataset,dev_dataset,test_dataset = get_dataset(join_path(dirname(path_root),'data'),text_field,label_field)
    if args.static and args.pretrained_name and args.pretrained_path:
        vectors = load_word_vectors(args.pretrained_name,args.pretrained_path)
        text_field.build_vocab(train_dataset,dev_dataset,vectors=vectors)
    else:
        text_field.build_vocab(train_dataset,dev_dataset)
    label_field.build_vocab(train_dataset,dev_dataset)
    train_iter,dev_iter = data.Iterator.splits(
        (train_dataset,dev_dataset),
        batch_sizes = (args.batch_size,args.batch_size),
        sort_key = lambda x:len(x.text),
        **kwargs
    )
    return train_iter,dev_iter

print('Loading data...')
text_field = data.Field(lower=True)
label_field = data.Field(sequential=False)
train_iter, dev_iter = load_dataset(text_field, label_field, args, device=-1, repeat=False, shuffle=True)

args.vocabulary_size = len(text_field.vocab)
if args.static:
    args.embedding_dimension = text_field.vocab.vectors.size()[-1]
    args.vectors = text_field.vocab.vectors

if args.multichannel:
    args.static = True
    args.non_static = True

args.class_num = len(label_field.vocab)
args.cuda = args.device != -1 or torch.cuda.is_available()

print('Parameters:')
for attr,value in sorted(args.__dict__.items()):
    if attr in {'vectors'}:
        continue
    print('\t{}={}'.format(attr.upper(),value))

text_rcnn = model.TextRCNN(args)
if args.snapshot:
    print('\nLoading model from {}...\n'.format(args.snapshot))
    text_rcnn.load_state_dict(torch.load(args.snapshot))

if args.cuda:
    torch.cuda.set_device(args.device)
    text_rcnn = text_rcnn.cuda()
try:
    train.train(train_iter,dev_iter,text_rcnn,args)
except KeyboardInterrupt:
    print('Existing from training early')