from sklearn.datasets import fetch_20newsgroups
from sklearn.linear_model import SGDClassifier
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer

from catalog.models import Product, Category

from nltk.tokenize import wordpunct_tokenize
from nltk.corpus import stopwords
import nltk


from keras.models import Sequential
from keras.layers import LSTM, Dense, Activation, Dropout, Embedding
import pandas as pd
import keras.utils
from keras.preprocessing.text import Tokenizer
from keras.preprocessing import sequence
from sklearn.preprocessing import LabelEncoder
import numpy as np
from keras.datasets import imdb

from keras.models import load_model
import numpy as np
from keras.preprocessing.text import Tokenizer
import pandas as pd

import re

import ssl


def formalize_products():
	ntwrk = NeuralNetworkOption2()
	for product in Product.objects.all():
		title = product.title
		if title:
			raw = product.raw
			if not raw:
				raw = {}
			raw['formalized_title'] = ntwrk.remove_stop_words(title.lower())
			product.raw = raw
			product.save(update_fields='raw')


class NeuralNetworkOption2(object):
	# define constants
	max_words = 1000
	batch_size = 32
	epochs = 3
	
	try:
		_create_unverified_https_context = ssl._create_unverified_context
	except AttributeError:
		pass
	else:
		ssl._create_default_https_context = _create_unverified_https_context
	"""
	https://habr.com/ru/post/350900/

	"""
	
	def __init__(self):
		nltk.download('stopwords')
		# stop = set(stopwords.words('russian', ))
		# инициализируем стоп слова и символы
		self.stop = set(stopwords.words('russian'))
		self.stop.update(['.', ',', '"', "'", '?', '!', ':', ';', '(', ')', '[', ']', '{', '}', '#', '№'])
		
		self.Y_raw = Product.objects.filter(is_tried=True).select_related('category').values_list('category__title',
		                                                                                          flat=True)
		
		self.X_raw = Product.objects.filter(is_tried=True).values_list('title', flat=True)
		
		self.count_raw = self.X_raw.count()
		self.length = int(self.count_raw - self.count_raw / 10)  # 10%
		
		self.X_raw_train = self.X_raw[:self.length]
		self.Y_raw_train = self.Y_raw[:self.length]
		self.num_classes = self.Y_raw_train.count()
	
	def remove_stop_words(self, query):
		formalized_query = re.sub(r'[^\w\s]+|[\d]+', r'', query).strip()
		string = ''
		for i in wordpunct_tokenize(formalized_query):
			if i not in self.stop and not i.isdigit():
				string = string + i + ' '
		
		return string
	
	def _fit(self):
		# трансформируем текст запросов в матрицы
		tokenizer = Tokenizer(num_words=self.max_words)
		tokenizer.fit_on_texts(self.X_raw_train)
		x_train = tokenizer.texts_to_matrix(self.X_raw_train)
		
		# трансформируем классы
		encoder = LabelEncoder()
		encoder.fit(self.Y_raw_train)
		
		encoded_Y = encoder.transform(self.Y_raw_train)
		print(encoded_Y)
		y_train = keras.utils.to_categorical(encoded_Y, self.num_classes)
		
		# строим модель
		model = Sequential()
		model.add(Dense(512, input_shape=(self.max_words,)))
		model.add(Activation('relu'))
		model.add(Dropout(0.5))
		model.add(Dense(self.num_classes))
		model.add(Activation('softmax'))
		
		model.compile(loss='categorical_crossentropy',
		              optimizer='adam',
		              metrics=['accuracy'])
		
		model.fit(x_train, y_train,
		          batch_size=self.batch_size,
		          epochs=self.epochs,
		          verbose=1)
		
		model.save('classifier.h5')
	
	def predict(self, str_query, numwords):
		model = load_model('classifier.h5')
		tokenizer = Tokenizer(num_words=numwords)
		X_raw_test = [str_query]
		# df = pd.read_csv('cleaned_dataset.csv', delimiter=';', encoding="utf-8").astype(str)
		# X_raw = df['запрос'].values
		X_raw = self.X_raw_train
		tokenizer.fit_on_texts(X_raw)
		x_test = tokenizer.texts_to_matrix(X_raw_test, mode='binary')
		prediction = model.predict(np.array(x_test))
		class_num = np.argmax(prediction[0])
		return class_num
# sys.stderr = stderr
# for name, index in classes.items():
# 	if index == class_num:
# 		print(name)


class NeuralNetworkOption1(object):
	"""
	http://zabaykin.ru/?p=558
	Simple neural network
	precision ~ 62% without removing stop words
	"""
	
	def __init__(self):
		
		# clf = SGDClassifier or RandomForestClassifier
		clf = SGDClassifier
		
		self.text_clf = Pipeline([
			('tfidf', TfidfVectorizer()),
			('clf', clf())
		])
		
		self.texts_labels = Product.objects.filter(is_tried=True).select_related('category').values_list('category__id',
		                                                                                                 flat=True)
		self.texts = Product.objects.filter(is_tried=True).values_list('title', flat=True)
		
		self.count_text = self.texts.count()
		self.length = int(self.count_text - self.count_text / 10)  # 10%
		
		self._fit()
	
	def _fit(self):
		self.text_clf.fit(self.texts[:self.length], self.texts_labels[:self.length])
	
	def prediction_check(self):
		
		truth, untruth = 0, 0
		
		for i, label in enumerate(self.texts[self.length + 1:]):
			res = self.text_clf.predict([label])
			if res[0] == self.texts_labels[self.length + i + 1]:
				truth += 1
			else:
				untruth += 1
		
		correct = (truth * 100) / (self.count_text - self.length)
		not_correct = 100 - correct
		
		print('Result: correct is {}, not correct {}'.format(correct, not_correct))
# print(truth, untruth)
