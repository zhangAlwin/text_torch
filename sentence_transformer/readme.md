# SimCSE
Gao et al. present in [SimCSE](https://arxiv.org/abs/2104.08821) a simple method to train sentence embeddings without having training data. 

The idea is to encode the same sentence twice. Due to the used dropout in transformer models, both sentence embeddings will be at slightly different positions. The distance between these two embeddings will be minized, while the distance to other embeddings of the other sentences in the same batch will be maximized (they serve as negative examples).

![SimCSE working](https://raw.githubusercontent.com/UKPLab/sentence-transformers/master/docs/img/SimCSE.png)

## Usage with SentenceTransformers
SentenceTransformers implements the [MultipleNegativesRankingLoss](https://www.sbert.net/docs/package_reference/losses.html#multiplenegativesrankingloss), which makes training with SimCSE trivial:

```python
from sentence_transformers import SentenceTransformer, InputExample
from sentence_transformers import models, losses
from torch.utils.data import DataLoader
# Define your sentence transformer model using CLS pooling
model_name = 'distilroberta-base'
word_embedding_model = models.Transformer(model_name, max_seq_length=32)
pooling_model = models.Pooling(word_embedding_model.get_word_embedding_dimension())
model = SentenceTransformer(modules=[word_embedding_model, pooling_model])
# Define a list with sentences (1k - 100k sentences)
train_sentences = ["Your set of sentences",
                   "Model will automatically add the noise",
                   "And re-construct it",
                   "You should provide at least 1k sentences"]
# Convert train sentences to sentence pairs
train_data = [InputExample(texts=[s, s]) for s in train_sentences]
# DataLoader to batch your data
train_dataloader = DataLoader(train_data, batch_size=128, shuffle=True)
# Use the denoising auto-encoder loss
train_loss = losses.MultipleNegativesRankingLoss(model)
# Call the fit method
model.fit(
    train_objectives=[(train_dataloader, train_loss)],
    epochs=1,
    show_progress_bar=True
)
model.save('output/simcse-model')
``` 

## Download SimCSE training datasets
数据集来源于苏建林repo整理 https://github.com/bojone/SimCSE
  
1.[senteval_cn](https://cloud.189.cn/t/mimMR3mMZJzq)  
2.[cnsd-snli](https://cloud.189.cn/t/ZZVJ7ryyuQZr)


## Training Examples
- **[train_simcse.py](train_stsb_simcse.py)** 