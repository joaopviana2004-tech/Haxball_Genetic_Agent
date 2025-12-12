import numpy as np
import config

class RedeNeural:
    def __init__(self, input_size=9, hidden_size=config.HIDDEN_SIZE_LAYER, output_size=2):
        """
        input_size: Quantidade de dados de entrada
        hidden_size: Pode ser um int (ex: 12) ou uma lista (ex: [12, 8, 6]) definindo várias camadas
        output_size: 2 (ax, ay)
        """
        self.input_size = input_size
        self.output_size = output_size
        
        # Garante que hidden_size seja uma lista, mesmo que venha como int
        if isinstance(hidden_size, int):
            self.hidden_sizes = [hidden_size]
        else:
            self.hidden_sizes = hidden_size

        # Inicializa listas para armazenar Pesos (W) e Viéses (b) de todas as camadas
        self.weights = []
        self.biases = []

        # --- Construção Dinâmica das Camadas ---
        
        # 1. Camada de Entrada -> Primeira Camada Oculta
        prev_size = self.input_size
        
        # Cria as camadas ocultas baseadas na lista
        for size in self.hidden_sizes:
            # Pesos: (tamanho_anterior, tamanho_atual)
            W = np.random.randn(prev_size, size)
            b = np.zeros((1, size))
            
            self.weights.append(W)
            self.biases.append(b)
            prev_size = size
            
        # 2. Última Camada Oculta -> Saída
        W_out = np.random.randn(prev_size, self.output_size)
        b_out = np.zeros((1, self.output_size))
        
        self.weights.append(W_out)
        self.biases.append(b_out)

        self.last_activations = []

    def tanh(self, x):
        return np.tanh(x)

    def feedForward(self, inputs):
        self.last_activations = [] # Limpa ativações anteriores
        
        inputs = np.array(inputs).reshape(1, -1)
        
        # A primeira "ativação" é o próprio input
        self.last_activations.append(inputs[0]) 

        current_activation = inputs

        # Passa por todas as camadas
        for W, b in zip(self.weights, self.biases):
            z = np.dot(current_activation, W) + b
            current_activation = self.tanh(z)
            self.last_activations.append(current_activation[0])

        return current_activation[0]

    def mutate(self, mutation_rate=0.1, mutation_scale=0.2):
        """
        Aplica mutação em todas as matrizes de peso e viés da lista
        """
        def mutate_matrix(matrix):
            mask = np.random.rand(*matrix.shape) < mutation_rate
            noise = np.random.randn(*matrix.shape) * mutation_scale
            matrix[mask] += noise[mask]
            return matrix

        # Aplica mutação em cada camada armazenada nas listas
        for i in range(len(self.weights)):
            self.weights[i] = mutate_matrix(self.weights[i])
            self.biases[i] = mutate_matrix(self.biases[i])

    def copy(self):
        """
        Cria uma cópia exata, suportando a estrutura dinâmica
        """
        # Cria nova rede com a mesma estrutura de camadas
        nova_rede = RedeNeural(self.input_size, self.hidden_sizes, self.output_size)
        
        # Copia profundamente as listas de pesos e viéses
        nova_rede.weights = [w.copy() for w in self.weights]
        nova_rede.biases = [b.copy() for b in self.biases]
        
        return nova_rede