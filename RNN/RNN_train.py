from function import *
import re
import pathlib


temp = pathlib.PosixPath
pathlib.PosixPath = pathlib.WindowsPath

class RNN:
    def __init__(self, word_dim, tag_dim, hidden_dim=100, bptt_truncate=4):
        self.word_dim = word_dim
        self.hidden_dim = hidden_dim
        self.tag_dim = tag_dim
        self.bptt_truncate = bptt_truncate

        self.E = np.random.uniform(-np.sqrt(1. / word_dim), np.sqrt(1. / word_dim), (word_dim, word_dim))

        self.U = np.random.uniform(-np.sqrt(1. / word_dim), np.sqrt(1. / word_dim), (hidden_dim, word_dim))
        self.V = np.random.uniform(-np.sqrt(1. / hidden_dim), np.sqrt(1. / hidden_dim), (tag_dim, hidden_dim))
        self.W = np.random.uniform(-np.sqrt(1. / hidden_dim), np.sqrt(1. / hidden_dim), (hidden_dim, hidden_dim))

    def forward(self, x):
        T = len(x)

        s = np.zeros((T + 1, self.hidden_dim))
        s[-1] = np.zeros(self.hidden_dim)

        o = np.zeros((T, self.tag_dim))

        for t in np.arange(T):
            x_t = self.E[:, x[t]]
            s[t] = np.tanh(self.U.dot(x_t) + self.W.dot(s[t - 1]))
            o[t] = softmax(self.V.dot(s[t]))
        return [o, s]

    def predict(self, x):
        o, s = self.forward(x)
        return np.argmax(o, axis=1)

    def calculate_total_loss(self, x, y):
        L = 0

        for i in np.arange(len(y)):
            o, s = self.forward(x[i])
            correct_word_predictions = o[np.arange(len(y[i])), y[i]]
            L += -1 * np.sum(np.log(correct_word_predictions))
        return L

    def calculate_loss(self, x, y):
        N = sum((len(y_i) for y_i in y))
        return self.calculate_total_loss(x, y) / N

    def backward(self, x, y):
        T = len(x)
        o, s = self.forward(x)

        dLdU = np.zeros(self.U.shape)
        dLdV = np.zeros(self.V.shape)
        dLdW = np.zeros(self.W.shape)
        dLdE = np.zeros(self.E.shape)

        delta_o = o
        delta_o[np.arange(len(y)), y] -= 1

        for t in np.arange(T)[::-1]:
            dLdV += np.outer(delta_o[t], s[t].T)
            delta_t = self.V.T.dot(delta_o[t]) * (1 - (s[t] ** 2))
            for bptt_step in np.arange(max(0, t - self.bptt_truncate), t + 1)[::-1]:
                dLdW += np.outer(delta_t, s[bptt_step - 1])
                dLdU[:, x[bptt_step]] += delta_t
                dLdE[:, x[bptt_step]] += self.U.T.dot(delta_t)
                delta_t = self.W.T.dot(delta_t) * (1 - (s[bptt_step] ** 2))

        return [dLdU, dLdV, dLdW, dLdE]

    def sgd_step(self, x, y, learning_rate=0.01):
        dLdU, dLdV, dLdW, dLdE = self.backward(x, y)

        self.U -= learning_rate * dLdU
        self.V -= learning_rate * dLdV
        self.W -= learning_rate * dLdW
        self.E -= learning_rate * dLdE