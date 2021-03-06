#!/usr/bin/env python3
import os.path
import tensorflow as tf
import helper
import warnings
from distutils.version import LooseVersion
import project_tests as tests
from datetime import datetime
import shutil

FLAGS = tf.app.flags.FLAGS

tf.app.flags.DEFINE_integer("EPOCHS", 40, "total run epochs")
tf.app.flags.DEFINE_integer("BATCH_SIZE", 16, "Batch size")
tf.app.flags.DEFINE_float("DROPOUT", 0.5, "keep prob")
tf.app.flags.DEFINE_float("LEARNING_RATE", 0.0001, "learning rate")

num_classes = 2
image_shape = (160, 576)  # KITTI dataset uses 160x576 images
data_dir = './data'
runs_dir = './runs'
SAVE_PATH = "save_models"


output_dir = os.path.join(runs_dir, "drop-"+str(FLAGS.DROPOUT))
if os.path.exists(output_dir):
    shutil.rmtree(output_dir)
os.makedirs(output_dir)

log_file = "{}/log_file_drop_{:.3f}.txt".format(output_dir, FLAGS.DROPOUT)

with open(log_file, "a") as f:
    f.write("Epoch:{}, BATCH_SIZE:{}, DROPOUT:{}, lr:{}\n".format(FLAGS.EPOCHS, FLAGS.BATCH_SIZE, FLAGS.DROPOUT, FLAGS.LEARNING_RATE))

# Check TensorFlow Version
assert LooseVersion(tf.__version__) >= LooseVersion('1.0'), 'Please use TensorFlow version 1.0 or newer.  You are using {}'.format(tf.__version__)
print('TensorFlow Version: {}'.format(tf.__version__))

# Check for a GPU
if not tf.test.gpu_device_name():
    warnings.warn('No GPU found. Please use a GPU to train your neural network.')
else:
    print('Default GPU Device: {}'.format(tf.test.gpu_device_name()))


def load_vgg(sess, vgg_path):
    """
    Load Pretrained VGG Model into TensorFlow.
    :param sess: TensorFlow Session
    :param vgg_path: Path to vgg folder, containing "variables/" and "saved_model.pb"
    :return: Tuple of Tensors from VGG model (image_input, keep_prob, layer3_out, layer4_out, layer7_out)
    """

    #   Use tf.saved_model.loader.load to load the model and weights
    vgg_tag = 'vgg16'
    vgg_input_tensor_name = 'image_input:0'
    vgg_keep_prob_tensor_name = 'keep_prob:0'
    vgg_layer3_out_tensor_name = 'layer3_out:0'
    vgg_layer4_out_tensor_name = 'layer4_out:0'
    vgg_layer7_out_tensor_name = 'layer7_out:0'

    model = tf.saved_model.loader.load(sess, [vgg_tag], vgg_path)

    graph = tf.get_default_graph()

    image_input = graph.get_tensor_by_name(vgg_input_tensor_name)
    keep_prob = graph.get_tensor_by_name(vgg_keep_prob_tensor_name)
    layer3_out = graph.get_tensor_by_name(vgg_layer3_out_tensor_name)
    layer4_out = graph.get_tensor_by_name(vgg_layer4_out_tensor_name)
    layer7_out = graph.get_tensor_by_name(vgg_layer7_out_tensor_name)

    return image_input, keep_prob, layer3_out, layer4_out, layer7_out

# tests.test_load_vgg(load_vgg, tf)


def layers(vgg_layer3_out, vgg_layer4_out, vgg_layer7_out, num_classes):
    """
    Create the layers for a fully convolutional network.  Build skip-layers using the vgg layers.
    :param vgg_layer3_out: TF Tensor for VGG Layer 3 output
    :param vgg_layer4_out: TF Tensor for VGG Layer 4 output
    :param vgg_layer7_out: TF Tensor for VGG Layer 7 output
    :param num_classes: Number of classes to classify
    :return: The Tensor for the last layer of output
    """
    # TODO: Implement function
    layer3, layer4, layer7 = vgg_layer3_out, vgg_layer4_out, vgg_layer7_out

    # 中间的layer， filter层数同分类数
    fcn8 = tf.layers.conv2d(layer7, filters=num_classes, kernel_size=1, name="fcn8")

    fcn9 = tf.layers.conv2d_transpose(fcn8, filters=layer4.shape.as_list()[-1],
                                      kernel_size=4, strides=(2, 2), padding="SAME", name="fcn9")

    fcn9_skip_connected = tf.add(fcn9, layer4, name="fcn9_plus_vgg_layer4")

    fcn10 = tf.layers.conv2d_transpose(fcn9_skip_connected, filters=layer3.shape.as_list()[-1],
                                       kernel_size=4, strides=(2, 2), padding="SAME", name="fcn10_conv2d")

    fcn10_skip_connected = tf.add(fcn10, layer3, name="fcn10_plus_vgg_layer3")

    fcn11 = tf.layers.conv2d_transpose(fcn10_skip_connected, filters=num_classes,
                                       kernel_size=16, strides=(8, 8), padding="SAME", name="fcn11")

    return fcn11

# tests.test_layers(layers)


def optimize(nn_last_layer, correct_label, learning_rate, num_classes):
    """
    Build the TensorFLow loss and optimizer operations.
    :param nn_last_layer: TF Tensor of the last layer in the neural network
    :param correct_label: TF Placeholder for the correct label image
    :param learning_rate: TF Placeholder for the learning rate
    :param num_classes: Number of classes to classify
    :return: Tuple of (logits, train_op, cross_entropy_loss)
    """
    # TODO: Implement function
    logits = tf.reshape(nn_last_layer, [-1, num_classes], name="fcn_logits")
    correct_label_reshaped = tf.reshape(correct_label, [-1, num_classes])

    cross_entropy = tf.nn.softmax_cross_entropy_with_logits(logits=logits, labels=correct_label_reshaped[:])

    loss_op = tf.reduce_mean(cross_entropy, name="fcn_loss")

    train_op = tf.train.AdamOptimizer(learning_rate).minimize(loss_op, name="fcn_train_op")

    return logits, train_op, loss_op

# tests.test_optimize(optimize)


def train_nn(sess, epochs, batch_size, get_batches_fn, train_op, cross_entropy_loss, input_image,
             correct_label, keep_prob, learning_rate):
    """
    Train neural network and print out the loss during training.
    :param sess: TF Session
    :param epochs: Number of epochs
    :param batch_size: Batch size
    :param get_batches_fn: Function to get batches of training data.  Call using get_batches_fn(batch_size)
    :param train_op: TF Operation to train the neural network
    :param cross_entropy_loss: TF Tensor for the amount of loss
    :param input_image: TF Placeholder for input images
    :param correct_label: TF Placeholder for label images
    :param keep_prob: TF Placeholder for dropout keep probability
    :param learning_rate: TF Placeholder for learning rate
    """
    # TODO: Implement function

    for epoch in range(epochs):

        total_loss = 0
        for X_batch, gt_batch in get_batches_fn(batch_size):

            loss, _ = sess.run([cross_entropy_loss, train_op], feed_dict={input_image: X_batch,
                                                                          correct_label:gt_batch,
                                                                          keep_prob:FLAGS.DROPOUT,
                                                                          learning_rate: FLAGS.LEARNING_RATE})
            total_loss += loss
        print("EPOCH {} ...".format(epoch + 1))
        print("Loss = {:.3f}".format(total_loss))
        print()

        with open(log_file, "a") as f:
            f.write("{}:Epoch:{}, Loss:{:.3}\n".format(datetime.now(), epoch+1, total_loss))

# tests.test_train_nn(train_nn)


def run():

    tests.test_for_kitti_dataset(data_dir)

    correct_label = tf.placeholder(tf.float32, [None, image_shape[0], image_shape[1], num_classes])
    learning_rate = tf.placeholder(tf.float32)

    # Download pretrained vgg model
    helper.maybe_download_pretrained_vgg(data_dir)

    # OPTIONAL: Train and Inference on the cityscapes dataset instead of the Kitti dataset.
    # You'll need a GPU with at least 10 teraFLOPS to train on.
    #  https://www.cityscapes-dataset.com/

    with tf.Session() as sess:
        # Path to vgg model
        vgg_path = os.path.join(data_dir, 'vgg')
        # Create function to get batches
        get_batches_fn = helper.gen_batch_function(os.path.join(data_dir, 'data_road/training'), image_shape)

        # OPTIONAL: Augment Images for better results
        #  https://datascience.stackexchange.com/questions/5224/how-to-prepare-augment-images-for-neural-network

        # TODO: Build NN using load_vgg, layers, and optimize function
        input_image, keep_prob, layer3, layer4, layer7 = load_vgg(sess, vgg_path)
        model_output = layers(layer3, layer4, layer7, num_classes)
        logits, train_op, cross_entropy_loss = optimize(model_output, correct_label, learning_rate, num_classes)

        saver = tf.train.Saver()
        sess.run(tf.global_variables_initializer())
        sess.run(tf.local_variables_initializer())

        print("Model bulid successful, starting training")

        # TODO: Train NN using the train_nn function
        train_nn(sess, FLAGS.EPOCHS, FLAGS.BATCH_SIZE, get_batches_fn,
                 train_op, cross_entropy_loss, input_image,
                 correct_label, keep_prob, learning_rate)


        # Save inference data using helper.save_inference_samples
        helper.save_inference_samples(output_dir, data_dir, sess, image_shape, logits, keep_prob, input_image)

        # save sess for later prediction
        # if not tf.gfile.IsDirectory(SAVE_PATH):
        #     tf.gfile.MakeDirs(SAVE_PATH)
        # saver.save(sess, SAVE_PATH+"/save-"+str(FLAGS.DROPOUT))
    
        # OPTIONAL: Apply the trained model to a video


if __name__ == '__main__':
    run()
