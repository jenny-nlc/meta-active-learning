'''Trains a simple convnet on the MNIST dataset.

Gets to 99.25% test accuracy after 12 epochs
(there is still a lot of margin for parameter tuning).
16 seconds per epoch on a GRID K520 GPU.
'''

from __future__ import print_function
import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K
from scipy.spatial.distance import pdist, squareform
from keras.layers.core import Lambda
import numpy as np
import scipy as sp
from scipy import linalg
from random import randint
from keras import regularizers
import random
import pdb
import argparse
import os
from oracle import KNOracle

parser = argparse.ArgumentParser()
named_args = parser.add_argument_group('named arguments')

named_args.add_argument('-g', '--gpu',
                        help="""gpu to use""",
                        required=False, type=str, default='0')
named_args.add_argument('-o', '--oracle',
			help="""oracle to use either `nearestlabel`, `nearestpoint`""",
			required=True, type=str)

named_args.add_argument('-e', '--epochs',
      help="""# of epochs to train""",
      required=False, type=int, default=1000)

named_args.add_argument('-a', '--acquisitions',
      help="""# of acquisitions for active learning""",
      required=False, type=int, default=980)


named_args.add_argument('-t', '--n_experiments',
      help="""# of experiments with different random seeds""",
      required=False, type=int, default=5)



named_args.add_argument('-d', '--dropoutiterations',
      help="""# of dropout estimates""",
      required=False, type=int, default=100)


named_args.add_argument('-s', '--save_dir',
      help="""`""",
      required=True, type=str, default='./results/')


args = parser.parse_args()

assert args.oracle in ['nearestlabel', 'nearestpoint']

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu





def split_data_into_binary(x_train, y_train, x_test, y_test):
    class_2 = np.where(y_train==2)[0]
    class_8 = np.where(y_train==8)[0]
    x_2 = x_train[class_2, :, :, :]
    y_2 = y_train[class_2]
    x_8 = x_train[class_8, :, :, :]
    y_8 = y_train[class_8]

    x_train = np.concatenate((x_2, x_8), axis=0)
    y_train = np.concatenate((y_2, y_8), axis=0)

    class_2 = np.where(y_test==2)[0]
    class_8 = np.where(y_test==8)[0]

    x_2 = x_test[class_2, :, :, :]
    y_2 = y_test[class_2]
    x_8 = x_test[class_8, :, :, :]
    y_8 = y_test[class_8]

    x_test = np.concatenate((x_2, x_8), axis=0)
    y_test = np.concatenate((y_2, y_8), axis=0)

    #randomly shuffle the data again
    random_split = np.asarray(random.sample(range(0,x_train.shape[0]), x_train.shape[0]))
    x_train = x_train[random_split, :, :, :]
    y_train = y_train[random_split]

    random_split = np.asarray(random.sample(range(0,x_test.shape[0]), x_test.shape[0]))
    x_test = x_test[random_split, :, :, :]
    y_test = y_test[random_split]


    return x_train, y_train, x_test, y_test


def get_valid_data(x_train, y_train):
    #split into train and validation sets
    valid_shape = np.int(np.round(x_train.shape[0]*0.1))
    x_valid = x_train[-valid_shape:, :, :, :]
    y_valid = y_train[-valid_shape:]

    x_train = x_train[0:-valid_shape, :, :, :]
    y_train = y_train[0:-valid_shape]


    return x_train, y_train, x_valid, y_valid


def get_pool_data(x_train, y_train, initial_train_point):
    x_pool = x_train[initial_train_point:, :, :, :]
    y_pool = y_train[initial_train_point:]

    x_train = x_train[0:initial_train_point, :, :, :]
    y_train = y_train[0:initial_train_point]

    return x_train, y_train, x_pool, y_pool

def get_uniform_training_data(x_train, y_train):

  idx_0 = np.array(  np.where(y_train == 0) ).T
  idx_0 = idx_0[0:2, 0]
  x_0 = x_train[idx_0, :, :, :]
  y_0 = y_train[idx_0]

  idx_1 = np.array(  np.where(y_train == 1) ).T
  idx_1 = idx_1[0:2, 0]
  x_1 = x_train[idx_1, :, :, :]
  y_1 = y_train[idx_1]

  idx_2 = np.array(  np.where(y_train == 2) ).T
  idx_2 = idx_2[0:2, 0]
  x_2 = x_train[idx_2, :, :, :]
  y_2 = y_train[idx_2]

  idx_3 = np.array(  np.where(y_train == 3) ).T
  idx_3 = idx_3[0:2, 0]
  x_3 = x_train[idx_3, :, :, :]
  y_3 = y_train[idx_3]

  idx_4 = np.array(  np.where(y_train == 4) ).T
  idx_4 = idx_4[0:2, 0]
  x_4 = x_train[idx_4, :, :, :]
  y_4 = y_train[idx_4]

  idx_5 = np.array(  np.where(y_train == 5) ).T
  idx_5 = idx_5[0:2, 0]
  x_5 = x_train[idx_5, :, :, :]
  y_5 = y_train[idx_5]

  idx_6 = np.array(  np.where(y_train == 6) ).T
  idx_6 = idx_6[0:2, 0]
  x_6 = x_train[idx_6, :, :, :]
  y_6 = y_train[idx_6]

  idx_7 = np.array(  np.where(y_train == 7) ).T
  idx_7 = idx_7[0:2, 0]
  x_7 = x_train[idx_7, :, :, :]
  y_7 = y_train[idx_7]

  idx_8 = np.array(  np.where(y_train == 8) ).T
  idx_8 = idx_8[0:2, 0]
  x_8 = x_train[idx_8, :, :, :]
  y_8 = y_train[idx_8]

  idx_9 = np.array(  np.where(y_train == 9) ).T
  idx_9 = idx_9[0:2, 0]
  x_9 = x_train[idx_9, :, :, :]
  y_9 = y_train[idx_9]


  x_train = np.concatenate((x_0, x_1, x_2, x_3, x_4, x_5, x_6, x_7, x_8, x_9), axis=0)
  y_train = np.concatenate((y_0, y_1, y_2, y_3, y_4, y_5, y_6, y_7, y_8, y_9), axis=0)


  return x_train, y_train


def remove_pool_labels_for_oracle(x_pool, y_pool):

  z =  np.arange(np.int(np.round(x_pool.shape[0]*0.5)))
  np.random.shuffle(z) 
  y_pool[z] = 10

  return y_pool


def get_pool_index_unknown_to_oracle(Pooled_Y):
  index_unknown_to_oracle = np.where(Pooled_Y == 10)
  print(index_unknown_to_oracle)
  index_unknown_to_oracle = np.asarray(list(index_unknown_to_oracle))[0,:]
  print(index_unknown_to_oracle)
  #returns index of pooled points that are unknown to oracle
  return index_unknown_to_oracle


batch_size = 128
num_classes = 10
epochs = args.epochs
acquisition_iterations = args.acquisitions
## use MC Samples = 100
dropout_iterations = args.dropoutiterations
Queries = 10


# input image dimensions
img_rows, img_cols = 28, 28
nb_filters = 32
nb_pool = 4
nb_conv = 3


Experiments = args.n_experiments


Exp_Training_Loss = np.zeros(shape=(acquisition_iterations+1, Experiments))
Exp_Valid_Acc = np.zeros(shape=(acquisition_iterations+1, Experiments))
Exp_Test_Acc = np.zeros(shape=(acquisition_iterations+1, Experiments))




for e in range(Experiments):

  print ("EXPERIMENT NUMBER", e)

  # the data, shuffled and split between train and test sets
  (x_train, y_train), (x_test, y_test) = mnist.load_data()

  if K.image_data_format() == 'channels_first':
      print ("Using Channels first")
      x_train = x_train.reshape(x_train.shape[0], 1, img_rows, img_cols)
      x_test = x_test.reshape(x_test.shape[0], 1, img_rows, img_cols)
      input_shape = (1, img_rows, img_cols)
  else:
      print("Channels last")
      x_train = x_train.reshape(x_train.shape[0], img_rows, img_cols, 1)
      x_test = x_test.reshape(x_test.shape[0], img_rows, img_cols, 1)
      input_shape = (img_rows, img_cols, 1)


  x_train, y_train, x_valid, y_valid = get_valid_data(x_train, y_train)

  initial_train_point = 10000 
  x_train, y_train, x_pool, y_pool = get_pool_data(x_train, y_train, initial_train_point)


  #get uniform distribution for initial training points
  #start with uniform labels for 20 training points
  x_train, y_train = get_uniform_training_data(x_train, y_train)


  print('x_train shape:', x_train.shape)
  print(x_train.shape[0], 'train samples')
  print (x_pool.shape[0], 'pool samples')
  print(x_valid.shape[0], 'valid samples')
  print(x_test.shape[0], 'test samples')

  """
  Remove majority of labels (70% of data) from pool sets
  Use some form of clustering/similarity metric to infer labels of Unlabelled points
  based on existing labels available 
  """


  ### normalize and convert to categorical
  x_train = x_train.astype('float32')
  x_valid = x_valid.astype('float32')
  x_pool = x_pool.astype('float32')
  x_test = x_test.astype('float32')

  x_train /= 255
  x_valid /= 255
  x_pool /= 255
  x_test /= 255
  # convert class vectors to binary class matrices
  y_train = keras.utils.to_categorical(y_train, num_classes)
  y_valid = keras.utils.to_categorical(y_valid, num_classes)
  # y_pool = keras.utils.to_categorical(y_pool, num_classes)
  y_test = keras.utils.to_categorical(y_test, num_classes)

  # for mnist : assign unknown label to pool set labels (that Oracle has access to)
  y_pool = remove_pool_labels_for_oracle(x_pool, y_pool)
  x_pool_with_labels = x_pool[y_pool != 10]
  y_pool_with_labels = y_pool[y_pool != 10]
  # print(np.mean(x_pool_with_labels))
  # print(y_pool_with_labels)
  # import sys
  # sys.exit()
  print('x_pool with labels accessible by oracle:',x_pool_with_labels.shape)
  oracle = KNOracle(x_pool_with_labels, y_pool_with_labels, n_neighbors=3, n_jobs=2)

  ### Naive approach - what's a better way to do this?
  ### Removing labels of some pool set points that Oracle has access to
  ### For MNIST, replacing labels >9 to have value of 10


  all_train_loss = np.zeros(shape=(acquisition_iterations+1, 1))
  all_valid_acc = np.zeros(shape=(acquisition_iterations+1, 1))

  all_test_acc = np.zeros(shape=(acquisition_iterations+1, 1))


  """
  TODO: DBAL PAPER : Use same network architecture
  """
  #Dropout CNN 
  model = Sequential()
  model.add(Conv2D(nb_filters, kernel_size=(nb_conv, nb_conv),
                   activation='relu',
                   input_shape=input_shape))
  model.add(Conv2D(nb_filters, (nb_conv, nb_conv), activation='relu'))
  model.add(MaxPooling2D(pool_size=(nb_pool, nb_pool)))
  model.add(Lambda(lambda x: K.dropout(x, level=0.25)))
  model.add(Flatten())
  model.add(Dense(256, activation='relu', kernel_regularizer=regularizers.l2(0.01),activity_regularizer=regularizers.l1(0.01)))
  model.add(Lambda(lambda x: K.dropout(x, level=0.5)))
  model.add(Dense(num_classes, activation='softmax'))
  model.compile(loss=keras.losses.categorical_crossentropy,
                optimizer=keras.optimizers.Adam(),
                metrics=['accuracy'])

  hist = model.fit(x_train, y_train,
            batch_size=batch_size,
            epochs=epochs,
            verbose=1,
            validation_data=(x_valid, y_valid))

  train_loss = np.asarray(hist.history.get('loss'))
  valid_acc = np.asarray(hist.history.get('val_acc'))

  all_train_loss[0,:] = train_loss[-1]
  all_valid_acc[0,:] = valid_acc[-1]


  score, accuracy = model.evaluate(x_test, y_test, verbose=0)
  print ("Accuracy with initial dataset")
  print('Test accuracy:', accuracy)

  all_test_acc[0,:] = accuracy

  print ("Performing Active Learning with Dropout BALD")

  for i in range(acquisition_iterations):

    print ("Acquisition Iteration", i)

    #take subset of pool points - to evaluate uncertainty over these points for querying
    pool_subset = 2000
    pool_subset_dropout = np.asarray(random.sample(range(0,x_pool.shape[0]), pool_subset))
    X_Pool_Dropout = x_pool[pool_subset_dropout, :, :, :]
    y_Pool_Dropout = y_pool[pool_subset_dropout]

    score_All = np.zeros(shape=(X_Pool_Dropout.shape[0], num_classes))
    All_Entropy_Dropout = np.zeros(shape=X_Pool_Dropout.shape[0])

    for d in range(dropout_iterations):
        print ('Dropout Iteration', d)

        dropout_score = model.predict(X_Pool_Dropout,batch_size=batch_size, verbose=1)
        #computing Entropy_Average_Pi
        score_All = score_All + dropout_score
        #computing Average_Entropy
        dropout_score_log = np.log2(dropout_score)
        Entropy_Compute = - np.multiply(dropout_score, dropout_score_log)
        Entropy_Per_Dropout = np.sum(Entropy_Compute, axis=1)
        All_Entropy_Dropout = All_Entropy_Dropout + Entropy_Per_Dropout 


    Avg_Pi = np.divide(score_All, dropout_iterations)
    Log_Avg_Pi = np.log2(Avg_Pi)
    Entropy_Avg_Pi = - np.multiply(Avg_Pi, Log_Avg_Pi)
    Entropy_Average_Pi = np.sum(Entropy_Avg_Pi, axis=1)

    G_X = Entropy_Average_Pi
    Average_Entropy = np.divide(All_Entropy_Dropout, dropout_iterations)
    U_X = Entropy_Average_Pi - Average_Entropy

    a_1d = U_X.flatten()
    x_pool_index = a_1d.argsort()[-Queries:][::-1]

    # this is where some elements are assigned to the Pool X
    Pooled_X = X_Pool_Dropout[x_pool_index, :, :, :]

    """
    Oracle gives TRUE LABEL to model here 
    """
    Pooled_Y = y_Pool_Dropout[x_pool_index] 
    #elements where Pooled_Y is 10 (elements for which Oracle does not have label)
    index_unknown_to_oracle = get_pool_index_unknown_to_oracle(Pooled_Y)

    """
    Assign labels to these points from Pool Point Clusters
    """
    ### assigning random labels for now (until clustering method is implemented!!!)
    ### Return Pooled_Y 

    if args.oracle == 'nearestlabel':
      Pooled_Y[index_unknown_to_oracle] = oracle.assign_nearest_available_label(Pooled_X[index_unknown_to_oracle])
    elif args.oracle == 'nearestpoint':
      # this call returns the 1st closest point to the learner
      X_closest, Y_closest = oracle.return_nearest_available_example_and_label(Pooled_X[index_unknown_to_oracle], neighbors=1)
      Pooled_X[index_unknown_to_oracle] = X_closest
      Pooled_Y[index_unknown_to_oracle] = Y_closest

    ## convert y_pool to categorical here
    Pooled_Y = keras.utils.to_categorical(Pooled_Y, num_classes)  


    delete_Pool_X = np.delete(x_pool, (pool_subset_dropout), axis=0)
    delete_Pool_Y = np.delete(y_pool, (pool_subset_dropout), axis=0)
    delete_Pool_X_Dropout = np.delete(X_Pool_Dropout, (x_pool_index), axis=0)
    delete_Pool_Y_Dropout = np.delete(y_Pool_Dropout, (x_pool_index), axis=0)


    x_pool = np.concatenate((x_pool, X_Pool_Dropout), axis=0)
    y_pool = np.concatenate((y_pool, y_Pool_Dropout), axis=0)

    x_train = np.concatenate((x_train, Pooled_X), axis=0)
    y_train = np.concatenate((y_train, Pooled_Y), axis=0)

    #Dropout CNN 
    model = Sequential()
    model.add(Conv2D(nb_filters, kernel_size=(nb_conv, nb_conv),
                     activation='relu',
                     input_shape=input_shape))
    model.add(Conv2D(nb_filters, (nb_conv, nb_conv), activation='relu'))
    model.add(MaxPooling2D(pool_size=(nb_pool, nb_pool)))
    model.add(Lambda(lambda x: K.dropout(x, level=0.25)))
    model.add(Flatten())
    model.add(Dense(256, activation='relu', kernel_regularizer=regularizers.l2(0.01),activity_regularizer=regularizers.l1(0.01)))
    model.add(Lambda(lambda x: K.dropout(x, level=0.5)))
    model.add(Dense(num_classes, activation='softmax'))
    model.compile(loss=keras.losses.categorical_crossentropy,
                  optimizer=keras.optimizers.Adam(),
                  metrics=['accuracy'])

    print(x_test.shape, y_test.shape)
    hist = model.fit(x_train, y_train,
              batch_size=batch_size,
              epochs=epochs,
              verbose=1,
              validation_data=(x_valid, y_valid))

    train_loss = np.asarray(hist.history.get('loss'))
    valid_acc = np.asarray(hist.history.get('val_acc'))

    all_train_loss[i,:] = train_loss[-1]
    all_valid_acc[i,:] = valid_acc[-1]


    score, accuracy = model.evaluate(x_test, y_test, verbose=0)

    all_test_acc[i,:] = accuracy


  np.save(args.save_dir + args.oracle + "_experiment_" + str(e) +  "_train_loss.npy", all_train_loss)
  np.save(args.save_dir + args.oracle + "_experiment_" + str(e) +  "_valid_acc.npy", all_valid_acc)
  np.save(args.save_dir + args.oracle + "_experiment_" + str(e) +  "_test_acc.npy", all_test_acc)

  Exp_Training_Loss[:, e] = all_train_loss[:,0]
  Exp_Valid_Acc[:, e] = all_valid_acc[:,0]
  Exp_Test_Acc[:, e] = all_test_acc[:, 0]



np.save(args.save_dir + args.oracle + "_all_train_loss.npy", Exp_Training_Loss)
np.save(args.save_dir + args.oracle + "_all_valid_acc.npy", Exp_Valid_Acc)
np.save(args.save_dir + args.oracle + "_all_test_acc.npy", Exp_Test_Acc)

