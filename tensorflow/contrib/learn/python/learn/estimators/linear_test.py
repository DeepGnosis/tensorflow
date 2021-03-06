# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
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
# ==============================================================================

"""Tests for estimators.linear."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
import tensorflow as tf


class LinearClassifierTest(tf.test.TestCase):

  def testTrain(self):
    """Tests that loss goes down with training."""

    def input_fn():
      return {
          'age': tf.constant([1]),
          'language': tf.SparseTensor(values=['english'],
                                      indices=[[0, 0]],
                                      shape=[1, 1])
      }, tf.constant([[1]])

    language = tf.contrib.layers.sparse_column_with_hash_bucket('language', 100)
    age = tf.contrib.layers.real_valued_column('age')

    classifier = tf.contrib.learn.LinearClassifier(
        feature_columns=[age, language])
    classifier.fit(input_fn=input_fn, steps=100)
    loss1 = classifier.evaluate(input_fn=input_fn, steps=1)['loss']
    classifier.fit(input_fn=input_fn, steps=200)
    loss2 = classifier.evaluate(input_fn=input_fn, steps=1)['loss']
    self.assertLess(loss2, loss1)
    self.assertLess(loss2, 0.01)

  def testTrainOptimizerWithL1Reg(self):
    """Tests l1 regularized model has higher loss."""

    def input_fn():
      return {
          'language': tf.SparseTensor(values=['hindi'],
                                      indices=[[0, 0]],
                                      shape=[1, 1])
      }, tf.constant([[1]])

    language = tf.contrib.layers.sparse_column_with_hash_bucket('language', 100)
    classifier_no_reg = tf.contrib.learn.LinearClassifier(
        feature_columns=[language])
    classifier_with_reg = tf.contrib.learn.LinearClassifier(
        feature_columns=[language],
        optimizer=tf.train.FtrlOptimizer(learning_rate=1.0,
                                         l1_regularization_strength=100.))
    loss_no_reg = classifier_no_reg.fit(
        input_fn=input_fn, steps=100).evaluate(
            input_fn=input_fn, steps=1)['loss']
    loss_with_reg = classifier_with_reg.fit(
        input_fn=input_fn, steps=100).evaluate(
            input_fn=input_fn, steps=1)['loss']
    self.assertLess(loss_no_reg, loss_with_reg)

  def testTrainWithMissingFeature(self):
    """Tests that training works with missing features."""

    def input_fn():
      return {
          'language': tf.SparseTensor(values=['Swahili', 'turkish'],
                                      indices=[[0, 0], [2, 0]],
                                      shape=[3, 1])
      }, tf.constant([[1], [1], [1]], dtype=tf.int32)

    language = tf.contrib.layers.sparse_column_with_hash_bucket('language', 100)
    classifier = tf.contrib.learn.LinearClassifier(feature_columns=[language])
    classifier.fit(input_fn=input_fn, steps=100)
    loss = classifier.evaluate(input_fn=input_fn, steps=1)['loss']
    self.assertLess(loss, 0.01)

  def testSdcaOptimizerRealValuedFeatureWithInvalidDimension(self):
    """Tests a ValueError is raised if a real valued feature has dimension>1."""

    def input_fn():
      return {
          'example_id': tf.constant(['1', '2']),
          'sq_footage': tf.constant([[800.0, 200.0], [650.0, 500.0]])
      }, tf.constant([[1.0], [0.0]])

    sq_footage = tf.contrib.layers.real_valued_column('sq_footage', dimension=2)
    sdca_optimizer = tf.contrib.learn.SDCAOptimizer(
        example_id_column='example_id')
    classifier = tf.contrib.learn.LinearClassifier(feature_columns=[sq_footage],
                                                   optimizer=sdca_optimizer)
    with self.assertRaises(ValueError):
      _ = classifier.fit(input_fn=input_fn, steps=100)

  def testSdcaOptimizerRealValuedFeatures(self):
    """Tests LinearClasssifier with SDCAOptimizer and real valued features."""

    def input_fn():
      return {
          'example_id': tf.constant(['1', '2']),
          'maintenance_cost': tf.constant([[500.0], [200.0]]),
          'sq_footage': tf.constant([[800.0], [600.0]]),
          'weights': tf.constant([[1.0], [1.0]])
      }, tf.constant([[0], [1]])

    maintenance_cost = tf.contrib.layers.real_valued_column('maintenance_cost')
    sq_footage = tf.contrib.layers.real_valued_column('sq_footage')
    sdca_optimizer = tf.contrib.learn.SDCAOptimizer(
        example_id_column='example_id')
    classifier = tf.contrib.learn.LinearClassifier(
        feature_columns=[maintenance_cost, sq_footage],
        weight_column_name='weights',
        optimizer=sdca_optimizer)
    classifier.fit(input_fn=input_fn, steps=100)
    loss = classifier.evaluate(input_fn=input_fn, steps=1)['loss']
    self.assertLess(loss, 0.05)

  def testSdcaOptimizerBucketizedFeatures(self):
    """Tests LinearClasssifier with SDCAOptimizer and bucketized features."""

    def input_fn():
      return {
          'example_id': tf.constant(['1', '2', '3']),
          'price': tf.constant([[600.0], [1000.0], [400.0]]),
          'sq_footage': tf.constant([[1000.0], [600.0], [700.0]]),
          'weights': tf.constant([[1.0], [1.0], [1.0]])
      }, tf.constant([[1], [0], [1]])

    price_bucket = tf.contrib.layers.bucketized_column(
        tf.contrib.layers.real_valued_column('price'),
        boundaries=[500.0, 700.0])
    sq_footage_bucket = tf.contrib.layers.bucketized_column(
        tf.contrib.layers.real_valued_column('sq_footage'),
        boundaries=[650.0])
    sdca_optimizer = tf.contrib.learn.SDCAOptimizer(
        example_id_column='example_id',
        symmetric_l2_regularization=1.0)
    classifier = tf.contrib.learn.LinearClassifier(
        feature_columns=[price_bucket, sq_footage_bucket],
        weight_column_name='weights',
        optimizer=sdca_optimizer)
    classifier.fit(input_fn=input_fn, steps=50)
    scores = classifier.evaluate(input_fn=input_fn, steps=2)
    self.assertGreater(scores['accuracy'], 0.9)

  def testSdcaOptimizerSparseFeatures(self):
    """Tests LinearClasssifier with SDCAOptimizer and sparse features."""

    def input_fn():
      return {
          'example_id': tf.constant(['1', '2', '3']),
          'price': tf.constant([[0.4], [0.6], [0.3]]),
          'country': tf.SparseTensor(values=['IT', 'US', 'GB'],
                                     indices=[[0, 0], [1, 3], [2, 1]],
                                     shape=[3, 5]),
          'weights': tf.constant([[1.0], [1.0], [1.0]])
      }, tf.constant([[1], [0], [1]])

    price = tf.contrib.layers.real_valued_column('price')
    country = tf.contrib.layers.sparse_column_with_hash_bucket(
        'country', hash_bucket_size=5)
    sdca_optimizer = tf.contrib.learn.SDCAOptimizer(
        example_id_column='example_id')
    classifier = tf.contrib.learn.LinearClassifier(
        feature_columns=[price, country],
        weight_column_name='weights',
        optimizer=sdca_optimizer)
    classifier.fit(input_fn=input_fn, steps=50)
    scores = classifier.evaluate(input_fn=input_fn, steps=2)
    self.assertGreater(scores['accuracy'], 0.9)

  def testSdcaOptimizerCrossedFeatures(self):
    """Tests LinearClasssifier with SDCAOptimizer and crossed features."""

    def input_fn():
      return {
          'example_id': tf.constant(['1', '2', '3']),
          'language': tf.SparseTensor(values=['english', 'italian', 'spanish'],
                                      indices=[[0, 0], [1, 0], [2, 0]],
                                      shape=[3, 1]),
          'country': tf.SparseTensor(values=['US', 'IT', 'MX'],
                                     indices=[[0, 0], [1, 0], [2, 0]],
                                     shape=[3, 1])
      }, tf.constant([[0], [0], [1]])

    language = tf.contrib.layers.sparse_column_with_hash_bucket(
        'language', hash_bucket_size=5)
    country = tf.contrib.layers.sparse_column_with_hash_bucket(
        'country', hash_bucket_size=5)
    country_language = tf.contrib.layers.crossed_column(
        [language, country], hash_bucket_size=10)
    sdca_optimizer = tf.contrib.learn.SDCAOptimizer(
        example_id_column='example_id')
    classifier = tf.contrib.learn.LinearClassifier(
        feature_columns=[country_language],
        optimizer=sdca_optimizer)
    classifier.fit(input_fn=input_fn, steps=10)
    scores = classifier.evaluate(input_fn=input_fn, steps=2)
    self.assertGreater(scores['accuracy'], 0.9)

  def testSdcaOptimizerMixedFeatures(self):
    """Tests LinearClasssifier with SDCAOptimizer and a mix of features."""

    def input_fn():
      return {
          'example_id': tf.constant(['1', '2', '3']),
          'price': tf.constant([[0.6], [0.8], [0.3]]),
          'sq_footage': tf.constant([[900.0], [700.0], [600.0]]),
          'country': tf.SparseTensor(values=['IT', 'US', 'GB'],
                                     indices=[[0, 0], [1, 3], [2, 1]],
                                     shape=[3, 5]),
          'weights': tf.constant([[3.0], [1.0], [1.0]])
      }, tf.constant([[1], [0], [1]])

    price = tf.contrib.layers.real_valued_column('price')
    sq_footage_bucket = tf.contrib.layers.bucketized_column(
        tf.contrib.layers.real_valued_column('sq_footage'),
        boundaries=[650.0, 800.0])
    country = tf.contrib.layers.sparse_column_with_hash_bucket(
        'country', hash_bucket_size=5)
    sq_footage_country = tf.contrib.layers.crossed_column(
        [sq_footage_bucket, country],
        hash_bucket_size=10)
    sdca_optimizer = tf.contrib.learn.SDCAOptimizer(
        example_id_column='example_id')
    classifier = tf.contrib.learn.LinearClassifier(
        feature_columns=[price, sq_footage_bucket, country, sq_footage_country],
        weight_column_name='weights',
        optimizer=sdca_optimizer)
    classifier.fit(input_fn=input_fn, steps=50)
    scores = classifier.evaluate(input_fn=input_fn, steps=2)
    self.assertGreater(scores['accuracy'], 0.9)

  def testEval(self):
    """Tests that eval produces correct metrics.
    """

    def input_fn():
      return {
          'age': tf.constant([[1], [2]]),
          'language': tf.SparseTensor(values=['greek', 'chinise'],
                                      indices=[[0, 0], [1, 0]],
                                      shape=[2, 1]),
      }, tf.constant([[1], [0]])

    language = tf.contrib.layers.sparse_column_with_hash_bucket('language', 100)
    age = tf.contrib.layers.real_valued_column('age')
    classifier = tf.contrib.learn.LinearClassifier(
        feature_columns=[age, language])

    # Evaluate on trained mdoel
    classifier.fit(input_fn=input_fn, steps=100)
    classifier.evaluate(input_fn=input_fn, steps=2)

    # TODO(ispir): Enable accuracy check after resolving the randomness issue.
    # self.assertLess(evaluated_values['loss/mean'], 0.3)
    # self.assertGreater(evaluated_values['accuracy/mean'], .95)


class LinearRegressorTest(tf.test.TestCase):

  def testRegression(self):
    """Tests that loss goes down with training."""

    def input_fn():
      return {
          'age': tf.constant([1]),
          'language': tf.SparseTensor(values=['english'],
                                      indices=[[0, 0]],
                                      shape=[1, 1])
      }, tf.constant([[10.]])

    language = tf.contrib.layers.sparse_column_with_hash_bucket('language', 100)
    age = tf.contrib.layers.real_valued_column('age')

    classifier = tf.contrib.learn.LinearRegressor(
        feature_columns=[age, language])
    classifier.fit(input_fn=input_fn, steps=100)
    loss1 = classifier.evaluate(input_fn=input_fn, steps=1)['loss']
    classifier.fit(input_fn=input_fn, steps=200)
    loss2 = classifier.evaluate(input_fn=input_fn, steps=1)['loss']

    self.assertLess(loss2, loss1)
    self.assertLess(loss2, 0.01)

  def testRecoverWeights(self):
    rng = np.random.RandomState(67)
    n = 1000
    n_weights = 10
    bias = 2
    x = rng.uniform(-1, 1, (n, n_weights))
    weights = 10 * rng.randn(n_weights)
    y = np.dot(x, weights)
    y += rng.randn(len(x)) * 0.05 + rng.normal(bias, 0.01)
    regressor = tf.contrib.learn.LinearRegressor()
    regressor.fit(x, y, batch_size=32, steps=1000)
    # Have to flatten weights since they come in (x, 1) shape.
    self.assertAllClose(weights, regressor.weights_.flatten(), rtol=0.01)
    # TODO(ispir): Disable centered_bias.
    # assert abs(bias - regressor.bias_) < 0.1


def boston_input_fn():
  boston = tf.contrib.learn.datasets.load_boston()
  features = tf.cast(tf.reshape(tf.constant(boston.data), [-1, 13]), tf.float32)
  target = tf.cast(tf.reshape(tf.constant(boston.target), [-1, 1]), tf.float32)
  return features, target


class InferedColumnTest(tf.test.TestCase):

  def testTrain(self):
    est = tf.contrib.learn.LinearRegressor()
    est.fit(input_fn=boston_input_fn, steps=1)
    _ = est.evaluate(input_fn=boston_input_fn, steps=1)


if __name__ == '__main__':
  tf.test.main()
