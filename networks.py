# -*- coding: utf-8 -*-
#/usr/bin/python2
'''
By kyubyong park. kbpark.linguist@gmail.com. 
https://www.github.com/kyubyong/dc_tts

Modified...
'''

from __future__ import print_function

from modules import *
import tensorflow as tf

def TextEnc(hp, L, training=True, emos=None, speaker_codes=None, reuse=None):
    '''
    Args:
      L: Text inputs. (B, N)

    Return:
        K: Keys. (B, N, d)
        V: Values. (B, N, d)
    '''
    lcc = 0 # default
    if 'learn_channel_contributions' in hp.multispeaker:
        lcc = hp.nspeakers
    i = 1
    tensor = embed(L,
                   vocab_size=len(hp.vocab),
                   num_units=hp.e,
                   scope="embed_{}".format(i), reuse=reuse); i += 1
    if 'text_encoder_input' in hp.multispeaker:
        speaker_codes_time = tf.tile(speaker_codes, [1,tf.shape(L)[1]])
        speaker_reps = embed(speaker_codes_time,
                       vocab_size=hp.nspeakers,
                       num_units=hp.speaker_embedding_size,
                       scope="embed_{}".format(i), reuse=reuse); i += 1 
        tensor = tf.concat((tensor, speaker_reps), -1)
    
    if not emos is None: 
        tensor=broadcast_concat(tensor,emos)
    
    tensor = conv1d(tensor,
                    filters=2*hp.d,
                    size=1,
                    rate=1,
                    dropout_rate=hp.dropout_rate,
                    activation_fn=tf.nn.relu,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                    lcc=lcc, codes=speaker_codes); i += 1
    tensor = conv1d(tensor,
                    size=1,
                    rate=1,
                    dropout_rate=hp.dropout_rate,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                    lcc=lcc, codes=speaker_codes); i += 1

    for outer_counter in range(2):
        for j in range(4):
            tensor = hc(tensor,
                            size=3,
                            rate=3**j,
                            dropout_rate=hp.dropout_rate,
                            activation_fn=None,
                            training=training,
                            scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse,\
                            lcc=lcc, codes=speaker_codes); i += 1

    for _ in range(2):
        tensor = hc(tensor,
                        size=3,
                        rate=1,
                        dropout_rate=hp.dropout_rate,
                        activation_fn=None,
                        training=training,
                        scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse,\
                        lcc=lcc, codes=speaker_codes); i += 1


    if 'text_encoder_towards_end' in hp.multispeaker:
        speaker_codes_time = tf.tile(speaker_codes, [1,tf.shape(L)[1]])
        speaker_reps = embed(speaker_codes_time,
                       vocab_size=hp.nspeakers,
                       num_units=hp.speaker_embedding_size,
                       scope="embed_{}".format(i), reuse=reuse); i += 1 
        tensor = tf.concat((tensor, speaker_reps), -1)
        ### extra 1x1 conv to squash hidden + embedding -> desired size (2*hp.d)
        tensor = conv1d(tensor,
                        filters=2*hp.d,
                        size=1,
                        rate=1,
                        dropout_rate=hp.dropout_rate,
                        activation_fn=tf.nn.relu,
                        training=training,
                        scope="C_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1

    for _ in range(2):
        tensor = hc(tensor,                        
                        size=1,
                        rate=1,
                        dropout_rate=hp.dropout_rate,
                        activation_fn=None,
                        training=training,
                        scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse,\
                        lcc=lcc, codes=speaker_codes); i += 1

    K, V = tf.split(tensor, 2, -1)
    return K, V

def AudioEnc(hp, S, training=True, speaker_codes=None, reuse=None):
    '''
    Args:
      S: melspectrogram. (B, T/r, n_mels)

    Returns
      Q: Queries. (B, T/r, d)
    '''
    lcc = 0 # default
    if 'learn_channel_contributions' in hp.multispeaker:
        lcc = hp.nspeakers
    i = 1
    tensor = conv1d(S,
                    filters=hp.d,
                    size=1,
                    rate=1,
                    padding="CAUSAL",
                    dropout_rate=hp.dropout_rate,
                    activation_fn=tf.nn.relu,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                    lcc=lcc, codes=speaker_codes); i += 1

    if 'audio_encoder_input' in hp.multispeaker:
        speaker_codes_time = tf.tile(speaker_codes, [1,tf.shape(S)[1]])   
        speaker_reps = embed(speaker_codes_time,
                       vocab_size=hp.nspeakers,
                       num_units=hp.speaker_embedding_size,
                       scope="embed_{}".format(i), reuse=reuse); i += 1 
        tensor = tf.concat((tensor, speaker_reps), -1)
        tensor = conv1d(tensor, filters=hp.d, size=1, rate=1, dropout_rate=hp.dropout_rate, \
                    training=training, scope="C_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1

    tensor = conv1d(tensor,
                    size=1,
                    rate=1,
                    padding="CAUSAL",
                    dropout_rate=hp.dropout_rate,
                    activation_fn=tf.nn.relu,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                    lcc=lcc, codes=speaker_codes); i += 1
    tensor = conv1d(tensor,
                    size=1,
                    rate=1,
                    padding="CAUSAL",
                    dropout_rate=hp.dropout_rate,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                    lcc=lcc, codes=speaker_codes); i += 1
    for _ in range(2):
        for j in range(4):
            tensor = hc(tensor,
                            size=3,
                            rate=3**j,
                            padding="CAUSAL",
                            dropout_rate=hp.dropout_rate,
                            training=training,
                            scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse,\
                            lcc=lcc, codes=speaker_codes); i += 1
    for _ in range(2):
        tensor = hc(tensor,
                        size=3,
                        rate=3,
                        padding="CAUSAL",
                        dropout_rate=hp.dropout_rate,
                        training=training,
                        scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse,\
                        lcc=lcc, codes=speaker_codes); i += 1

    return tensor

def Audio2Emo(hp, S, training=True, speaker_codes=None, reuse=None):
    '''
    Args:
      S: melspectrogram. (B, T/r, n_mels)

    Returns
      Q: Queries. (B, T/r, d)
    '''
    lcc = 0
    i=1
    
    tensor = conv1d(S,
                    filters=hp.uee,
                    size=1,
                    rate=1,
                    padding="CAUSAL",
                    dropout_rate=hp.dropout_rate,
                    activation_fn=tf.nn.relu,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                    lcc=lcc, codes=speaker_codes); i += 1

    tensor = conv1d(tensor,
                    size=1,
                    rate=1,
                    padding="CAUSAL",
                    dropout_rate=hp.dropout_rate,
                    activation_fn=tf.nn.relu,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                    lcc=lcc, codes=speaker_codes); i += 1
    tensor = conv1d(tensor,
                    size=1,
                    rate=1,
                    padding="CAUSAL",
                    dropout_rate=hp.dropout_rate,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                    lcc=lcc, codes=speaker_codes); i += 1
    for _ in range(2):
        for j in range(4):
            tensor = hc(tensor,
                            size=3,
                            rate=3**j,
                            padding="CAUSAL",
                            dropout_rate=hp.dropout_rate,
                            training=training,
                            scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse,\
                            lcc=lcc, codes=speaker_codes); i += 1
    for _ in range(2):
        tensor = hc(tensor,
                        size=3,
                        rate=3,
                        padding="CAUSAL",
                        dropout_rate=hp.dropout_rate,
                        training=training,
                        scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse,\
                        lcc=lcc, codes=speaker_codes); i += 1

    return tensor


def broadcast_concat(Y, info):
    '''
        Args:
          Y: (B, T, n)
          info: (B, d)

        Returns:
          Y: (B, T, n+d)
        '''
    B = tf.shape(Y)[0]
    T = tf.shape(Y)[1]
    d = tf.shape(info)[-1]
    info = tf.ones([B, T, d]) * info  # (B, T, d)
    Y = tf.concat([Y, info], 2)  # (B, T, n+d)

    return Y


def Attention(hp, Q, K, V, monotonic_attention=False, prev_max_attentions=None):
    '''
    Args:
      Q: Queries. (B, T/r, d)
      K: Keys. (B, N, d)
      V: Values. (B, N, d)
      monotonic_attention: A boolean. At training, it is False.
      prev_max_attentions: (B,). At training, it is set to None.

    Returns:
      R: [Context Vectors; Q]. (B, T/r, 2d)
      alignments: (B, N, T/r)
      max_attentions: (B, T/r)
    '''
    A = tf.matmul(Q, K, transpose_b=True) * tf.rsqrt(tf.to_float(hp.d))
    if monotonic_attention:  # for inference
        key_masks = tf.sequence_mask(prev_max_attentions, hp.max_N)
        reverse_masks = tf.sequence_mask(hp.max_N - hp.attention_win_size - prev_max_attentions, hp.max_N)[:, ::-1]
        masks = tf.logical_or(key_masks, reverse_masks)
        masks = tf.tile(tf.expand_dims(masks, 1), [1, hp.max_T, 1])
        paddings = tf.ones_like(A) * (-2 ** 32 + 1)  # (B, T/r, N)
        A = tf.where(tf.equal(masks, False), A, paddings)  # where(condition,x,y) --Return the elements, either from x or y, depending on the condition.
    A = tf.nn.softmax(A) # (B, T/r, N)
    max_attentions = tf.argmax(A, -1)  # (B, T/r)
    R = tf.matmul(A, V)
    if hp.concatenate_query:
        print ('Concatenate R & Q -> R prime')
        R = tf.concat((R, Q), -1)
    else:
        print ('Do ***not*** concatenate R & Q -> R prime')

    alignments = tf.transpose(A, [0, 2, 1]) # (B, N, T/r)

    return R, alignments, max_attentions

# TODO: test to reparametrize the Attention matrix as a list of steps
def Attention_reparametrized(hp, Q, K, V, monotonic_attention=False, prev_max_attentions=None):
    '''
    Args:
      Q: Queries. (B, T/r, d)
      K: Keys. (B, N, d)
      V: Values. (B, N, d)
      monotonic_attention: A boolean. At training, it is False.
      prev_max_attentions: (B,). At training, it is set to None.

    Returns:
      R: [Context Vectors; Q]. (B, T/r, 2d)
      alignments: (B, N, T/r)
      max_attentions: (B, T/r)
    '''
    A = tf.matmul(Q, K, transpose_b=True) * tf.rsqrt(tf.to_float(hp.d)) # (B, T/r, N), I suppose ?
    
    v=tf.reduce_mean(A, axis=2) # (B, T/r) ?
    v=tf.math.sigmoid(v)*4-1
    v=tf.cast(v, dtype=tf.int32)
    v=tf.cumsum(v, axis=1)

    depth=tf.shape(V)[1] # depth is N
    A=tf.one_hot(v, depth) # (B, T/r, N) ?
    #A=tf.transpose(A, [0, 2, 1]) # (B, T/r, N) ?
    
    #A = tf.nn.softmax(A) # (B, T/r, N)
    max_attentions = tf.argmax(A, -1)  # (B, T/r)
    R = tf.matmul(A, V)
    if hp.concatenate_query:
        print ('Concatenate R & Q -> R prime')
        R = tf.concat((R, Q), -1)
    else:
        print ('Do ***not*** concatenate R & Q -> R prime')

    alignments = tf.transpose(A, [0, 2, 1]) # (B, N, T/r)

    return R, alignments, max_attentions

def FixedAttention(hp, duration_matrix, Q, V):
    '''
    Implement upsampling according to external duration model via an attention-like
    mechanism. Instead of computing A dynamically based on the comparison of Q and K,
    we use duration_matrix, an externally-supplied matrix. If binary and designed 
    appropriately, taking the product of this and V will perform selection and 
    upsampling of text-derived features in V. 

    Note that training and synthesis time operation is identical: i.e. the synthesis
    transcript is expected to have an externally-supplied duration field.

    Note that if K is computed elsewhere in the network, it is never used and will
    not be trained.

    Q is only passed in to optionally concatenate with upsampled text representations
    (if hp.concatenate_query==True) for compatibility with standard attention function 
    above.

    Return alignments -- used for attention loss even though this will never inform learning
    when using FixedAttention.

    max_attentions computed and returned, even though trivial in this case.
    '''
    max_attentions = tf.argmax(duration_matrix, -1)  # (B, T/r)
    R = tf.matmul(duration_matrix, V)
    if hp.concatenate_query:
        print ('Concatenate R & Q -> R prime')
        R = tf.concat((R, Q), -1)
    else:
        print ('Do ***not*** concatenate R & Q -> R prime')
    alignments = tf.transpose(duration_matrix, [0, 2, 1]) # (B, N, T/r)
    return R, alignments, max_attentions

def AudioDec(hp, R, training=True, emos=None, speaker_codes=None, reuse=None):
    '''
    Args:
      R: [Context Vectors; Q]. (B, T/r, 2d)

    Returns:
      Y: Melspectrogram predictions. (B, T/r, n_mels)
    '''
    lcc = 0 # default
    if 'learn_channel_contributions' in hp.multispeaker:
        lcc = hp.nspeakers
    i = 1

    if not emos is None: 
        R=broadcast_concat(R,emos)
    
    tensor = conv1d(R,
                    filters=hp.d,
                    size=1,
                    rate=1,
                    padding="CAUSAL",
                    dropout_rate=hp.dropout_rate,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1

    if 'audio_decoder_input' in hp.multispeaker:
        speaker_codes_time = tf.tile(speaker_codes, [1,tf.shape(R)[1]])   
        speaker_reps = embed(speaker_codes_time,    
                       vocab_size=hp.nspeakers,
                       num_units=hp.speaker_embedding_size,
                       scope="embed_{}".format(i), reuse=reuse); i += 1 
        tensor = tf.concat((tensor, speaker_reps), -1)
        tensor = conv1d(tensor, filters=hp.d, size=1, rate=1, dropout_rate=hp.dropout_rate, \
                    training=training, scope="C_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1

    for j in range(4):
        tensor = hc(tensor,
                        size=3,
                        rate=3**j,
                        padding="CAUSAL",
                        dropout_rate=hp.dropout_rate,
                        training=training,
                        scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse, \
                        lcc=lcc, codes=speaker_codes); i += 1

    for _ in range(2):
        tensor = hc(tensor,
                        size=3,
                        rate=1,
                        padding="CAUSAL",
                        dropout_rate=hp.dropout_rate,
                        training=training,
                        scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse,\
                        lcc=lcc, codes=speaker_codes); i += 1
    for _ in range(3):
        tensor = conv1d(tensor,
                        size=1,
                        rate=1,
                        padding="CAUSAL",
                        dropout_rate=hp.dropout_rate,
                        activation_fn=tf.nn.relu,
                        training=training,
                        scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                        lcc=lcc, codes=speaker_codes); i += 1
    # mel_hats
    logits = conv1d(tensor,
                    filters=hp.n_mels,
                    size=1,
                    rate=1,
                    padding="CAUSAL",
                    dropout_rate=hp.dropout_rate,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse,\
                    lcc=lcc, codes=speaker_codes); i += 1
    if hp.squash_output_t2m:
        Y = tf.nn.sigmoid(logits) # mel_hats
    else:
        Y = logits

    return logits, Y

def SSRN(hp, Y, training=True, speaker_codes=None, reuse=None):
    '''
    Args:
      Y: Melspectrogram Predictions. (B, T/r, n_mels)

    Returns:
      Z: Spectrogram Predictions. (B, T, 1+n_fft/2)
    '''

    i = 1 # number of layers

    # -> (B, T/r, c)
    tensor = conv1d(Y,
                    filters=hp.c,
                    size=1,
                    rate=1,
                    dropout_rate=hp.dropout_rate,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1

    if 'ssrn_input' in hp.multispeaker:
        speaker_codes_time = tf.tile(speaker_codes, [1,tf.shape(Y)[1]])   
        speaker_reps = embed(speaker_codes_time,            
                       vocab_size=hp.nspeakers,
                       num_units=hp.speaker_embedding_size,
                       scope="embed_{}".format(i), reuse=reuse); i += 1 
        tensor = tf.concat((tensor, speaker_reps), -1)    
        tensor = conv1d(tensor, filters=hp.c, size=1, rate=1, dropout_rate=hp.dropout_rate, \
                    training=training, scope="C_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1

    for j in range(2):
        tensor = hc(tensor,
                      size=3,
                      rate=3**j,
                      dropout_rate=hp.dropout_rate,
                      training=training,
                      scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1
    if hp.r==4:
        n_transposes=2
    elif hp.r==8:
        n_transposes=3
    else:
        sys.exit('reduction factor not handled by SSRN!')

    for _ in range(n_transposes):
        # -> (B, T/2, c) -> (B, T, c)
        tensor = conv1d_transpose(tensor,
                                  scope="D_{}".format(i),
                                  dropout_rate=hp.dropout_rate,
                                  training=training, reuse=reuse); i += 1
        for j in range(2):
            tensor = hc(tensor,
                            size=3,
                            rate=3**j,
                            dropout_rate=hp.dropout_rate,
                            training=training,
                            scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1
    # -> (B, T, 2*c)
    tensor = conv1d(tensor,
                    filters=2*hp.c,
                    size=1,
                    rate=1,
                    dropout_rate=hp.dropout_rate,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1
    for _ in range(2):
        tensor = hc(tensor,
                        size=3,
                        rate=1,
                        dropout_rate=hp.dropout_rate,
                        training=training,
                        scope="HC_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1
    # -> (B, T, 1+n_fft/2)

    tensor = conv1d(tensor,
                    filters=hp.full_dim, 
                    size=1,
                    rate=1,
                    dropout_rate=hp.dropout_rate,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1

    for _ in range(2):
        tensor = conv1d(tensor,
                        size=1,
                        rate=1,
                        dropout_rate=hp.dropout_rate,
                        activation_fn=tf.nn.relu,
                        training=training,
                        scope="C_{}".format(i), normtype=hp.norm, reuse=reuse); i += 1
    logits = conv1d(tensor,
               size=1,
               rate=1,
               dropout_rate=hp.dropout_rate,
               training=training,
               scope="C_{}".format(i), normtype=hp.norm, reuse=reuse)
    if hp.squash_output_ssrn:
        Z = tf.nn.sigmoid(logits)
    else:
        Z = logits
    return logits, Z

# this function is adapted from https://github.com/rishikksh20/vae_tacotron2
def VAE(inputs, num_units=32, scope='vae', reuse=None):
    with tf.variable_scope(scope):
        mu = tf.layers.dense(inputs, num_units, name='mean', reuse=reuse)
        log_var = tf.layers.dense(inputs, num_units, name='vari', reuse=reuse)
        std = tf.exp(log_var)
        z = tf.random_normal(shape=[tf.shape(mu)[0], num_units], mean=0.0, stddev=1.0)
        output = mu + z * std
        return output, mu, log_var

def vae_weight(hp, global_step):
    warm_up_step = hp.vae_warming_up

    warm_up_step=tf.reshape(warm_up_step, [])
    global_step=tf.reshape(global_step, [])

    w1 = tf.cond(
       global_step < warm_up_step,
       lambda: tf.cond(
            global_step % 100 < 1,
            lambda: tf.convert_to_tensor(hp.init_vae_weights) + tf.cast(global_step / 100  * hp.vae_weight_multiler, tf.float32),
            lambda: tf.cast(tf.convert_to_tensor(0), tf.float32)
         ),
       lambda: tf.cast(tf.convert_to_tensor(0), tf.float32)
    )
      
    w2 = tf.cond(
       global_step > warm_up_step,
       lambda: tf.cond(
             global_step % 400 < 1,
             lambda: tf.convert_to_tensor(hp.init_vae_weights) + tf.cast((global_step - warm_up_step) / 400 * hp.vae_weight_multiler + warm_up_step / 100 * hp.vae_weight_multiler, tf.float32),
             lambda: tf.cast(tf.convert_to_tensor(0), tf.float32)
         ),
       lambda: tf.cast(tf.convert_to_tensor(0), tf.float32)
    )             
    return tf.reshape(tf.maximum(w1, w2), [])

def LinearTransformLabels(hp, L, training=True, reuse=None):
    '''
    Args:
      L: Text inputs. (B, N, labdim)

    Return:
        K or V: Keys. (B, N, d)
    '''
    i = 1
    tensor = conv1d(L,
                    filters=hp.d,
                    size=1,
                    rate=1,
                    dropout_rate=hp.dropout_rate,
                    activation_fn=None,
                    training=training,
                    scope="C_{}".format(i), normtype=hp.norm, reuse=reuse)
    return tensor

