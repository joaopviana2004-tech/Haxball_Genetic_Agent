import numpy as np
import config

class RedeNeural:
    def __init__(self, input_size=9, hidden_size=config.HIDDEN_SIZE_LAYER, output_size=2):
        """
        input_size: Quantidade de dados de entrada (bola, inimigo, gol, etc.)
        hidden_size: Neurônios na camada oculta (pode ajustar para mais inteligência/complexidade)
        output_size: 2 (ax, ay)
        """
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size

        # Inicialização dos pesos (W) e viéses (b) com valores aleatórios
        # W1: Pesos da Entrada -> Oculta
        self.W1 = np.random.randn(self.input_size, self.hidden_size)
        self.b1 = np.zeros((1, self.hidden_size))
        
        # W2: Pesos da Oculta -> Saída
        self.W2 = np.random.randn(self.hidden_size, self.output_size)
        self.b2 = np.zeros((1, self.output_size))

    def tanh(self, x):
        # Retorna valores entre -1 e 1 (Perfeito para direção/aceleração)
        return np.tanh(x)

    def feedForward(self, inputs):
        """
        Recebe a lista de inputs e retorna a aceleração ax, ay
        """
        # Garante que o input seja um array numpy no formato correto
        inputs = np.array(inputs).reshape(1, -1)

        # Camada 1 (Entrada -> Oculta)
        self.z1 = np.dot(inputs, self.W1) + self.b1
        self.a1 = self.tanh(self.z1) # Ativação da oculta

        # Camada 2 (Oculta -> Saída)
        self.z2 = np.dot(self.a1, self.W2) + self.b2
        output = self.tanh(self.z2) # Ativação final

        # Retorna ax, ay (valores entre -1 e 1)
        return output[0] 

    def mutate(self, mutation_rate=0.1, mutation_scale=0.2):
        """
        Função vital para o Algoritmo Genético.
        Altera levemente os pesos da rede para criar variação.
        """
        # Função auxiliar para aplicar mutação em uma matriz
        def mutate_matrix(matrix):
            mask = np.random.rand(*matrix.shape) < mutation_rate
            noise = np.random.randn(*matrix.shape) * mutation_scale
            matrix[mask] += noise[mask]
            return matrix

        self.W1 = mutate_matrix(self.W1)
        self.b1 = mutate_matrix(self.b1)
        self.W2 = mutate_matrix(self.W2)
        self.b2 = mutate_matrix(self.b2)

    def copy(self):
        """
        Cria uma cópia exata dessa rede (para clonar o melhor da geração)
        """
        nova_rede = RedeNeural(self.input_size, self.hidden_size, self.output_size)
        nova_rede.W1 = self.W1.copy()
        nova_rede.b1 = self.b1.copy()
        nova_rede.W2 = self.W2.copy()
        nova_rede.b2 = self.b2.copy()
        return nova_rede