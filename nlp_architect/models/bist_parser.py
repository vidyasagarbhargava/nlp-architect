# ******************************************************************************
# Copyright 2017-2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ******************************************************************************
"""BIST parser main module."""
from __future__ import unicode_literals, print_function, division, absolute_import

import json
import os

from nlp_architect.models.bist import utils
from nlp_architect.models.bist.mstlstm import MSTParserLSTM
from nlp_architect.models.bist.utils import get_options_dict


class BISTModel(object):
    """
    BIST parser model class.
    After the model is initialized, it accepts a CoNLL formatted dataset as input, and learns to
    output dependencies for new input.

    This class handles training, prediction, loading and saving of a BIST parser model.
    Args:
        activation (str, optional): Activation function to use.
        lstm_layers (int, optional): Number of LSTM layers to use.
        lstm_dims (int, optional): Number of LSTM dimensions to use.
        pos_dims (int, optional): Number of part-of-speech embedding dimensions to use.

    Attributes:
        model (MSTParserLSTM): The underlying LSTM model.
        params (tuple): Additional parameters and resources for the model.
        options (dict): User model options.
    """
    def __init__(self, activation='tanh',
                 lstm_layers=2,
                 lstm_dims=125,
                 pos_dims=25):
        if isinstance(activation, str) and isinstance(lstm_layers, int) \
                and isinstance(lstm_dims, int) and isinstance(pos_dims, int):
            self.options = get_options_dict(activation, lstm_dims, lstm_layers, pos_dims)
            self.params = None
            self.model = None

    def fit(self, dataset, epochs=10, dev=None):
        """
        Trains a BIST model on an annotated dataset in CoNLL file format.
        Args:
            dataset (str): Path to input dataset for training, formatted in CoNLL/U format.
            epochs (int, optional): Number of learning iterations.
            dev (str, optional): Path to development dataset for conducting evaluations.
        """
        if isinstance(dataset, str) and os.path.isfile(dataset) and isinstance(epochs, int)\
                and (not dev or isinstance(dev, str)):
            print('\nRunning fit on ' + dataset + '...\n')
            words, w2i, pos, rels = utils.vocab(dataset)
            self.params = words, w2i, pos, rels, self.options
            self.model = MSTParserLSTM(*self.params)

            for epoch in range(epochs):
                print('Starting epoch', epoch + 1)
                self.model.train(dataset)
                if dev:
                    ext = dev.rindex('.')
                    res_path = dev[:ext] + '_epoch_' + str(epoch + 1) + '_pred' + dev[ext:]
                    utils.write_conll(res_path, self.model.predict(dev))
                    utils.run_eval(dev, res_path)

    def predict(self, dataset, evaluate=False):
        """
        Runs inference with the BIST model on a dataset in CoNLL file format.
        Args:
            dataset (str): Path to input CoNLL file.
            evaluate (bool, optional): Write prediction and evaluation files to dataset's folder.
        Returns:
            res (list of list of ConllEntry): The list of input sentences with predicted
            dependencies attached.
        """
        res = None
        if isinstance(dataset, str) and os.path.isfile(dataset):
            print('\nRunning predict on ' + dataset + '...\n')
            res = list(self.model.predict(conll_path=dataset))
            if evaluate:
                ext = dataset.rindex('.')
                pred_path = dataset[:ext] + '_pred' + dataset[ext:]
                utils.write_conll(pred_path, res)
                utils.run_eval(dataset, pred_path)
        return res

    def predict_conll(self, dataset):
        """
        Runs inference with the BIST model on a dataset in CoNLL object format.
        Args:
            dataset (list of list of ConllEntry): Input in the form of ConllEntry objects.
        Returns:
            res (list of list of ConllEntry): The list of input sentences with predicted
            dependencies attached.
        """
        if hasattr(dataset, '__iter__'):
            return list(self.model.predict(conll=dataset))

    def load(self, path):
        """
        Loads and initializes a BIST model from file.
        """
        if isinstance(path, str) and os.path.isfile(path):
            with open(os.path.join(os.path.dirname(path), 'params.json'), 'r') as file:
                self.params = json.load(file)
            self.model = MSTParserLSTM(*self.params)
            self.model.load(path)

    def save(self, path):
        """
        Saves the BIST model to file.
        """
        if isinstance(path, str) and os.path.isdir(os.path.dirname(path)):
            with open(os.path.join(os.path.dirname(path), 'params.json'), 'w') as file:
                json.dump(self.params, file)
            self.model.save(path)