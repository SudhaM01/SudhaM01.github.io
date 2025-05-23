
## Requirements
#!pip3 install torch numpy matplotlib

from __future__ import unicode_literals, print_function, division
from io import open
import unicodedata
import string
import re
import random

import torch
import torch.nn as nn
from torch import optim
import torch.nn.functional as F



device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

from google.colab import drive
drive.mount('/content/drive')
file_path = "/content/drive/MyDrive"

import torch
torch.cuda.is_available()

"""We need a unique index per word to use as the inputs and targets of the networks later. To keep track of all this we will use a helper class called Lang which has word → index (word2index) and index → word (index2word) dictionaries, as well as a count of each word word2count which will be used to replace rare words later."""

SOS_token = 0;
EOS_token = 1;


class Lang:
    def __init__(self, name):
        self.name = name
        self.word2index = {}
        self.word2count = {}
        self.index2word = {0: "SOS", 1: "EOS"}
        self.n_words = 2  # Count SOS and EOS

    def addSentence(self, sentence):
        for word in sentence.split(' '):
            self.addWord(word)

    def addWord(self, word):
        if word not in self.word2index:
            self.word2index[word] = self.n_words
            self.word2count[word] = 1
            self.index2word[self.n_words] = word
            self.n_words += 1
        else:
            self.word2count[word] += 1

#coverting unicode to ascii to simplify and the trim the punctuation and change everything to lower case
def unicodeToAscii(s):
    return ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

# Lowercase, trim, and remove non-letter characters


def normalizeString(s):
    s = unicodeToAscii(s.lower().strip())
    s = re.sub(r"([.!?])", r" \1", s)
    s = re.sub(r"[^a-zA-Z.!?]+", r" ", s)
    return s

"""the file is split into lines to read the data file and then split into pairs"""

import pandas as pd
def readCSV(csv_file):
    print("Reading CSV file...")
    # Read the CSV file
    df = pd.read_csv(csv_file)

    # Extract Ingredients and Recipe columns
    ingredients = df['Ingredients'].tolist()
    recipes = df['Recipe'].tolist()

    return ingredients, recipes



def readLangs(Ingredients, Recipe, reverse=False):
    print("Reading lines...")
    Lines = readCSV('your_csv_file.csv').strip().split('\n')
    # Read the file and split into lines
    # file_name = file_path + '/train.csv'
    # lines = open(file_name, encoding='utf-8').\
    #     read().strip().split('\n')

    # Split every line into pairs and normalize
    pairs = [[normalizeString(s) for s in l.split('\t')] for l in lines]


    # Reverse pairs, make Lang instances
    if reverse:
        pairs = [list(reversed(p)) for p in pairs]
        input_ingredients = Lang(Ingredients)
        output_recipe = Lang(Recipe)
    else:
        input_ingredients = Lang(Ingredients)
        output_recipe = Lang(Recipe)

    return input_ingredients, output_recipe, pairs

"""Since there are a lot of example sentences and we want to train something quickly, we’ll trim the data set to only relatively short and simple sentences. Here, the maximum length is 10 words (that includes ending punctuation) and the filter considers sentences that translate to the form “I am” or “He is” etc. (accounting for apostrophes replaced earlier)."""

MAX_LENGTH = 150

def filterPair(p):
    return len(p[0].split(' ')) < MAX_LENGTH and \
        len(p[1].split(' ')) < MAX_LENGTH \


def filterPairs(pairs):
    return [pair for pair in pairs if filterPair(pair)]

"""The full process for preparing the data is:

- Read text file and split into lines, split lines into pairs
- Normalize text, filter by length and content
- Make word lists from sentences in pairs

"""

def prepareData(Ingredients, Recipe, reverse=False):
    pairs = [(str(ing),str(rec)) for ing,rec in zip(ingredients, recipes)]
    print("Read %s sentence pairs" % len(pairs))
    pairs = filterPairs(pairs)
    print("Trimmed to %s sentence pairs" % len(pairs))
    input_ingredients= Lang('Ingredients')
    output_recipe=Lang('Recipe')
    print("Counting words...")
    for pair in pairs:
        input_ingredients.addSentence(pair[0])
        output_recipe.addSentence(pair[1])
    print("Counted words:")
    print(input_ingredients.name, input_ingredients.n_words)
    print(output_recipe.name, output_recipe.n_words)
    return input_ingredients, output_recipe, pairs

ingredients, recipes= readCSV('/content/drive/MyDrive/train.csv')
input_ingredients, output_recipe, pairs = prepareData(ingredients, recipes , True)
test_ingredients, test_recipes= readCSV('/content/drive/MyDrive/test.csv')
input_test_ingredients, output_test_recipe, test_pairs = prepareData(test_ingredients, test_recipes , True)
val_ingredients, val_recipes= readCSV('/content/drive/MyDrive/dev.csv')
input_val_ingredients, output_val_recipe, val_pairs = prepareData(val_ingredients, val_recipes , True)
print(random.choice(pairs))
print(random.choice(test_pairs))
print(random.choice(val_pairs))

"""###Implementation of Baseline 1
Seq2Seq model

The encoder
"""

class EncoderRNN(nn.Module):
    def __init__(self, input_size, hidden_size):
        super(EncoderRNN, self).__init__()
        self.hidden_size = hidden_size

        self.embedding = nn.Embedding(input_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size)

    def forward(self, input, hidden):
        embedded = self.embedding(input).view(1, 1, -1)
        output = embedded
        output, hidden = self.lstm(output, hidden)
        return output, hidden

    def initHidden(self):
        return (torch.zeros(1, 1, self.hidden_size, device=device),torch.zeros(1, 1, self.hidden_size, device=device))

"""The decoder"""

class DecoderRNN(nn.Module):
    def __init__(self, hidden_size, output_size):
        super(DecoderRNN, self).__init__()
        self.hidden_size = hidden_size

        self.embedding = nn.Embedding(output_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size)
        self.out = nn.Linear(hidden_size, output_size)
        self.softmax = nn.LogSoftmax(dim=1)

    def forward(self, input, hidden):
        output = self.embedding(input).view(1, 1, -1)
        output = F.relu(output)
        output, hidden = self.lstm(output, hidden)
        output = self.softmax(self.out(output[0]))
        return output, hidden

    def initHidden(self):
        return (torch.zeros(1, 1, self.hidden_size, device=device),torch.zeros(1, 1, self.hidden_size, device=device))

"""Preparing training data and training the model"""

def indexesFromSentence(lang, sentence):
    return [lang.word2index[word] for word in sentence.split(' ')]


def tensorFromSentence(lang, sentence):
    indexes = indexesFromSentence(lang, sentence)
    indexes.append(EOS_token)
    return torch.tensor(indexes, dtype=torch.long, device=device).view(-1, 1)


def tensorsFromPair(pair):
    input_tensor = tensorFromSentence(input_ingredients, pair[0])
    target_tensor = tensorFromSentence(output_recipe, pair[1])
    return (input_tensor, target_tensor)

teacher_forcing_ratio = 1


def train(input_tensor, target_tensor, encoder, decoder, encoder_optimizer, decoder_optimizer, criterion, max_length=MAX_LENGTH):
    encoder_hidden = encoder.initHidden()

    encoder_optimizer.zero_grad()
    decoder_optimizer.zero_grad()

    input_length = input_tensor.size(0)
    target_length = target_tensor.size(0)

    encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)

    loss = 0

    for ei in range(input_length):
        encoder_output, encoder_hidden = encoder(
            input_tensor[ei], encoder_hidden)
        encoder_outputs[ei] = encoder_output[0, 0]

    decoder_input = torch.tensor([[SOS_token]], device=device)

    decoder_hidden = encoder_hidden

    use_teacher_forcing = True if random.random() < teacher_forcing_ratio else False

    if use_teacher_forcing:
        # Teacher forcing: Feed the target as the next input
        for di in range(target_length):
            decoder_output, decoder_hidden = decoder(
                decoder_input, decoder_hidden)
            loss += criterion(decoder_output, target_tensor[di])
            decoder_input = target_tensor[di]  # Teacher forcing

    else:
        # Without teacher forcing: use its own predictions as the next input
        for di in range(target_length):
            decoder_output, decoder_hidden = decoder(
                decoder_input, decoder_hidden)
            topv, topi = decoder_output.topk(1)
            decoder_input = topi.squeeze().detach()  # detach from history as input

            loss += criterion(decoder_output, target_tensor[di])
            if decoder_input.item() == EOS_token:
                break

    loss.backward()

    encoder_optimizer.step()
    decoder_optimizer.step()

    return loss.item() / target_length

def validation(input_tensor, target_tensor,encoder, decoder, criterion, max_length=MAX_LENGTH):

    with torch.no_grad():
            encoder_hidden = encoder.initHidden()
            input_length = input_tensor.size(0)
            target_length = target_tensor.size(0)

            encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)

            loss = 0

            for ei in range(input_length):
                encoder_output, encoder_hidden = encoder(input_tensor[ei], encoder_hidden)
                encoder_outputs[ei] = encoder_output[0, 0]

            decoder_input = torch.tensor([[SOS_token]], device=device)
            decoder_hidden = encoder_hidden

            for di in range(target_length):
                decoder_output, decoder_hidden = decoder(decoder_input, decoder_hidden)
                topv, topi = decoder_output.topk(1)
                decoder_input = topi.squeeze().detach()

                loss += criterion(decoder_output, target_tensor[di])
                if decoder_input.item() == EOS_token:
                    break

            #total_loss += (loss.item() / target_length)

    # encoder.train()
    # decoder.train()

    return loss.item() / target_length

import time
import math


def asMinutes(s):
    m = math.floor(s / 60)
    s -= m * 60
    return '%dm %ds' % (m, s)


# def timeSince(since, percent):
#     now = time.time()
#     s = now - since
#     es = s / (percent)
#     rs = es/percent - s
#     return '%s (- %s)' % (asMinutes(s), asMinutes(rs))

def timeSince(since, percent):
    now = time.time()
    s = now - since
    es = s / (percent)
    rs = es - s
    return '%s (- %s)' % (asMinutes(s), asMinutes(rs))

def trainIters(encoder, decoder, n_iters, print_every=1000, save_every=1000, plot_every=1000, val_every=5000, learning_rate=0.01, validation_pairs=None, patience=3, val_subset_size=10000):
    start = time.time()
    train_losses = []
    val_losses = []
    print_loss_total = 0  # Reset every print_every
    plot_loss_total = 0  # Reset every plot_every
    best_loss = float('inf')
    no_improvement = 0
    checkpoints = []
    encoder_optimizer = optim.Adam(encoder.parameters(), lr=learning_rate)
    decoder_optimizer = optim.Adam(decoder.parameters(), lr=learning_rate)
    criterion = nn.NLLLoss()
    plot_losses=[]
    training_pairs = [tensorsFromPair(random.choice(pairs)) for i in range(n_iters)]
    if validation_pairs is not None:
        val_pairs = [tensorsFromPair(pair) for pair in random.sample(validation_pairs, min(val_subset_size,len(validation_pairs)))]
    # if validation_pairs is not None:
    #     val_pairs = [tensorsFromPair(random.choice(validation_pairs)) for i in range(len(validation_pairs))]

    for iter in range(1, n_iters + 1):
        training_pair = training_pairs[iter - 1]
        input_tensor = training_pair[0]
        target_tensor = training_pair[1]

        loss = train(input_tensor, target_tensor, encoder, decoder, encoder_optimizer, decoder_optimizer, criterion)
        print_loss_total += loss
        plot_loss_total += loss
        val_loss = 0
        if iter % print_every == 0:
            print_loss_avg = print_loss_total / print_every
            print_loss_total = 0
            train_losses.append(print_loss_avg)
            if validation_pairs is not None and iter % val_every == 0:
                encoder.eval()
                decoder.eval()

                #val_subset= random.sample(val_pairs, min(val_subset_size, len(val_pairs)))
                for val_pair in val_pairs:
                  val_input_tensor = val_pair[0]
                  val_target_tensor = val_pair[1]
                  val_loss += validation(val_input_tensor, val_target_tensor, encoder, decoder, criterion)
                val_loss /= len(val_pairs)
                val_losses.append(val_loss)
                encoder.train()
                decoder.train()
                print('%s (%d %d%%) Training Loss %.4f ; Validation Loss: %.4f' % (timeSince(start, iter / n_iters),
                                                                                  iter, iter / n_iters * 100, print_loss_avg, val_loss))
            else:
                print('%s (%d %d%%) Training Loss %.4f' % (timeSince(start, iter / n_iters),
                                                            iter, iter / n_iters * 100, print_loss_avg))


        if iter % plot_every == 0:
            plot_loss_avg = plot_loss_total / plot_every
            plot_losses.append(plot_loss_avg)
            plot_loss_total = 0

        if iter % save_every == 0:
            save_checkpoint(encoder, decoder, encoder_optimizer, decoder_optimizer, iter // save_every, train_losses, val_losses, '/content/drive/MyDrive/Colab Notebooks/checkpoint_50000.pt')

        if validation_pairs is not None and iter % val_every == 0:
            if val_loss < best_loss:
                best_loss = val_loss
                no_improvement = 0
            else:
                no_improvement += 1
                if no_improvement >= patience:
                    print("Early stopping after no improvement for %d iterations." % patience)
                    break

    return(train_losses, val_losses, val_every)

def save_checkpoint(encoder, decoder, encoder_optimizer, decoder_optimizer, epoch, train_losses, val_losses, filename):
    checkpoint = {
        'encoder_state_dict': encoder.state_dict(),
        'decoder_state_dict': decoder.state_dict(),
        'encoder_optimizer_state_dict': encoder_optimizer.state_dict(),
        'decoder_optimizer_state_dict': decoder_optimizer.state_dict(),
        'epoch': epoch,
        'train_losses': train_losses,
        'val_losses': val_losses
    }
    torch.save(checkpoint, filename)

def load_checkpoint(encoder, decoder, encoder_optimizer, decoder_optimizer, filename):
    checkpoint = torch.load(filename)
    encoder.load_state_dict(checkpoint['encoder_state_dict'])
    decoder.load_state_dict(checkpoint['decoder_state_dict'])
    encoder_optimizer.load_state_dict(checkpoint['encoder_optimizer_state_dict'])
    decoder_optimizer.load_state_dict(checkpoint['decoder_optimizer_state_dict'])
    epoch = checkpoint['epoch']
    train_losses = checkpoint['train_losses']
    val_losses = checkpoint['val_losses']
    return encoder, decoder, encoder_optimizer, decoder_optimizer, epoch, train_losses, val_losses

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

def showPlot(train_losses, val_losses,val_every, plot_every):
    plt.figure()
    loc = ticker.MultipleLocator(base=0.5)
    plt.gca().yaxis.set_major_locator(loc)
    train_epochs = range(plot_every, len(train_losses)*plot_every + 1,plot_every)
    val_epochs=range(val_every, val_every*len(val_losses)+1,val_every)
    plt.plot(train_epochs, train_losses, label='Training Loss')
    if val_losses:
        plt.plot(val_epochs, val_losses, label='Validation Loss')

    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.show()

def evaluate(encoder, decoder, sentence, max_length=MAX_LENGTH):
    with torch.no_grad():
        input_tensor = tensorFromSentence(input_ingredients, sentence)
        input_length = input_tensor.size()[0]
        encoder_hidden = encoder.initHidden()

        encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)

        for ei in range(input_length):
            encoder_output, encoder_hidden = encoder(input_tensor[ei],
                                                     encoder_hidden)
            encoder_outputs[ei] += encoder_output[0, 0]

        decoder_input = torch.tensor([[SOS_token]], device=device)  # SOS

        decoder_hidden = encoder_hidden

        decoded_words = []
        decoder_attentions = torch.zeros(max_length, max_length)

        for di in range(max_length):
            decoder_output, decoder_hidden = decoder(
                decoder_input, decoder_hidden)
            topv, topi = decoder_output.data.topk(1)
            if topi.item() == EOS_token:
                decoded_words.append('<EOS>')
                break
            else:
                decoded_words.append(output_recipe.index2word[topi.item()])

            decoder_input = topi.squeeze().detach()

        return decoded_words

def evaluateRandomly(encoder, decoder, n=10, save_path=None):
    generated_recipes=[]
    test_recipes=[]
    for i in range(n):
        pair = random.choice(test_pairs)
        print('>', pair[0])
        print('=', pair[1])#reference recipe
        output_words= evaluate(encoder, decoder, pair[0])
        output_sentence = ' '.join(output_words)
        print('<', output_sentence) #generated recipe
        generated_recipes.append(output_sentence)
        test_recipes.append(pair[1])
        print('')
        if save_path:
          data={'Test recipe':test_recipes, 'Generated recipe':generated_recipes}
          df=pd.DataFrame(data)
          df.to_csv(save_path,index=False)

hidden_size = 256
encoder1 = EncoderRNN(input_ingredients.n_words, hidden_size).to(device)
decoder1 = DecoderRNN(hidden_size, output_recipe.n_words).to(device)

train_losses, val_losses, val_every=trainIters(encoder1, decoder1, 50000, print_every=1000,validation_pairs=val_pairs, patience=3)

hidden_size=256
checkpoint_path = '/content/drive/MyDrive/Colab Notebooks/checkpoint_50000.pt'
encoder1 = EncoderRNN(input_ingredients.n_words, hidden_size).to(device)
decoder1 = DecoderRNN(hidden_size, output_recipe.n_words).to(device)
encoder_optimizer = optim.Adam(encoder1.parameters(), lr=0.01)
decoder_optimizer = optim.Adam(decoder1.parameters(), lr=0.01)


encoder, decoder, encoder_optimizer, decoder_optimizer, epoch, train_losses, val_losses = load_checkpoint(
    encoder1, decoder1, encoder_optimizer, decoder_optimizer, checkpoint_path
)

evaluateRandomly(encoder1, decoder1, save_path='/content/drive/MyDrive/gen_vs_test_seq2seq.csv')

model_save_de= "decoder.pt"
path= f"/content/drive/MyDrive/{model_save_de}"
torch.save(decoder1.state_dict(),path)

model_save_de= "encoder.pt"
path= f"/content/drive/MyDrive/{model_save_de}"
torch.save(encoder1.state_dict(),path)

"""### Implementation of Baseline 2

Seq2Seq model with attention
"""

class AttnDecoderRNN(nn.Module):
    def __init__(self, hidden_size, output_size, dropout_p=0.1, max_length=MAX_LENGTH):
        super(AttnDecoderRNN, self).__init__()
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.dropout_p = dropout_p
        self.max_length = max_length

        self.embedding = nn.Embedding(self.output_size, self.hidden_size)
        # self.attn = nn.Linear(self.hidden_size * 2, self.max_length)
        # self.attn_combine = nn.Linear(self.hidden_size * 2, self.hidden_size)
        self.dropout = nn.Dropout(self.dropout_p)
        self.lstm = nn.LSTM(self.hidden_size, self.hidden_size)
        #self.out = nn.Linear(self.hidden_size, self.output_size)
        self.out = nn.Linear(self.hidden_size*2, self.output_size)

    def forward(self, input, hidden, encoder_outputs):
        embedded = self.embedding(input).view(1, 1, -1)
        embedded = self.dropout(embedded)

        # _, hidden = self.lstm(embedded, hidden)

        # attn_weights = F.softmax(torch.bmm(hidden[0], encoder_outputs.T.unsqueeze(0)),dim=-1)
        # attn_output = torch.bmm(attn_weights, encoder_outputs.unsqueeze(0))

        # concat_output = torch.cat((attn_output[0], hidden[0][0]), 1)
        lstm_output, hidden = self.lstm(embedded, hidden)

        # Calculate attention weights and apply to encoder outputs
        attn_weights = F.softmax(torch.bmm(lstm_output.transpose(0, 1), encoder_outputs.unsqueeze(0).transpose(1, 2)), dim=-1)
        attn_output = torch.bmm(attn_weights, encoder_outputs.unsqueeze(0))

        # Concatenate the attention output and the LSTM output
        concat_output = torch.cat((attn_output.squeeze(0), lstm_output.squeeze(0)), 1)

        output = F.log_softmax(self.out(concat_output), dim=1)


        return output, hidden, attn_weights

    def initHidden(self):
        return torch.zeros(1, 1, self.hidden_size, device=device)

teacher_forcing_ratio = 1


def train_attn(input_tensor, target_tensor, encoder, decoder, encoder_optimizer, decoder_optimizer, criterion, max_length=MAX_LENGTH):
    encoder_hidden = encoder.initHidden()

    encoder_optimizer.zero_grad()
    decoder_optimizer.zero_grad()

    input_length = input_tensor.size(0)
    target_length = target_tensor.size(0)

    encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)

    loss = 0

    for ei in range(input_length):
        encoder_output, encoder_hidden = encoder(
            input_tensor[ei], encoder_hidden)
        encoder_outputs[ei] = encoder_output[0, 0]

    decoder_input = torch.tensor([[SOS_token]], device=device)

    decoder_hidden = encoder_hidden

    use_teacher_forcing = True if random.random() < teacher_forcing_ratio else False

    if use_teacher_forcing:
        # Teacher forcing: Feed the target as the next input
        for di in range(target_length):
            decoder_output, decoder_hidden, decoder_attention = decoder(
                decoder_input, decoder_hidden, encoder_outputs)
            loss += criterion(decoder_output, target_tensor[di])
            decoder_input = target_tensor[di]  # Teacher forcing

    else:
        # Without teacher forcing: use its own predictions as the next input
        for di in range(target_length):
            decoder_output, decoder_hidden, decoder_attention = decoder(
                decoder_input, decoder_hidden, encoder_outputs)
            topv, topi = decoder_output.topk(1)
            decoder_input = topi.squeeze().detach()  # detach from history as input

            loss += criterion(decoder_output, target_tensor[di])
            if decoder_input.item() == EOS_token:
                break

    loss.backward()

    encoder_optimizer.step()
    decoder_optimizer.step()

    return loss.item() / target_length

def evaluate_attn(encoder, decoder, sentence, max_length=MAX_LENGTH):
    with torch.no_grad():
        input_tensor = tensorFromSentence(input_ingredients, sentence)
        input_length = input_tensor.size()[0]
        encoder_hidden = encoder.initHidden()

        encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)

        for ei in range(input_length):
            encoder_output, encoder_hidden = encoder(input_tensor[ei],
                                                     encoder_hidden)
            encoder_outputs[ei] += encoder_output[0, 0]

        decoder_input = torch.tensor([[SOS_token]], device=device)  # SOS

        decoder_hidden = encoder_hidden

        decoded_words = []
        decoder_attentions = torch.zeros(max_length, max_length)

        for di in range(max_length):
            decoder_output, decoder_hidden, decoder_attention = decoder(
                decoder_input, decoder_hidden, encoder_outputs)
            decoder_attentions[di] = decoder_attention.data
            topv, topi = decoder_output.data.topk(1)
            if topi.item() == EOS_token:
                decoded_words.append('<EOS>')
                break
            else:
                decoded_words.append(output_recipe.index2word[topi.item()])

            decoder_input = topi.squeeze().detach()

        return decoded_words, decoder_attentions[:di + 1]

def validation_attn(input_tensor, target_tensor, encoder, decoder, criterion, max_length=MAX_LENGTH):
    with torch.no_grad():
        encoder_hidden = encoder.initHidden()

        input_length = input_tensor.size(0)
        target_length = target_tensor.size(0)

        encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)

        loss = 0

        # Encode the input sequence
        for ei in range(input_length):
            encoder_output, encoder_hidden = encoder(input_tensor[ei], encoder_hidden)
            encoder_outputs[ei] = encoder_output[0, 0]

        decoder_input = torch.tensor([[SOS_token]], device=device)
        decoder_hidden = encoder_hidden

        # Attention mechanism
        decoder_attentions = torch.zeros(max_length, max_length)

        # Decode with attention
        for di in range(target_length):
            decoder_output, decoder_hidden, decoder_attention = decoder(
                decoder_input, decoder_hidden, encoder_outputs)
            decoder_attentions[di] = decoder_attention.data

            topv, topi = decoder_output.topk(1)
            decoder_input = topi.squeeze().detach()

            loss += criterion(decoder_output, target_tensor[di])
            if decoder_input.item() == EOS_token:
                break

    return loss.item() / target_length

def evaluateRandomly_attn(encoder, decoder, n=10, save_path=None):
    generated_recipes=[]
    test_recipes=[]
    for i in range(n):
        pair = random.choice(test_pairs)
        print('>', pair[0])
        print('=', pair[1])
        output_words, attention= evaluate_attn(encoder, decoder, pair[0])
        output_sentence = ' '.join(output_words)
        print('<', output_sentence)
        generated_recipes.append(output_sentence)
        test_recipes.append(pair[1])
        print('')

        if save_path:
          data={'Test recipe':test_recipes, 'Generated recipe':generated_recipes}
          df=pd.DataFrame(data)
          df.to_csv(save_path,index=False)

def trainIters_attn(encoder, decoder, n_iters, print_every=1000, save_every=1000, plot_every=1000, val_every=5000, learning_rate=0.01, validation_pairs=None, patience=3, val_subset_size=10000, file_path=file_path):
    start = time.time()
    train_losses = []
    val_losses = []
    print_loss_total = 0  # Reset every print_every
    plot_loss_total = 0  # Reset every plot_every
    best_loss = float('inf')
    no_improvement = 0
    checkpoints = []
    encoder_optimizer = optim.Adam(encoder.parameters(), lr=learning_rate)
    decoder_optimizer = optim.Adam(decoder.parameters(), lr=learning_rate)
    criterion = nn.NLLLoss()
    plot_losses=[]
    training_pairs = [tensorsFromPair(random.choice(pairs)) for i in range(n_iters)]
    if validation_pairs is not None:
        val_pairs = [tensorsFromPair(pair) for pair in random.sample(validation_pairs, min(val_subset_size,len(validation_pairs)))]
        #val_pairs=random.sample(validation_pair, min(val_subset_size,len(validation_pair)))
    for iter in range(1, n_iters + 1):
        training_pair = training_pairs[iter - 1]
        input_tensor = training_pair[0]
        target_tensor = training_pair[1]

        loss = train_attn(input_tensor, target_tensor, encoder, decoder, encoder_optimizer, decoder_optimizer, criterion)
        print_loss_total += loss
        plot_loss_total += loss
        val_loss = 0
        if iter % print_every == 0:
            print_loss_avg = print_loss_total / print_every
            print_loss_total = 0
            train_losses.append(print_loss_avg)
            if validation_pairs is not None and iter % val_every == 0:
                encoder.eval()
                decoder.eval()

                #val_subset= random.sample(val_pairs, min(val_subset_size, len(val_pairs)))
                for val_pair in val_pairs:
                  val_input_tensor = val_pair[0]
                  val_target_tensor = val_pair[1]
                  val_loss += validation_attn(val_input_tensor, val_target_tensor, encoder, decoder, criterion)
                val_loss /= len(val_pairs)
                val_losses.append(val_loss)
                encoder.train()
                decoder.train()
                print('%s (%d %d%%) Training Loss %.4f ; Validation Loss: %.4f' % (timeSince(start, iter / n_iters),
                                                                                  iter, iter / n_iters * 100, print_loss_avg, val_loss))
            else:
                print('%s (%d %d%%) Training Loss %.4f' % (timeSince(start, iter / n_iters),
                                                            iter, iter / n_iters * 100, print_loss_avg))


        if iter % plot_every == 0:
            plot_loss_avg = plot_loss_total / plot_every
            plot_losses.append(plot_loss_avg)
            plot_loss_total = 0

        if validation_pairs is not None and iter % val_every == 0:
            if val_loss < best_loss:
                best_loss = val_loss
                no_improvement = 0
            else:
                no_improvement += 1
                if no_improvement >= patience:
                    print("Early stopping after no improvement for %d iterations." % patience)
                    break

        if iter % save_every == 0:
            save_checkpoint(encoder, decoder, encoder_optimizer, decoder_optimizer, iter // save_every, train_losses, val_losses, file_path)



    return(train_losses, val_losses, val_every)

hidden_size = 256
encoder = EncoderRNN(input_ingredients.n_words, hidden_size).to(device)
attn_decoder = AttnDecoderRNN(hidden_size, output_recipe.n_words, dropout_p=0.1).to(device)
file_path= '/content/drive/MyDrive/Colab Notebooks/checkpoint_attn_new.pt'
train_losses_attn, val_losses_attn, val_every=trainIters_attn(encoder, attn_decoder, 50000, print_every=1000, validation_pairs=val_pairs, patience=3, file_path=file_path)

model_save_en= "encoder_attn.pt"
path= f"/content/drive/MyDrive/{model_save_en}"
torch.save(encoder.state_dict(),path)

model_save_de= "decoder_attn.pt"
path= f"/content/drive/MyDrive/{model_save_de}"
torch.save(attn_decoder.state_dict(),path)

evaluateRandomly_attn(encoder, attn_decoder, save_path='gen_vs_test_seq2seq_withattn.csv')

"""##Implementation of Extention 1
 ( layering encoders and decoders)
"""

class EncoderRNN_layers(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers=1):
        super(EncoderRNN_layers, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.embedding = nn.Embedding(input_size, hidden_size)
        self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers=num_layers)

    def forward(self, input, hidden):
        embedded = self.embedding(input).view(1, 1, -1)
        output, hidden = self.lstm(embedded, hidden)
        return output, hidden

    def initHidden(self):
        return (torch.zeros(self.num_layers, 1, self.hidden_size, device=device),
                torch.zeros(self.num_layers, 1, self.hidden_size, device=device))

import torch
import torch.nn as nn
import torch.nn.functional as F

class AttnDecoderRNN_layers(nn.Module):
    def __init__(self, hidden_size, output_size, num_layers=1, dropout_p=0.1, max_length=MAX_LENGTH):
        super(AttnDecoderRNN_layers, self).__init__()
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.num_layers = num_layers
        self.dropout_p = dropout_p
        self.max_length = max_length

        self.embedding = nn.Embedding(self.output_size, self.hidden_size)
        self.attn = nn.Linear(self.hidden_size * 2, self.max_length)
        self.attn_combine = nn.Linear(self.hidden_size * 2, self.hidden_size)
        self.dropout = nn.Dropout(self.dropout_p)
        self.lstm = nn.LSTM(self.hidden_size, self.hidden_size, num_layers=self.num_layers)
        self.out = nn.Linear(self.hidden_size, self.output_size)

    def forward(self, input, hidden, encoder_outputs):
        embedded = self.embedding(input).view(1, 1, -1)
        embedded = self.dropout(embedded)

        output, hidden = self.lstm(embedded, hidden)

        attn_weights = F.softmax(self.attn(torch.cat((output[0], hidden[0][-1]), 1)), dim=1)
        attn_applied = torch.bmm(attn_weights.unsqueeze(0), encoder_outputs.unsqueeze(0))

        output = torch.cat((output[0], attn_applied[0]), 1)
        output = self.attn_combine(output).unsqueeze(0)

        output = F.relu(output)
        output = F.log_softmax(self.out(output[0]), dim=1)
        return output, hidden, attn_weights

    def initHidden(self):
        return (torch.zeros(self.num_layers, 1, self.hidden_size, device=device),
                torch.zeros(self.num_layers, 1, self.hidden_size, device=device))

hidden_size = 256
num_layers=4
encoder = EncoderRNN_layers(input_ingredients.n_words, hidden_size,num_layers=num_layers).to(device)
attn_decoder = AttnDecoderRNN_layers(hidden_size, output_recipe.n_words, num_layers=num_layers,dropout_p=0.1).to(device)
file_path='/content/drive/MyDrive/Colab Notebooks/checkpoint_attn_layers.pt'
train_losses_attn, val_losses_attn, val_every=trainIters_attn(encoder, attn_decoder, 50000, print_every=1000, validation_pairs=val_pairs, patience=3,file_path=file_path)

# Your training loop or script
file_path = '/content/drive/MyDrive/Colab Notebooks/checkpoint_attn_layers.pt'



num_layers=4
checkpoint_path_layers = '/content/drive/MyDrive/Colab Notebooks/checkpoint_attn_layers.pt'
encoder_layers = EncoderRNN_layers(input_ingredients.n_words, hidden_size,num_layers=num_layers).to(device)
attn_decoder_layers = AttnDecoderRNN_layers(hidden_size, output_recipe.n_words, num_layers=num_layers,dropout_p=0.1).to(device)
encoder_optimizer_layers = optim.Adam(encoder_layers.parameters(), lr=0.01)
decoder_optimizer_layers = optim.Adam(attn_decoder_layers.parameters(), lr=0.01)

try:
    encoder_layers, decoder_layers, encoder_optimizer_layers, decoder_optimizer_layers, start_epoch, train_losses_layers, val_losses_layers = load_checkpoint(encoder_layers, attn_decoder_layers, encoder_optimizer_layers, decoder_optimizer_layers, checkpoint_path_layers)
    print(f"Loaded checkpoint from epoch {start_epoch}")
except FileNotFoundError:
    start_epoch = 0
    train_losses_attn = []
    val_losses_attn = []
    print("No checkpoint found, starting from scratch.")
# encoder_optimizer = optim.Adam(encoder1.parameters(), lr=0.01)
# decoder_optimizer = optim.Adam(decoder1.parameters(), lr=0.01)

# trainIters_attn(encoder, attn_decoder, num_iters=50000, start_epoch=start_epoch, print_every=1000, validation_pairs=val_pairs, patience=3, file_path=file_path)

# def save_checkpoint(encoder, decoder, encoder_optimizer, decoder_optimizer, epoch, train_losses, val_losses, filename):
#     checkpoint = {
#         'encoder_state_dict': encoder.state_dict(),
#         'decoder_state_dict': decoder.state_dict(),
#         'encoder_optimizer_state_dict': encoder_optimizer.state_dict(),
#         'decoder_optimizer_state_dict': decoder_optimizer.state_dict(),
#         'epoch': epoch,
#         'train_losses': train_losses,
#         'val_losses': val_losses
#     }
#     torch.save(checkpoint, filename)

evaluateRandomly_attn(encoder, attn_decoder, save_path='gen_vs_test_seq2seq_withattn_layers.csv')

"""##Implementation of Extention 2

Pretraining using Glove
"""

import pandas as pd
import numpy as np

class GloveDataset:

    def __init__(self, data_file_path, window_size=2):
        # Read the CSV file
        df = pd.read_csv(data_file_path)

        # Convert 'Ingredients' and 'Recipe' columns to strings
        df['Ingredients'] = df['Ingredients'].astype(str)
        df['Recipe'] = df['Recipe'].astype(str)

        # Select only the 'Ingredients' and 'Recipe' columns
        text = ' '.join(df['Ingredients'] + ' ' + df['Recipe']).lower()


        self._window_size = window_size

        self._tokens = text.split(" ")
        word_counter = Counter()
        word_counter.update(self._tokens)
        self._word2id = {w:i for i, (w,_) in enumerate(word_counter.most_common())}
        self._id2word = {i:w for w, i in self._word2id.items()}
        self._vocab_len = len(self._word2id)

        self._id_tokens = [self._word2id[w] for w in self._tokens]

        self._create_coocurrence_matrix()

        print("# of words: {}".format(len(self._tokens)))
        print("Vocabulary length: {}".format(self._vocab_len))

    def _create_coocurrence_matrix(self):
        cooc_mat = defaultdict(Counter)
        for i, w in enumerate(self._id_tokens):
            start_i = max(i - self._window_size, 0)
            end_i = min(i + self._window_size + 1, len(self._id_tokens))
            for j in range(start_i, end_i):
                if i != j:
                    c = self._id_tokens[j]
                    cooc_mat[w][c] += 1 / abs(j-i)

        self._i_idx = list()
        self._j_idx = list()
        self._xij = list()

        #Create indexes and x values tensors
        for w, cnt in cooc_mat.items():
            for c, v in cnt.items():
                self._i_idx.append(w)
                self._j_idx.append(c)
                self._xij.append(v)
        self._i_idx = torch.LongTensor(self._i_idx).to(device)
        self._j_idx = torch.LongTensor(self._j_idx).to(device)
        self._xij = torch.FloatTensor(self._xij).to(device)


    def get_batches(self, batch_size):
        #Generate random idx
        rand_ids = torch.LongTensor(np.random.choice(len(self._xij), len(self._xij), replace=False))

        for p in range(0, len(rand_ids), batch_size):
            batch_ids = rand_ids[p:p+batch_size]
            yield self._xij[batch_ids], self._i_idx[batch_ids], self._j_idx[batch_ids]

class GloveModel(nn.Module):
    def __init__(self, num_embeddings, embedding_dim):
        super(GloveModel, self).__init__()
        self.wi = nn.Embedding(num_embeddings, embedding_dim)
        self.wj = nn.Embedding(num_embeddings, embedding_dim)
        self.bi = nn.Embedding(num_embeddings, 1)
        self.bj = nn.Embedding(num_embeddings, 1)

        self.wi.weight.data.uniform_(-1, 1)
        self.wj.weight.data.uniform_(-1, 1)
        self.bi.weight.data.zero_()
        self.bj.weight.data.zero_()

    def forward(self, i_indices, j_indices):
        w_i = self.wi(i_indices)
        w_j = self.wj(j_indices)
        b_i = self.bi(i_indices).squeeze()
        b_j = self.bj(j_indices).squeeze()

        x = torch.sum(w_i * w_j, dim=1) + b_i + b_j

        return x

def weight_func(x, x_max, alpha):
    wx = (x/x_max)**alpha
    wx = torch.min(wx, torch.ones_like(wx)).to(device)
    return wx

def wmse_loss(weights, inputs, targets):
    loss = weights * F.mse_loss(inputs, targets, reduction='none')

    return torch.mean(loss).to(device)

from collections import Counter, defaultdict
path= '/content/drive/MyDrive/train.csv'
dataset = GloveDataset(path)
EMBED_DIM = 256

glove = GloveModel(dataset._vocab_len, EMBED_DIM).to(device)
optimizer = optim.Adam(glove.parameters(), lr=0.01)
import matplotlib.pyplot as plt
#training
N_EPOCHS = 10
BATCH_SIZE = 4000
X_MAX = 100
ALPHA = 0.75
n_batches = int(len(dataset._xij) / BATCH_SIZE)
loss_values = list()
for e in range(1, N_EPOCHS+1):
    batch_i = 0

    for x_ij, i_idx, j_idx in dataset.get_batches(BATCH_SIZE):

        batch_i += 1

        optimizer.zero_grad()

        outputs = glove(i_idx, j_idx)
        weights_x = weight_func(x_ij, X_MAX, ALPHA)
        loss = wmse_loss(weights_x, outputs, torch.log(x_ij))

        loss.backward()

        optimizer.step()

        loss_values.append(loss.item())

        if batch_i % 100 == 0:
            print("Epoch: {}/{} \t Batch: {}/{} \t Loss: {}".format(e, N_EPOCHS, batch_i, n_batches, np.mean(loss_values[-20:])))

plt.plot(loss_values)
print("Saving model...")
torch.save(glove.state_dict(), "GloVe.pt")

class EncoderRNN_glove(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers=1):
        super(EncoderRNN_glove, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        emb_i = torch.FloatTensor(glove.wi.weight.cpu().data.numpy())
        emb_j = torch.FloatTensor(glove.wj.weight.cpu().data.numpy())
        self.embedding = nn.Embedding.from_pretrained(emb_i + emb_j)
        self.lstm = nn.LSTM(hidden_size, hidden_size, num_layers=num_layers)

    def forward(self, input, hidden):
        embedded = self.embedding(input).view(1, 1, -1)
        output, hidden = self.lstm(embedded, hidden)
        return output, hidden

    def initHidden(self):
        return (torch.zeros(self.num_layers, 1, self.hidden_size, device=device),
                torch.zeros(self.num_layers, 1, self.hidden_size, device=device))

class AttnDecoderRNN_glove(nn.Module):
    def __init__(self, hidden_size, output_size, num_layers=1, dropout_p=0.1, max_length=MAX_LENGTH):
        super(AttnDecoderRNN_glove, self).__init__()
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.num_layers = num_layers
        self.dropout_p = dropout_p
        self.max_length = max_length

        # Assume glove.wi and glove.wj are pre-initialized GloVe weights
        emb_i = torch.FloatTensor(glove.wi.weight.cpu().data.numpy())
        emb_j = torch.FloatTensor(glove.wj.weight.cpu().data.numpy())
        self.embedding = nn.Embedding.from_pretrained(emb_i + emb_j)
        self.attn = nn.Linear(self.hidden_size * 2, self.max_length)
        self.attn_combine = nn.Linear(self.hidden_size * 2, self.hidden_size)
        self.dropout = nn.Dropout(self.dropout_p)
        self.lstm = nn.LSTM(self.hidden_size, self.hidden_size, num_layers=self.num_layers)
        self.out = nn.Linear(self.hidden_size, self.output_size)  # Corrected size for final output

    def forward(self, input, hidden, encoder_outputs):
        embedded = self.embedding(input).view(1, 1, -1)
        embedded = self.dropout(embedded)

        output, hidden = self.lstm(embedded, hidden)

        # Calculate attention weights from the current LSTM output and encoder outputs
        attn_weights = F.softmax(self.attn(torch.cat((output[0], hidden[0][-1]), 1)), dim=1)
        attn_applied = torch.bmm(attn_weights.unsqueeze(0), encoder_outputs.unsqueeze(0))

        # Concatenate the attention output with the LSTM output
        output = torch.cat((output[0], attn_applied[0]), 1)
        output = self.attn_combine(output).unsqueeze(0)

        output = F.relu(output)
        output = F.log_softmax(self.out(output[0]), dim=1)
        return output, hidden, attn_weights

    def initHidden(self):
        return (torch.zeros(self.num_layers, 1, self.hidden_size, device=device),
                torch.zeros(self.num_layers, 1, self.hidden_size, device=device))

hidden_size = 256
num_layers=1
encoder_glove = EncoderRNN_glove(input_ingredients.n_words, hidden_size,num_layers=num_layers).to(device)
attn_decoder_glove = AttnDecoderRNN_glove(hidden_size, output_recipe.n_words, num_layers=num_layers,dropout_p=0.1).to(device)


file_path='/content/drive/MyDrive/Colab Notebooks/checkpoint_attn_glove.pt'
train_losses_attn, val_losses_attn, val_every=trainIters_attn(encoder_glove, attn_decoder_glove, 50000, print_every=1000, validation_pairs=val_pairs, patience=3,file_path=file_path)

model_save_en= "encoder_attn_glove.pt"
path= f"/content/drive/MyDrive/{model_save_en}"
torch.save(encoder_glove.state_dict(),path)

model_save_de= "decoder_attn_glove.pt"
path= f"/content/drive/MyDrive/{model_save_de}"
torch.save(attn_decoder_glove.state_dict(),path)

evaluateRandomly_attn(encoder, attn_decoder, save_path='gen_vs_test_seq2seq_withattn_glove.csv')

hidden_size=256
# without attention
checkpoint_path = '/content/drive/MyDrive/Colab Notebooks/checkpoint_50000.pt'
encoder1 = EncoderRNN(input_ingredients.n_words, hidden_size).to(device)
decoder1 = DecoderRNN(hidden_size, output_recipe.n_words).to(device)
encoder_optimizer = optim.Adam(encoder1.parameters(), lr=0.01)
decoder_optimizer = optim.Adam(decoder1.parameters(), lr=0.01)

#with attention
checkpoint_path_attn =  '/content/drive/MyDrive/Colab Notebooks/checkpoint_attn_new.pt'
encoder = EncoderRNN(input_ingredients.n_words, hidden_size).to(device)
attn_decoder = AttnDecoderRNN(hidden_size, output_recipe.n_words, dropout_p=0.1).to(device)
encoder_optimizer_attn = optim.Adam(encoder.parameters(), lr=0.01)
decoder_optimizer_attn = optim.Adam(attn_decoder.parameters(), lr=0.01)

#with layers
num_layers=4
checkpoint_path_layers = '/content/drive/MyDrive/Colab Notebooks/checkpoint_attn_layers.pt'
encoder_layers = EncoderRNN_layers(input_ingredients.n_words, hidden_size,num_layers=num_layers).to(device)
attn_decoder_layers = AttnDecoderRNN_layers(hidden_size, output_recipe.n_words, num_layers=num_layers,dropout_p=0.1).to(device)
encoder_optimizer_layers = optim.Adam(encoder_layers.parameters(), lr=0.01)
decoder_optimizer_layers = optim.Adam(attn_decoder_layers.parameters(), lr=0.01)

#with glove
num_layers=1
checkpoint_path_glove ='/content/drive/MyDrive/Colab Notebooks/checkpoint_attn_glove.pt'
encoder_glove = EncoderRNN_glove(input_ingredients.n_words, hidden_size,num_layers=num_layers).to(device)
attn_decoder_glove = AttnDecoderRNN_glove(hidden_size, output_recipe.n_words, num_layers=num_layers,dropout_p=0.1).to(device)
encoder_optimizer_glove = optim.Adam(encoder_glove.parameters(), lr=0.01)
decoder_optimizer_glove = optim.Adam(attn_decoder_glove.parameters(), lr=0.01)



encoder, decoder, encoder_optimizer, decoder_optimizer, epoch, train_losses, val_losses = load_checkpoint(encoder1, decoder1, encoder_optimizer, decoder_optimizer, checkpoint_path)

encoder_attn, decoder_attn, encoder_optimizer_attn, decoder_optimizer_attn, epoch_attn, train_losses_attn, val_losses_attn = load_checkpoint(encoder, attn_decoder, encoder_optimizer_attn, decoder_optimizer_attn, checkpoint_path_attn)
encoder_layers, decoder_layers, encoder_optimizer_layers, decoder_optimizer_layers, epochattn, train_losses_layers, val_losses_layers = load_checkpoint(encoder_layers, attn_decoder_layers, encoder_optimizer_layers, decoder_optimizer_layers, checkpoint_path_layers)
encoder_glove, decoder_glove, encoder_optimizer_glove, decoder_optimizer_glove, epoch_attn, train_losses_glove, val_losses_glove = load_checkpoint(encoder_glove, attn_decoder_glove, encoder_optimizer_glove, decoder_optimizer_glove, checkpoint_path_glove)

evaluateRandomly(encoder1, decoder1, save_path='/content/drive/MyDrive/gen_vs_test_seq2seq.csv')
evaluateRandomly_attn(encoder_attn, decoder_attn, save_path='/content/drive/MyDrive/Colab Notebooks/gen_vs_test_seq2seq_withattn.csv')
evaluateRandomly_attn(encoder_layers, decoder_layers, save_path='/content/drive/MyDrive/Colab Notebooks/gen_vs_test_seq2seq_layers.csv')
evaluateRandomly_attn(encoder_glove, decoder_glove, save_path='/content/drive/MyDrive/Colab Notebooks/gen_vs_test_seq2seq_glove.csv')

import matplotlib.pyplot as plt
import matplotlib.ticker as ticker


def showPlot_allmodels(train_losses_list, val_losses_list, total_epochs, val_every, plot_every):
    colors = ['b', 'g', 'r', 'c']

    plt.figure()
    loc = ticker.MultipleLocator(base=0.5)
    plt.gca().yaxis.set_major_locator(loc)

    train_epochs = range(plot_every, total_epochs + 1, plot_every)
    val_epochs = range(val_every, total_epochs + 1, val_every)

    for i, (train_losses, val_losses) in enumerate(zip(train_losses_list, val_losses_list)):
        color = colors[i % len(colors)]  # Cycle through colors if more models than colors
        train_label = f'Training Loss (Model {i+1})'
        val_label = f'Validation Loss (Model {i+1})'

        # Plot training losses with solid line
        epochs_train = range(plot_every, plot_every*len(train_losses) + 1, plot_every)
        plt.plot(epochs_train, train_losses, label=train_label, color=color, linestyle='-')

        # Plot validation losses with dotted line
        if val_losses:
            epochs_val = range(val_every, val_every*len(val_losses) + 1, val_every)
            plt.plot(epochs_val, val_losses, label=val_label, color=color, linestyle=':')

    plt.xlabel('Epoch')
    plt.ylabel('Loss')
    plt.title('Training and Validation Loss')
    plt.legend()
    plt.show()



train_losses_list = [train_losses, train_losses_attn, train_losses_layers, train_losses_glove]
val_losses_list = [val_losses, val_losses_attn, val_losses_layers, val_losses_glove]
showPlot_allmodels(train_losses_list, val_losses_list, total_epochs= 50000,val_every=5000, plot_every=1000)

analyze_model('/content/drive/MyDrive/goldvssample.csv')

def evaluate(encoder, decoder, sentence, max_length=MAX_LENGTH):
    with torch.no_grad():
        input_tensor = tensorFromSentence(input_ingredients, sentence)
        input_length = input_tensor.size()[0]
        encoder_hidden = encoder.initHidden()

        encoder_outputs = torch.zeros(max_length, encoder.hidden_size, device=device)

        for ei in range(input_length):
            encoder_output, encoder_hidden = encoder(input_tensor[ei],
                                                     encoder_hidden)
            encoder_outputs[ei] += encoder_output[0, 0]

        decoder_input = torch.tensor([[SOS_token]], device=device)  # SOS

        decoder_hidden = encoder_hidden

        decoded_words = []
        decoder_attentions = torch.zeros(max_length, max_length)

        for di in range(max_length):
            decoder_output, decoder_hidden = decoder(
                decoder_input, decoder_hidden)
            topv, topi = decoder_output.data.topk(1)
            if topi.item() == EOS_token:
                decoded_words.append('<EOS>')
                break
            else:
                decoded_words.append(output_recipe.index2word[topi.item()])

            decoder_input = topi.squeeze().detach()

        return decoded_words

def evaluatesample(encoder, decoder):
    ingredients=  "2 c sugar, 1/4 c lemon juice, 1 c water, 1/3 c orange juice, 8 c strawberries"
    output_words= evaluate(encoder, decoder, ingredients)
    output_sentence = ' '.join(output_words)
    print('<', output_sentence) #generated recipe
    print('')

def evaluatesample_attn(encoder, decoder):
    ingredients=  "2 c sugar, 1/4 c lemon juice, 1 c water, 1/3 c orange juice, 8 c strawberries"
    output_words, attention= evaluate_attn(encoder, decoder, ingredients)
    output_sentence = ' '.join(output_words)
    print('<', output_sentence)
    print('')

evaluatesample(encoder1, decoder1)
evaluatesample_attn(encoder_attn, decoder_attn)
evaluatesample_attn(encoder_layers, decoder_layers)
evaluatesample_attn(encoder_glove, decoder_glove)