import numpy as np
from proj1_helpers import *

##############################################
#       Loss + Gradient Calculators          #
##############################################

# compute the MSE Loss
def compute_loss(y, tx, w):
    N = y.shape[0] # N = Number of samples
    e = y - tx @ w # e = error vector (truth - prediction)
    loss = 1/(2*N) * np.dot(e,e) # calculate the average loss
    return loss

# compute the gradient for the MSE loss function
def compute_gradient(y, tx, w):
    N = y.shape[0] # N = Number of samples
    e = y - tx @ w # e = error vector (truth - prediction)
    gradient = -(1/N) * (tx.T) @ (e) # calculate the gradient
    return gradient


##############################################################
#            Ridge Regression                                #
##############################################################

# Use the ridge regression formula
def ridge_regression(y, tx, lambda_):
    N = tx.shape #get the dimensions of x
    lambda_prime = 2 * N[0] * lambda_ #calculate the new lambda of the gradient formula

    # calculate the coefficient matrix and the forcing term respectively
    coefficient_matrix = np.transpose(tx) @ tx + lambda_prime * np.eye(N[1])
    forcing_term = np.transpose(tx) @ y

    w = np.linalg.solve(coefficient_matrix, forcing_term) #calculate the w with the ridge normal equation
    return w

#do we need this?
def debug_ridge(y, tx):
    """debugging the ridge regression by setting lambda=0."""
    w_least_squares = least_squares(y, tx)
    w_0 = ridge_regression(y, tx, 0)
    err = np.linalg.norm(w_least_squares-w_0)
    return err

#################################################
#       Cross Validation &                      #
#      Hyperparameter Finetuning                #
#################################################

# cross validation function for ridge regression
# k-indices = random subsets of the original samples
# k the set that we will use as the test set out of the subsets
# lambda_ = the lambda for the regularization function
# degree = the degree up to which we will exponentiate each feature

def cross_validation_ridge(y, x, k_indices, k, lambda_, degree,crossing = False):
    N = y.shape[0] # number of samples
    k_fold = k_indices.shape[0] # number of seperated sets
    list_ = []
    interval = int(N/k_fold) # the length of each subset
    # this is not well written and should be changed it is very hard to understand
    # Create a list of the indices of subsets that are supposed to be used as a training set
    for i in range(k_fold):
        if i != k:
            list_.append(i)
    # create the training set out of these indices
    x_training = np.zeros((int((k_fold-1)/k_fold*N), x.shape[1]))
    y_training = np.zeros(int((k_fold-1)/k_fold*N))
    column_to_add_train_0 = x_training[:, 0]
    for j in range(len(list_)):
        x_training[interval*(j):interval*(j+1), :] = x[np.array([k_indices[list_[j]]]), :]
    for j in range(len(list_)):
        y_training[interval*(j):interval*(j+1)] = y[np.array([k_indices[list_[j]]])]
    # get the testing set out of the remaining set
    x_testing = x[k_indices[k], :]
    y_testing = y[k_indices[k]]
    column_to_add_test_0 = x_testing[:, 0]
    # augment the testing and training set feature vectors
    if crossing is True:
        x_training_augmented = build_poly_cov(x_training[:,1:], degree)
        x_testing_augmented = build_poly_cov(x_testing[:,1:], degree)
        x_training_augmented = np.insert(x_training_augmented, 0, column_to_add_train_0, axis=1)
        x_testing_augmented = np.insert(x_testing_augmented, 0, column_to_add_test_0, axis=1)
    else:
        x_training_augmented = build_poly(x_training, degree)
        x_testing_augmented = build_poly(x_testing, degree)
    # get optimal weights
    w_opt_training = ridge_regression(y_training, x_training_augmented, lambda_)
    # calculate accuracy for the test set and return it
    predictions_test = x_testing_augmented@w_opt_training
    predictions_test = np.array([0 if el <0.5 else 1 for el in predictions_test])
    acc_test = compute_accuracy(y_testing, predictions_test)
    return acc_test

def cross_validation_logistic(y, x, k_indices, k, lambda_, degree, gamma, crossing = False):
    """return the loss of ridge regression."""
    N = y.shape[0]
    k_fold = k_indices.shape[0]
    list_ = []
    interval = int(N/k_fold)
    for i in range(k_fold):
        if i != k:
            list_.append(i)
    x_training = np.zeros((int((k_fold-1)/k_fold*N), x.shape[1]))
    y_training = np.zeros(int((k_fold-1)/k_fold*N))
    column_to_add_train_0 = x_training[:, 0]
    for j in range(len(list_)):
        x_training[interval*(j):interval*(j+1), :] = x[np.array([k_indices[list_[j]]]), :]
    x_testing = x[k_indices[k], :]
    column_to_add_test_0 = x_testing[:, 0]
    for j in range(len(list_)):
        y_training[interval*(j):interval*(j+1)] = y[np.array([k_indices[list_[j]]])]
    y_testing = y[k_indices[k]]
    if crossing is True:
        x_training_augmented = build_poly_cov(x_training[:,1:], degree)
        x_testing_augmented = build_poly_cov(x_testing[:,1:], degree)
        x_training_augmented = np.insert(x_training_augmented, 0, column_to_add_train_0, axis=1)
        x_testing_augmented = np.insert(x_testing_augmented, 0, column_to_add_test_0, axis=1)
    else:
        x_training_augmented = build_poly(x_training, degree)
        x_testing_augmented = build_poly(x_testing, degree)
    _, w_opt_training = learning_by_penalized_gradient(y_training, x_training_augmented,
                                                       np.zeros(x_training_augmented.shape[1]), gamma, 1000, lambda_)
    predictions_test = sigmoid(x_testing_augmented @ w_opt_training)
    predictions_test = np.array([0 if el < 0.5 else 1 for el in predictions_test])
    acc_test = compute_accuracy(y_testing, predictions_test)
    return acc_testf
# the following function aims at finetuning the hyperparameters of the ridge regression model
# tX = the array of features of the samples
# y = the label of each sample
# k_fold = the number of splits the dataset should be split into
# degrees = the range of the degrees to be tested for data augmentation
# lambdas = the different lambdas that can be used as a regularization param

def finetune_ridge(tX, y, k_fold = 5, degrees = np.arange(2, 7), lambdas = np.logspace(-5,0,15),crossing = False):
    seed = 1 # initialise the seed for the randomizer
    testing_acc = np.zeros((len(lambdas), len(degrees)))# initial 2-d array for the grid search or the lambads and the degrees
    k_indices = build_k_indices(y, k_fold, seed) #create the subarrays for the cross_validation
    for index1 in range(len(lambdas)):
        for index2 in range(len(degrees)):
            current_sum_test = 0
            #run the cross validation for each possible split into test-train
            for k in range(k_fold):
                current_test_acc = cross_validation_ridge(y, tX, k_indices, k,
                                                    lambdas[index1], degrees[index2],crossing)
                current_sum_test += current_test_acc # we increase the sum of the accuracy that we will later average
            testing_acc[index1, index2] = current_sum_test / k_fold # save the average of the test_accuracy
    best_result = np.where(testing_acc == np.amax(testing_acc)) # get the optimal index for the hyper parameters
    # get and print the optimal values
    print(best_result)
    lambda_opt, degree_opt = lambdas[best_result[0]],degrees[best_result[1]]
    print(testing_acc)
    print(lambda_opt, degree_opt)
    return lambda_opt[0], degree_opt[0]

# calculate weights given the degree of data augmentation and the lambda_
def optimal_weights_ridge(tX, y, degree, lambda_):
    tX_augmented = build_poly(tX, degree)
    w_ridge = ridge_regression(y, tX_augmented, lambda_)
    return w_ridge

def predict_ridge(tX,w,degree):
    #since we trained the model in augmented data, we augment the test set
    tX_augmented = build_poly(tX, degree)
    # make the predictions with the augmented test set and ridge resgression
    predictions_ridge = tX_augmented @ w
    return predictions_ridge
