import keras

from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.layers import Conv2D, MaxPooling2D
from keras import backend as K
from keras.losses import categorical_crossentropy
from keras.optimizers import Adam
from keras.layers.core import Lambda
from keras import regularizers

def cnn(input_shape,
        output_classes,
        conv_kernel_size= (3, 3),
        n_filters= 32,
        pool_size=(4, 4),
        kernel_regularizer=regularizers.l2(0.01),
        activity_regularizer=regularizers.l1(0.01),
        optimizer=Adam(lr=0.01, decay=1e-6)):

    """
    Returns a CNN that can be used for mnist
    :param input_shape: the size of the input
    :param conv_kernel_size: size of the kernel for the convolution layers
    :param n_filters: the number of filters per convolution layer
    :param pool_size: size of the pooling operation
    :param kernel_regularizer: the regularizer to use for the weights of the dense layer
    :param activity_regularizer: the regularizer to use for the activations of a network
    :param optimizer: the optimizer to use (must be a keras.optimizers.Optimizer instance)
    :param loss: the loss function to use 

    :returns: keras.models.Model instance that has been compiled.
    """
    model = Sequential()
    model.add(Conv2D(n_filters,
                     kernel_size=conv_kernel_size,
                     activation='relu',
                     input_shape=input_shape))
    model.add(Conv2D(n_filters, conv_kernel_size, activation='relu'))
    model.add(MaxPooling2D(pool_size=pool_size))
    model.add(Lambda(lambda x: K.dropout(x, level=0.25)))
    model.add(Flatten())
    model.add(Dense(256,
                    activation='relu',
                    kernel_regularizer=kernel_regularizer,
                    activity_regularizer=activity_regularizer))
    model.add(Lambda(lambda x: K.dropout(x, level=0.5)))
    model.add(Dense(output_classes, activation='softmax'))
    model.compile(loss=categorical_crossentropy,
    optimizer=optimizer,
    metrics=['accuracy'])

    return model