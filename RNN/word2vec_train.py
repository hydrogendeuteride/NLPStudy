from word2vec import *
from train import *
from utils import *
import time
import numpy as np

try:
    import cupy

    array_library = cupy
except ImportError:
    array_library = np


def find_nearest(word, embeddings, word_to_index, index_to_word, k=5):
    if word not in word_to_index:
        return "Word not in dictionary."

    vec = embeddings[:, word_to_index[word]]
    similarity = np.dot(embeddings.T, vec)
    norms = np.linalg.norm(embeddings, axis=0) * np.linalg.norm(vec)
    similarity /= norms

    nearest = np.argsort(-similarity)[1:k + 1]
    nearest_words = [index_to_word[idx] for idx in nearest]
    return nearest_words


def analogy(word_a, word_b, word_c, embeddings, word_to_index, index_to_word):
    vec_a = embeddings[:, word_to_index[word_a]]
    vec_b = embeddings[:, word_to_index[word_b]]
    vec_c = embeddings[:, word_to_index[word_c]]
    vec_result = vec_b - vec_a + vec_c
    similarity = np.dot(embeddings.T, vec_result)
    norms = np.linalg.norm(embeddings, axis=0) * np.linalg.norm(vec_result)
    similarity /= norms

    nearest = np.argsort(-similarity)[0:5]
    nearest_words = [index_to_word[idx] for idx in nearest]
    return nearest_words


data_line = read_file_to_list('../dataset/tagged_train.txt')
processed_data_line = reader(data_line[:8192])
pos_cnt, word_cnt = count_word_POS(processed_data_line)
word_to_idx, tag_to_idx = build_vocab(word_cnt, pos_cnt)

x1, y1 = text_to_indices(processed_data_line, word_to_idx, tag_to_idx)
idx_to_tag = build_reverse_tag_index(tag_to_idx)
idx_to_word = {idx: word for word, idx in word_to_idx.items()}

print(len(word_to_idx))
model = SkipGram(len(word_to_idx), 512, use_gpu=True)

train_skipgram(model, x1, len(word_to_idx), evaluation_interval=1)

print("\nTesting with nearest words:")
test_words = ['example', 'data', 'network', 'algorithm']
for word in test_words:
    if word in word_to_idx:
        nearest = find_nearest(word, model.W1, word_to_idx, idx_to_word, k=5)
        print(f"Nearest to '{word}': {nearest}")
    else:
        print(f"'{word}' not found in the vocabulary.")

print("\nTesting with analogies:")
triplets = [('king', 'man', 'queen'), ('paris', 'france', 'london')]
for a, b, c in triplets:
    if a in word_to_idx and b in word_to_idx and c in word_to_idx:
        result = analogy(a, b, c, model.W1.T, word_to_idx, idx_to_word)
        print(f"'{a}' is to '{b}' as '{c}' is to {result}")
    else:
        print(f"Words '{a}', '{b}', or '{c}' not found in vocabulary.")